from __future__ import annotations

import logging
import secrets
import shutil
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from yt_dlp.utils import DownloadError

from app.config import Settings
from app.models import JobStatus
from app.services.downloader import MediaDownloader, MediaExtractionError


logger = logging.getLogger(__name__)


class QueueFullError(RuntimeError):
    pass


@dataclass(slots=True)
class JobRecord:
    job_id: str
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    status: str = "queued"
    progress: int = 0
    message: str = "Queue mein add ho gaya"
    file_path: Path | None = None


class JobManager:
    def __init__(self, settings: Settings, downloader: MediaDownloader) -> None:
        self.settings = settings
        self.downloader = downloader
        self._jobs: dict[str, JobRecord] = {}
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(
            max_workers=settings.max_workers, thread_name_prefix="media-download"
        )

    def create(self, *, url: str, mode: str, format_id: str) -> str:
        with self._lock:
            active = sum(
                job.status in {"queued", "downloading", "processing"}
                for job in self._jobs.values()
            )
            if active >= self.settings.max_workers * 4:
                raise QueueFullError("Server queue is currently full")
            job_id = secrets.token_urlsafe(18)
            self._jobs[job_id] = JobRecord(job_id=job_id)
        self._executor.submit(self._run, job_id, url, mode, format_id)
        return job_id

    def _update(self, job_id: str, **changes: object) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            for key, value in changes.items():
                setattr(job, key, value)
            job.updated_at = time.time()

    def _run(self, job_id: str, url: str, mode: str, format_id: str) -> None:
        job_dir = (self.settings.data_dir / job_id).resolve()
        try:
            job_dir.mkdir(parents=True, exist_ok=False)
        except Exception:
            logger.exception("Could not create output directory for job %s", job_id)
            self._update(
                job_id,
                status="failed",
                progress=0,
                message="Server storage is not available. Please try again later.",
            )
            return
        self._update(job_id, status="downloading", progress=1, message="Media download ho raha hai")

        def progress_hook(data: dict) -> None:
            status = data.get("status")
            if status == "downloading":
                downloaded = data.get("downloaded_bytes") or 0
                total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
                if downloaded > self.settings.max_download_bytes:
                    raise DownloadError("Download exceeds configured file size limit")
                percent = int((downloaded / total) * 94) if total else 5
                self._update(
                    job_id,
                    status="downloading",
                    progress=max(1, min(94, percent)),
                    message="Best quality media download ho raha hai",
                )
            elif status == "finished":
                self._update(
                    job_id,
                    status="processing",
                    progress=95,
                    message="File final format mein prepare ho rahi hai",
                )

        def postprocessor_hook(data: dict) -> None:
            if data.get("status") == "started":
                self._update(
                    job_id,
                    status="processing",
                    progress=97,
                    message="Audio/video processing chal rahi hai",
                )

        try:
            output = self.downloader.download(
                url=url,
                mode=mode,
                format_id=format_id,
                job_dir=job_dir,
                progress_hook=progress_hook,
                postprocessor_hook=postprocessor_hook,
            )
            self._update(
                job_id,
                status="ready",
                progress=100,
                message="File ready hai",
                file_path=output,
            )
        except MediaExtractionError as exc:
            logger.info("Job %s failed with a handled extraction error", job_id)
            shutil.rmtree(job_dir, ignore_errors=True)
            self._update(job_id, status="failed", progress=0, message=str(exc))
        except Exception:
            logger.exception("Job %s failed unexpectedly", job_id)
            shutil.rmtree(job_dir, ignore_errors=True)
            self._update(
                job_id,
                status="failed",
                progress=0,
                message="Unexpected server error. Please try again later.",
            )

    def get(self, job_id: str) -> JobRecord | None:
        with self._lock:
            return self._jobs.get(job_id)

    def public_status(self, job_id: str) -> JobStatus | None:
        job = self.get(job_id)
        if not job:
            return None
        ready = job.status == "ready" and job.file_path is not None
        return JobStatus(
            job_id=job.job_id,
            status=job.status,
            progress=job.progress,
            message=job.message,
            filename=job.file_path.name if ready else None,
            file_url=f"/api/jobs/{job.job_id}/file" if ready else None,
        )

    def cleanup(self) -> int:
        cutoff = time.time() - self.settings.job_ttl_seconds
        removed = 0
        with self._lock:
            expired = [
                job_id
                for job_id, job in self._jobs.items()
                if job.updated_at < cutoff and job.status not in {"downloading", "processing"}
            ]
            for job_id in expired:
                self._jobs.pop(job_id, None)
                shutil.rmtree(self.settings.data_dir / job_id, ignore_errors=True)
                removed += 1
        return removed

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)
