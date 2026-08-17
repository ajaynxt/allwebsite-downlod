from __future__ import annotations

import asyncio
import ipaddress
import logging
import mimetypes
from contextlib import asynccontextmanager, suppress
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import BASE_DIR, settings
from app.models import AnalyzeRequest, DownloadRequest, JobCreated, JobStatus, MediaInfo
from app.security import UnsafeUrlError, validate_public_url
from app.services.downloader import MediaDownloader, MediaExtractionError
from app.services.jobs import JobManager, QueueFullError
from app.services.rate_limit import RateLimitExceeded, SlidingWindowRateLimiter


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

downloader = MediaDownloader(settings)
jobs = JobManager(settings, downloader)
rate_limiter = SlidingWindowRateLimiter(window_seconds=900)
analyze_slots = asyncio.Semaphore(settings.max_workers * 2)


async def cleanup_loop() -> None:
    while True:
        await asyncio.sleep(300)
        await asyncio.to_thread(jobs.cleanup)
        rate_limiter.prune()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    task = asyncio.create_task(cleanup_loop())
    yield
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task
    jobs.shutdown()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    docs_url=None if settings.is_production else "/api/docs",
    redoc_url=None,
    openapi_url=None if settings.is_production else "/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(settings.allowed_hosts))
if settings.allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
        max_age=600,
    )


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=(), payment=(), usb=(), browsing-topics=()"
    )
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'; "
        "form-action 'self'; script-src 'self'; style-src 'self'; img-src 'self' https: data:; "
        "font-src 'self'; connect-src 'self'; media-src 'none'"
    )
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    if settings.enable_hsts:
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request: Request, _exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": "Invalid request. Link aur selected options check karein."},
    )


def client_ip(request: Request) -> str:
    direct = request.client.host if request.client else "unknown"
    if not settings.trust_proxy:
        return direct
    forwarded = request.headers.get("x-real-ip", "").strip()
    try:
        return str(ipaddress.ip_address(forwarded))
    except ValueError:
        return direct


def enforce_rate_limit(request: Request, action: str, limit: int) -> None:
    try:
        rate_limiter.check(f"{action}:{client_ip(request)}", limit)
    except RateLimitExceeded as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Thodi der baad try karein.",
            headers={"Retry-After": str(exc.retry_after)},
        ) from None


@app.get("/healthz", include_in_schema=False)
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "a-to-z-link-downloader"}


@app.post("/api/analyze", response_model=MediaInfo)
async def analyze_media(payload: AnalyzeRequest, request: Request) -> MediaInfo:
    enforce_rate_limit(request, "analyze", settings.analyze_limit)
    try:
        async with analyze_slots:
            return await asyncio.wait_for(
                asyncio.to_thread(downloader.analyze, str(payload.url)), timeout=90
            )
    except UnsafeUrlError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    except MediaExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    except TimeoutError:
        raise HTTPException(status_code=504, detail="Link analysis timed out. Dobara try karein.") from None


@app.post("/api/download", response_model=JobCreated, status_code=202)
async def start_download(payload: DownloadRequest, request: Request) -> JobCreated:
    enforce_rate_limit(request, "download", settings.download_limit)
    try:
        safe_url = validate_public_url(str(payload.url))
        job_id = jobs.create(url=safe_url, mode=payload.mode, format_id=payload.format_id)
    except UnsafeUrlError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    except QueueFullError:
        raise HTTPException(
            status_code=503,
            detail="Server queue busy hai. Kuch minute baad try karein.",
            headers={"Retry-After": "60"},
        ) from None
    return JobCreated(job_id=job_id, status_url=f"/api/jobs/{job_id}")


@app.get("/api/jobs/{job_id}", response_model=JobStatus)
async def job_status(job_id: str) -> JobStatus:
    if len(job_id) > 64:
        raise HTTPException(status_code=404, detail="Job not found")
    result = jobs.public_status(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Job not found or expired")
    return result


@app.get("/api/jobs/{job_id}/file")
async def download_file(job_id: str):
    if len(job_id) > 64:
        raise HTTPException(status_code=404, detail="File not found")
    job = jobs.get(job_id)
    if not job or job.status != "ready" or not job.file_path:
        raise HTTPException(status_code=404, detail="File not found or expired")
    file_path = job.file_path.resolve()
    expected_parent = (settings.data_dir / job_id).resolve()
    if file_path.parent != expected_parent or not file_path.is_file():
        logger.warning("Rejected invalid output path for job %s", job_id)
        raise HTTPException(status_code=404, detail="File not found or expired")
    media_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=file_path.name,
        content_disposition_type="attachment",
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )


static_dir = Path(BASE_DIR / "app" / "static")
app.mount("/", StaticFiles(directory=static_dir, html=True), name="site")
