from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.config import Settings
from app.seo import PUBLIC_ROUTES, build_ads_txt, build_robots, build_sitemap, render_page


class SeoEndpointContentTests(unittest.TestCase):
    def test_sitemap_uses_absolute_canonical_urls(self):
        sitemap = build_sitemap("https://download.ajaynxt.com/")
        for path in PUBLIC_ROUTES:
            self.assertIn(f"<loc>https://download.ajaynxt.com{path}</loc>", sitemap)
        self.assertNotIn("priority", sitemap)

    def test_robots_points_to_canonical_sitemap_and_blocks_api(self):
        robots = build_robots("https://download.ajaynxt.com")
        self.assertIn("Disallow: /api/", robots)
        self.assertIn("Sitemap: https://download.ajaynxt.com/sitemap.xml", robots)

    def test_ads_txt_requires_valid_publisher_id(self):
        self.assertIsNone(build_ads_txt(""))
        self.assertIsNone(build_ads_txt("ca-pub-not-valid"))
        self.assertEqual(
            build_ads_txt("pub-1234567890123456"),
            "google.com, pub-1234567890123456, DIRECT, f08c47fec0942fa0\n",
        )

    def test_page_rendering_includes_canonical_upi_and_owner(self):
        with tempfile.TemporaryDirectory() as folder:
            template = Path(folder) / "page.html"
            template.write_text(
                "__CANONICAL_URL__ __UPI_NAV__ __UPI_SUPPORT__ __OWNER_NAME__",
                encoding="utf-8",
            )
            page = render_page(template, Settings(), "/")
        self.assertIn("https://download.ajaynxt.com/", page)
        self.assertIn("9929562585@ybl", page)
        self.assertIn("Support AJAYNXT", page)
        self.assertIn("AJAYNXT", page)


if __name__ == "__main__":
    unittest.main()
