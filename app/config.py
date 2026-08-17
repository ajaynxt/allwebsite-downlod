from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


def _int_env(name: str, default: int, minimum: int, maximum: int) -> int:
    raw = os.getenv(name, str(default))
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc
    if not minimum <= value <= maximum:
        raise RuntimeError(f"{name} must be between {minimum} and {maximum}")
    return value


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "A TO Z Link Downloader")
    environment: str = os.getenv("APP_ENV", "development")
    public_base_url: str = os.getenv(
        "PUBLIC_BASE_URL", "https://download.ajaynxt.com"
    ).rstrip("/")
    frontend_api_base_url: str = os.getenv("FRONTEND_API_BASE_URL", "").rstrip("/")
    owner_name: str = os.getenv("OWNER_NAME", "AJAYNXT")
    contact_email: str = os.getenv("CONTACT_EMAIL", "ajayx3neha@gmail.com")
    support_upi_id: str = os.getenv("SUPPORT_UPI_ID", "9929562585@ybl").strip()
    buy_me_a_coffee_url: str = os.getenv("BUY_ME_A_COFFEE_URL", "").strip()
    google_site_verification: str = os.getenv("GOOGLE_SITE_VERIFICATION", "").strip()
    adsense_publisher_id: str = os.getenv("ADSENSE_PUBLISHER_ID", "").strip()
    owner_ad_title: str = os.getenv("OWNER_AD_TITLE", "Website ya app banwani hai?").strip()
    owner_ad_text: str = os.getenv(
        "OWNER_AD_TEXT", "AJAYNXT se premium website, automation aur digital product banwayein."
    ).strip()
    owner_ad_url: str = os.getenv("OWNER_AD_URL", "https://ajaynxt.com/").strip()
    data_dir: Path = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data" / "jobs"))).resolve()
    max_download_bytes: int = _int_env(
        "MAX_DOWNLOAD_BYTES", 1_073_741_824, 10_485_760, 5_368_709_120
    )
    max_duration_seconds: int = _int_env("MAX_DURATION_SECONDS", 10_800, 60, 43_200)
    socket_timeout_seconds: int = _int_env("SOCKET_TIMEOUT_SECONDS", 20, 5, 120)
    job_ttl_seconds: int = _int_env("JOB_TTL_SECONDS", 3_600, 300, 86_400)
    max_workers: int = _int_env("MAX_WORKERS", 2, 1, 8)
    analyze_limit: int = _int_env("ANALYZE_LIMIT_PER_15_MIN", 20, 1, 500)
    download_limit: int = _int_env("DOWNLOAD_LIMIT_PER_15_MIN", 6, 1, 100)
    allowed_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")
        if origin.strip()
    )
    allowed_hosts: tuple[str, ...] = tuple(
        host.strip().lower()
        for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")
        if host.strip()
    )
    trust_proxy: bool = os.getenv("TRUST_PROXY", "false").lower() == "true"
    enable_hsts: bool = os.getenv("ENABLE_HSTS", "false").lower() == "true"

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
