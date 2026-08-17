from __future__ import annotations

import unittest

from pydantic import ValidationError

from app.models import DownloadRequest
from app.services.downloader import build_format_options
from app.services.rate_limit import RateLimitExceeded, SlidingWindowRateLimiter


class FormatOptionTests(unittest.TestCase):
    def test_builds_best_video_resolutions_and_audio(self):
        info = {
            "formats": [
                {"format_id": "a", "height": 720, "vcodec": "avc1", "tbr": 1200},
                {"format_id": "b", "height": 1080, "vcodec": "avc1", "tbr": 2500},
                {"format_id": "c", "height": None, "vcodec": "none", "abr": 128},
            ]
        }
        options = build_format_options(info)
        ids = [item.id for item in options]
        self.assertEqual(ids[0], "best")
        self.assertIn("height-1080", ids)
        self.assertIn("height-720", ids)
        self.assertEqual(sum(item.kind == "audio" for item in options), 2)


class RateLimitTests(unittest.TestCase):
    def test_sliding_window_limit_and_expiry(self):
        limiter = SlidingWindowRateLimiter(window_seconds=10)
        limiter.check("download:ip", limit=2, now=100)
        limiter.check("download:ip", limit=2, now=101)
        with self.assertRaises(RateLimitExceeded):
            limiter.check("download:ip", limit=2, now=102)
        limiter.check("download:ip", limit=2, now=111)


class RequestValidationTests(unittest.TestCase):
    def test_download_requires_rights_confirmation(self):
        with self.assertRaises(ValidationError):
            DownloadRequest(
                url="https://example.com/video", mode="video", format_id="best", rights_confirmed=False
            )

    def test_rejects_format_expression(self):
        with self.assertRaises(ValidationError):
            DownloadRequest(
                url="https://example.com/video",
                mode="video",
                format_id="best[height>0]",
                rights_confirmed=True,
            )


if __name__ == "__main__":
    unittest.main()
