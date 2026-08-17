from __future__ import annotations

import asyncio
import ipaddress
import logging
import mimetypes
import shutil
import tempfile
from contextlib import asynccontextmanager, suppress
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse, Response as FastAPIResponse
from fastapi.staticfiles import StaticFiles
from starlette.background import BackgroundTask

from app.config import BASE_DIR, settings
from app.models import AnalyzeRequest, DownloadRequest, MediaInfo
from app.security import UnsafeUrlError, validate_public_url
from app.seo import build_ads_txt, build_robots, build_sitemap, render_page
from app.services.downloader import MediaDownloader, MediaExtractionError
from app.services.rate_limit import RateLimitExceeded, SlidingWindowRateLimiter


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

downloader = MediaDownloader(settings)
rate_limiter = SlidingWindowRateLimiter(window_seconds=900)
analyze_slots = asyncio.Semaphore(settings.max_workers * 2)
download_slots = asyncio.Semaphore(settings.max_workers)


async def cleanup_loop() -> None:
    while True:
        await asyncio.sleep(300)
        rate_limiter.prune()


def purge_abandoned_temp_files() -> None:
    """Remove only request folders created by this app after an interrupted process."""
    settings.temp_dir.mkdir(parents=True, exist_ok=True)
    for child in settings.temp_dir.iterdir():
        if child.is_dir() and child.name.startswith("request-"):
            shutil.rmtree(child, ignore_errors=True)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await asyncio.to_thread(purge_abandoned_temp_files)
    task = asyncio.create_task(cleanup_loop())
    yield
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    docs_url=None if settings.is_production else "/api/docs",
    redoc_url=None,
    openapi_url=None if settings.is_production else "/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(settings.allowed_hosts))

# Public downloader API: browser clients can come from the GitHub Pages custom
# domain as well as future AJAYNXT frontends. No cookies/credentials are used,
# so wildcard CORS is safe here and avoids brittle origin mismatches.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Length"],
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
    if request.url.path.startswith("/api/") or request.url.path == "/healthz":
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Robots-Tag"] = "noindex, nofollow"
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


static_dir = Path(BASE_DIR / "app" / "static")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def homepage() -> str:
    return render_page(static_dir / "index.html", settings, "/")


@app.get("/supported-sites", response_class=HTMLResponse, include_in_schema=False)
async def supported_sites() -> str:
    return render_page(static_dir / "supported-sites.html", settings, "/supported-sites")


@app.get("/privacy", response_class=HTMLResponse, include_in_schema=False)
async def privacy() -> str:
    return render_page(static_dir / "privacy.html", settings, "/privacy")


@app.get("/terms", response_class=HTMLResponse, include_in_schema=False)
async def terms() -> str:
    return render_page(static_dir / "terms.html", settings, "/terms")


@app.get("/copyright", response_class=HTMLResponse, include_in_schema=False)
async def copyright_policy() -> str:
    return render_page(static_dir / "copyright.html", settings, "/copyright")


@app.get("/robots.txt", response_class=PlainTextResponse, include_in_schema=False)
async def robots() -> str:
    return build_robots(settings.public_base_url)


@app.get("/sitemap.xml", include_in_schema=False)
async def sitemap() -> FastAPIResponse:
    return FastAPIResponse(
        content=build_sitemap(settings.public_base_url),
        media_type="application/xml",
    )


@app.get("/ads.txt", response_class=PlainTextResponse, include_in_schema=False)
async def ads_txt() -> str:
    content = build_ads_txt(settings.adsense_publisher_id)
    if content is None:
        raise HTTPException(status_code=404, detail="Ads publisher is not configured")
    return content


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


@app.post("/api/download")
async def direct_download(payload: DownloadRequest, request: Request) -> FileResponse:
    """Prepare one permitted file, send it directly, then remove all temporary bytes."""
    enforce_rate_limit(request, "download", settings.download_limit)
    try:
        safe_url = validate_public_url(str(payload.url))
    except UnsafeUrlError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None

    request_dir = Path(tempfile.mkdtemp(prefix="request-", dir=settings.temp_dir)).resolve()

    def progress_hook(data: dict) -> None:
        downloaded = data.get("downloaded_bytes") or 0
        if downloaded > settings.max_download_bytes:
            raise MediaExtractionError("Downloaded file exceeds the configured size limit.")

    async def prepare_file() -> Path:
        async with download_slots:
            return await asyncio.to_thread(
                downloader.download,
                url=safe_url,
                mode=payload.mode,
                format_id=payload.format_id,
                temp_dir=request_dir,
                progress_hook=progress_hook,
                postprocessor_hook=lambda _data: None,
            )
    preparation = asyncio.create_task(prepare_file())
    try:
        file_path = await asyncio.shield(preparation)
    except asyncio.CancelledError:
        preparation.add_done_callback(
            lambda _task: shutil.rmtree(request_dir, ignore_errors=True)
        )
        raise
    except UnsafeUrlError as exc:
        shutil.rmtree(request_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail=str(exc)) from None
    except MediaExtractionError as exc:
        shutil.rmtree(request_dir, ignore_errors=True)
        raise HTTPException(status_code=422, detail=str(exc)) from None
    except Exception:
        shutil.rmtree(request_dir, ignore_errors=True)
        logger.exception("Direct media preparation failed")
        raise HTTPException(
            status_code=500,
            detail="File prepare nahi hui. Thodi der baad dobara try karein.",
        ) from None

    if file_path.parent != request_dir or not file_path.is_file():
        shutil.rmtree(request_dir, ignore_errors=True)
        logger.warning("Rejected invalid direct-download output path")
        raise HTTPException(status_code=500, detail="Prepared file path was rejected")

    media_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=file_path.name,
        content_disposition_type="attachment",
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
        background=BackgroundTask(shutil.rmtree, request_dir, ignore_errors=True),
    )


app.mount("/", StaticFiles(directory=static_dir, html=True), name="site")
