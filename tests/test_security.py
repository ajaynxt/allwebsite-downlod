from __future__ import annotations

import socket
import unittest

from app.security import UnsafeUrlError, validate_public_url


def resolver_for(address: str):
    def fake_resolver(_host: str, port: int, type: int = socket.SOCK_STREAM):
        return [(socket.AF_INET, type, 6, "", (address, port))]

    return fake_resolver


class PublicUrlValidationTests(unittest.TestCase):
    def test_accepts_public_https_and_removes_fragment(self):
        value = validate_public_url(
            "HTTPS://Example.COM/watch?v=1#secret", resolver=resolver_for("93.184.216.34")
        )
        self.assertEqual(value, "https://example.com/watch?v=1")

    def test_rejects_private_ip_resolution(self):
        with self.assertRaises(UnsafeUrlError):
            validate_public_url("https://example.com/video", resolver=resolver_for("127.0.0.1"))

    def test_rejects_credentials(self):
        with self.assertRaises(UnsafeUrlError):
            validate_public_url(
                "https://user:pass@example.com/video", resolver=resolver_for("93.184.216.34")
            )

    def test_rejects_nonstandard_port(self):
        with self.assertRaises(UnsafeUrlError):
            validate_public_url(
                "https://example.com:8443/video", resolver=resolver_for("93.184.216.34")
            )

    def test_rejects_file_scheme(self):
        with self.assertRaises(UnsafeUrlError):
            validate_public_url("file:///etc/passwd", resolver=resolver_for("93.184.216.34"))


if __name__ == "__main__":
    unittest.main()
