from __future__ import annotations

import shutil
from pathlib import Path

from app.config import BASE_DIR, Settings
from app.seo import build_robots, render_page


PAGES_URL = "https://ajaynxt.github.io/allwebsite-downlod"
API_URL = "https://download.ajaynxt.com"
STATIC_DIR = BASE_DIR / "app" / "static"
OUTPUT_DIR = BASE_DIR / "pages-dist"

PAGE_TEMPLATES = {
    "index.html": ("index.html", "/"),
    "supported-sites.html": ("supported-sites.html", "/supported-sites.html"),
    "privacy.html": ("privacy.html", "/privacy.html"),
    "terms.html": ("terms.html", "/terms.html"),
    "copyright.html": ("copyright.html", "/copyright.html"),
}

ASSETS = ("styles.css", "app.js")


def make_relative(page: str) -> str:
    replacements = {
        'href="/supported-sites"': 'href="./supported-sites.html"',
        'href="/privacy"': 'href="./privacy.html"',
        'href="/terms"': 'href="./terms.html"',
        'href="/copyright"': 'href="./copyright.html"',
        'href="/#': 'href="./#',
        'href="/"': 'href="./"',
        'href="/favicon.svg"': 'href="./app/static/favicon.svg"',
        'href="/styles.css"': 'href="./styles.css"',
        'src="/app.js"': 'src="./app.js"',
        'src="/ajaynxt-panther-logo.jpeg"': 'src="./app/static/ajaynxt-panther-logo.jpeg"',
        f'{PAGES_URL}/social-cover.png': f'{PAGES_URL}/app/static/social-cover.png',
    }
    for source, target in replacements.items():
        page = page.replace(source, target)
    return page


def sitemap() -> str:
    paths = tuple(canonical for _, canonical in PAGE_TEMPLATES.values())
    entries = "".join(
        f"<url><loc>{PAGES_URL}{path}</loc><lastmod>2026-08-17</lastmod></url>"
        for path in paths
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{entries}</urlset>"
    )


def build() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    settings = Settings(public_base_url=PAGES_URL, frontend_api_base_url=API_URL)
    for output_name, (template_name, canonical_path) in PAGE_TEMPLATES.items():
        rendered = render_page(STATIC_DIR / template_name, settings, canonical_path)
        (OUTPUT_DIR / output_name).write_text(make_relative(rendered), encoding="utf-8")
    for asset in ASSETS:
        shutil.copy2(STATIC_DIR / asset, OUTPUT_DIR / asset)
    (OUTPUT_DIR / "robots.txt").write_text(build_robots(PAGES_URL), encoding="utf-8")
    (OUTPUT_DIR / "sitemap.xml").write_text(sitemap(), encoding="utf-8")
    (OUTPUT_DIR / ".nojekyll").write_text("", encoding="utf-8")


if __name__ == "__main__":
    build()
