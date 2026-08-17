from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yt_dlp
from yt_dlp.utils import DownloadError

from app.config import Settings
from app.models import FormatOption, MediaInfo
from app.security import UnsafeUrlError, validate_public_url


logger = logging.getLogger(__name__)


class MediaExtractionError(RuntimeError):
    """A safe, user-displayable media extraction error."""


class QuietLogger:
    def debug(self, _message: str) -> None:
        return

    def info(self, _message: str) -> None:
        return

    def warning(self, _message: str) -> None:
        return

    def error(self, _message: str) -> None:
        return


def _bytes_from_format(item: dict[str, Any]) -> int | None:
    size = item.get("filesize") or item.get("filesize_approx")
    return int(size) if isinstance(size, (int, float)) and size > 0 else None


def build_format_options(info: dict[str, Any]) -> list[FormatOption]:
    options = [
        FormatOption(
            id="best",
            kind="video",
            label="Best Quality",
            detail="Highest video + audio available",
            extension="mp4",
            recommended=True,
        )
    ]

    by_height: dict[int, dict[str, Any]] = {}
    for item in info.get("formats") or []:
        if item.get("vcodec") in {None, "none"}:
            continue
        height = item.get("height")
        if not isinstance(height, int) or height < 144:
            continue
        current = by_height.get(height)
        if current is None or (item.get("tbr") or 0) > (current.get("tbr") or 0):
            by_height[height] = item

    preferred = [2160, 1440, 1080, 720, 480, 360, 240]
    available = sorted(by_height, reverse=True)
    picked: list[int] = []
    for target in preferred:
        nearest = next((height for height in available if height <= target), None)
        if nearest and nearest not in picked:
            picked.append(nearest)
    for height in picked[:6]:
        item = by_height[height]
        fps = item.get("fps")
        fps_label = f" · {int(fps)} fps" if isinstance(fps, (int, float)) and fps >= 50 else ""
        name = "4K" if height >= 2160 else "2K" if height >= 1440 else f"{height}p"
        options.append(
            FormatOption(
                id=f"height-{height}",
                kind="video",
                label=name,
                detail=f"MP4 video + audio{fps_label}",
                extension="mp4",
                estimated_bytes=_bytes_from_format(item),
            )
        )

    options.extend(
        [
            FormatOption(
                id="audio-best",
                kind="audio",
                label="MP3 · Best",
                detail="High-quality 320 kbps conversion",
                extension="mp3",
            ),
            FormatOption(
                id="audio-best",
                kind="audio",
                label="M4A · Best",
                detail="Efficient, high-quality audio",
                extension="m4a",
            ),
        ]
    )
    return options


def _safe_thumbnail(candidate: Any) -> str | None:
    if not isinstance(candidate, str):
        return None
    try:
        return validate_public_url(candidate)
    except UnsafeUrlError:
        return None


class MediaDownloader:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _base_options(self) -> dict[str, Any]:
        return {
            "logger": QuietLogger(),
            "quiet": True,
            "no_warnings": True,
            "ignoreconfig": True,
            "noplaylist": True,
            "playlistend": 1,
            "socket_timeout": self.settings.socket_timeout_seconds,
            "retries": 2,
            "fragment_retries": 2,
            "extractor_retries": 2,
            "cachedir": False,
            "check_formats": True,
            "max_filesize": self.settings.max_download_bytes,
            "concurrent_fragment_downloads": 2,
            "js_runtimes": {"node": {}},
        }

    def analyze(self, url: str) -> MediaInfo:
        safe_url = validate_public_url(url)
        options = {
            **self._base_options(),
            "skip_download": True,
            "extract_flat": False,
        }
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                raw = ydl.extract_info(safe_url, download=False)
                info = ydl.sanitize_info(raw)
        except (DownloadError, OSError, ValueError) as exc:
            logger.info("Media analysis failed: %s", type(exc).__name__)
            raise MediaExtractionError(
                "Link read nahi ho saka. Public single-video/Reel link check karke dobara try karein."
            ) from None

        if not isinstance(info, dict) or info.get("entries") is not None:
            raise MediaExtractionError("Playlist/channel nahi, ek single video ya Reel link paste karein.")
        if info.get("is_live"):
            raise MediaExtractionError("Live streams is version mein supported nahi hain.")

        duration = info.get("duration")
        if isinstance(duration, (int, float)) and duration > self.settings.max_duration_seconds:
            raise MediaExtractionError("Yeh media configured duration limit se bada hai.")

        title = str(info.get("title") or "Untitled media").strip()[:200]
        creator = info.get("uploader") or info.get("channel") or info.get("creator")
        platform = str(info.get("extractor_key") or info.get("extractor") or "Website")[:80]
        return MediaInfo(
            title=title,
            creator=str(creator).strip()[:120] if creator else None,
            platform=platform,
            duration_seconds=int(duration) if isinstance(duration, (int, float)) else None,
            thumbnail=_safe_thumbnail(info.get("thumbnail")),
            webpage_url=safe_url,
            formats=build_format_options(info),
        )

    def download(
        self,
        *,
        url: str,
        mode: str,
        format_id: str,
        temp_dir: Path,
        progress_hook: Any,
        postprocessor_hook: Any,
    ) -> Path:
        safe_url = validate_public_url(url)

        if mode == "video":
            if format_id == "best":
                selector = "bv*+ba/b"
            elif format_id.startswith("height-") and format_id[7:].isdigit():
                height = int(format_id[7:])
                if height < 144 or height > 4320:
                    raise MediaExtractionError("Invalid video quality selected.")
                selector = f"bv*[height<={height}]+ba/b[height<={height}]/b"
            else:
                raise MediaExtractionError("Invalid video quality selected.")
        else:
            selector = "bestaudio/best"

        def match_filter(info: dict[str, Any], *, incomplete: bool) -> str | None:
            if info.get("is_live"):
                return "Live streams are not supported"
            duration = info.get("duration")
            if duration and duration > self.settings.max_duration_seconds:
                return "Media exceeds the configured duration limit"
            return None

        options: dict[str, Any] = {
            **self._base_options(),
            "format": selector,
            "outtmpl": str(temp_dir / "%(title).120B [%(id)s].%(ext)s"),
            "restrictfilenames": True,
            "windowsfilenames": True,
            "overwrites": False,
            "continuedl": False,
            "progress_hooks": [progress_hook],
            "postprocessor_hooks": [postprocessor_hook],
            "match_filter": match_filter,
        }
        if mode == "video":
            options["merge_output_format"] = "mp4"
        elif mode == "mp3":
            options["postprocessors"] = [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "320"}
            ]
        elif mode == "m4a":
            options["postprocessors"] = [
                {"key": "FFmpegExtractAudio", "preferredcodec": "m4a", "preferredquality": "0"}
            ]
        else:
            raise MediaExtractionError("Invalid output format selected.")

        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                result = ydl.download([safe_url])
            if result != 0:
                raise MediaExtractionError("Download could not be completed.")
        except MediaExtractionError:
            raise
        except (DownloadError, OSError, ValueError) as exc:
            logger.info("Media download failed: %s", type(exc).__name__)
            raise MediaExtractionError(
                "Download complete nahi hua. Link private, expired, blocked ya unsupported ho sakta hai."
            ) from None

        candidates = [
            path
            for path in temp_dir.iterdir()
            if path.is_file() and path.suffix.lower() not in {".part", ".ytdl", ".json"}
        ]
        if not candidates:
            raise MediaExtractionError("Downloaded file could not be prepared.")
        output = max(candidates, key=lambda item: item.stat().st_size).resolve()
        if output.parent != temp_dir.resolve():
            raise MediaExtractionError("Unsafe output path was rejected.")
        if output.stat().st_size > self.settings.max_download_bytes:
            output.unlink(missing_ok=True)
            raise MediaExtractionError("Downloaded file exceeds the configured size limit.")
        return output
