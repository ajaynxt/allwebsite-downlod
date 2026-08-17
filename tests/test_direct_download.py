from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from starlette.requests import Request

import app.main as main_module
from app.config import Settings
from app.models import DownloadRequest
from app.services.downloader import MediaExtractionError


def make_request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/download",
            "headers": [],
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
            "scheme": "http",
            "query_string": b"",
        }
    )


def make_payload() -> DownloadRequest:
    return DownloadRequest(
        url="https://example.com/video",
        mode="video",
        format_id="best",
        rights_confirmed=True,
    )


class DirectDownloadTests(unittest.IsolatedAsyncioTestCase):
    async def test_attachment_is_sent_and_temporary_folder_is_removed(self):
        with tempfile.TemporaryDirectory() as root:
            test_settings = Settings(temp_dir=Path(root), download_limit=100)

            def fake_download(**kwargs):
                output = kwargs["temp_dir"] / "AJAYNXT-test.mp4"
                output.write_bytes(b"permitted-media")
                return output

            with (
                patch.object(main_module, "settings", test_settings),
                patch.object(
                    main_module,
                    "validate_public_url",
                    return_value="https://example.com/video",
                ),
                patch.object(main_module.downloader, "download", side_effect=fake_download),
            ):
                response = await main_module.direct_download(make_payload(), make_request())

            self.assertEqual(Path(response.path).read_bytes(), b"permitted-media")
            self.assertIn("attachment", response.headers["content-disposition"])
            self.assertEqual(response.headers["cache-control"], "no-store")
            await response.background()
            self.assertEqual(list(Path(root).iterdir()), [])

    def test_startup_cleanup_only_removes_owned_request_folders(self):
        with tempfile.TemporaryDirectory() as root:
            temp_root = Path(root)
            owned = temp_root / "request-abandoned"
            unrelated = temp_root / "keep-this"
            owned.mkdir()
            unrelated.mkdir()
            (owned / "partial.mp4").write_bytes(b"partial")
            (unrelated / "user.txt").write_text("keep", encoding="utf-8")

            with patch.object(main_module, "settings", Settings(temp_dir=temp_root)):
                main_module.purge_abandoned_temp_files()

            self.assertFalse(owned.exists())
            self.assertTrue(unrelated.is_dir())
            self.assertEqual((unrelated / "user.txt").read_text(encoding="utf-8"), "keep")

    async def test_failed_preparation_also_removes_temporary_folder(self):
        with tempfile.TemporaryDirectory() as root:
            test_settings = Settings(temp_dir=Path(root), download_limit=100)

            with (
                patch.object(main_module, "settings", test_settings),
                patch.object(
                    main_module,
                    "validate_public_url",
                    return_value="https://example.com/video",
                ),
                patch.object(
                    main_module.downloader,
                    "download",
                    side_effect=MediaExtractionError("Source blocked the download."),
                ),
            ):
                with self.assertRaises(HTTPException) as raised:
                    await main_module.direct_download(make_payload(), make_request())

            self.assertEqual(raised.exception.status_code, 422)
            self.assertEqual(raised.exception.detail, "Source blocked the download.")
            self.assertEqual(list(Path(root).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
