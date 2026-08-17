from __future__ import annotations

import html
import json
import re
from pathlib import Path
from urllib.parse import quote

from app.config import Settings


PUBLIC_ROUTES = ("/", "/supported-sites", "/privacy", "/terms", "/copyright")
ADSENSE_PUBLISHER_PATTERN = re.compile(r"^pub-\d{10,20}$")


def build_robots(base_url: str) -> str:
    return (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /api/\n"
        "Disallow: /healthz\n\n"
        f"Sitemap: {base_url.rstrip('/')}/sitemap.xml\n"
    )


def build_sitemap(base_url: str, last_modified: str = "2026-08-17") -> str:
    base = base_url.rstrip("/")
    entries = "".join(
        f"<url><loc>{html.escape(base + path)}</loc><lastmod>{last_modified}</lastmod></url>"
        for path in PUBLIC_ROUTES
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{entries}</urlset>"
    )


def build_ads_txt(publisher_id: str) -> str | None:
    if not ADSENSE_PUBLISHER_PATTERN.fullmatch(publisher_id):
        return None
    return f"google.com, {publisher_id}, DIRECT, f08c47fec0942fa0\n"


def _upi_link(upi_id: str, owner_name: str) -> str:
    return (
        "upi://pay?pa="
        f"{quote(upi_id, safe='@')}&pn={quote(owner_name)}&cu=INR"
        "&tn=Support%20A%20TO%20Z%20Link%20Downloader"
    )


def render_page(template_path: Path, settings: Settings, canonical_path: str) -> str:
    base = settings.public_base_url.rstrip("/")
    page = template_path.read_text(encoding="utf-8")
    google_verification = ""
    if settings.google_site_verification:
        token = html.escape(settings.google_site_verification, quote=True)
        google_verification = f'<meta name="google-site-verification" content="{token}">'

    upi_block = '<p class="support-pending">UPI support launch se pehle configure karein.</p>'
    upi_nav = ""
    if settings.support_upi_id:
        upi_id = html.escape(settings.support_upi_id)
        upi_url = html.escape(
            _upi_link(settings.support_upi_id, settings.owner_name), quote=True
        )
        upi_nav = f'<a class="support-nav" href="{upi_url}">Support AJAYNXT</a>'
        upi_block = (
            f'<a class="support-primary" href="{upi_url}">Pay securely with UPI ↗</a>'
            f'<button class="copy-upi" type="button" data-copy-upi="{upi_id}">'
            f'<span>{upi_id}</span><small>Copy UPI ID</small></button>'
        )

    coffee_block = ""
    if settings.buy_me_a_coffee_url.startswith("https://"):
        coffee_url = html.escape(settings.buy_me_a_coffee_url, quote=True)
        coffee_block = (
            f'<a class="support-secondary" href="{coffee_url}" target="_blank" '
            'rel="noopener noreferrer">Buy me a coffee ↗</a>'
        )

    owner_ad = ""
    if settings.owner_ad_url.startswith("https://") and settings.owner_ad_title:
        owner_ad_url = html.escape(settings.owner_ad_url, quote=True)
        owner_ad_title = html.escape(settings.owner_ad_title)
        owner_ad_text = html.escape(settings.owner_ad_text)
        owner_ad = (
            '<aside class="owner-ad" aria-label="AJAYNXT advertisement">'
            '<span>AJAYNXT AD</span><div>'
            f'<strong>{owner_ad_title}</strong><p>{owner_ad_text}</p></div>'
            f'<a href="{owner_ad_url}" target="_blank" rel="sponsored noopener">Know more ↗</a>'
            "</aside>"
        )

    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Organization",
                "@id": "https://ajaynxt.com/#organization",
                "name": settings.owner_name,
                "url": "https://ajaynxt.com/",
                "email": settings.contact_email,
                "sameAs": [
                    "https://www.instagram.com/ajay_nxt_/",
                    "https://x.com/Ajay_Nxt_",
                ],
            },
            {
                "@type": "WebSite",
                "@id": f"{base}/#website",
                "url": f"{base}/",
                "name": settings.app_name,
                "publisher": {"@id": "https://ajaynxt.com/#organization"},
                "inLanguage": "en-IN",
            },
            {
                "@type": "WebApplication",
                "@id": f"{base}/#app",
                "name": settings.app_name,
                "url": f"{base}/",
                "applicationCategory": "MultimediaApplication",
                "operatingSystem": "Any",
                "isAccessibleForFree": True,
                "offers": {"@type": "Offer", "price": "0", "priceCurrency": "INR"},
                "description": "Save permitted public video, Reel and audio links in the best available source quality.",
                "publisher": {"@id": "https://ajaynxt.com/#organization"},
            },
        ],
    }

    schema_json = json.dumps(schema, separators=(",", ":"), ensure_ascii=True)
    schema_json = schema_json.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")

    replacements = {
        "__PUBLIC_BASE_URL__": html.escape(base, quote=True),
        "__API_BASE_URL__": html.escape(settings.frontend_api_base_url, quote=True),
        "__CANONICAL_URL__": html.escape(base + canonical_path, quote=True),
        "__GOOGLE_SITE_VERIFICATION__": google_verification,
        "__SCHEMA_JSON__": schema_json,
        "__UPI_NAV__": upi_nav,
        "__UPI_SUPPORT__": upi_block,
        "__COFFEE_SUPPORT__": coffee_block,
        "__OWNER_AD_SLOT__": owner_ad,
        "__OWNER_NAME__": html.escape(settings.owner_name),
        "__CONTACT_EMAIL__": html.escape(settings.contact_email),
    }
    for marker, value in replacements.items():
        page = page.replace(marker, value)
    return page
