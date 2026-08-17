# A TO Z Link Downloader

A GitHub-ready, mobile-first web app that analyzes a single public media URL and prepares a permitted video or audio download in the best available quality.

## What is included

- Public YouTube video links, Instagram Reels, supported media sites, and generic/direct media URLs through `yt-dlp`
- Metadata preview: title, creator, platform, thumbnail, and duration
- Best available video plus practical resolution choices such as 4K, 1440p, 1080p, and 720p when the source offers them
- MP3 320 kbps conversion and M4A audio output through FFmpeg
- Background jobs with real progress, error, success, and expiry states
- Responsive accessible UI, keyboard focus, reduced-motion support, and Hindi-friendly copy
- AJAYNXT ownership, direct UPI support, editable owner-ad slot, privacy/terms/copyright pages
- Canonical metadata, Open Graph image, JSON-LD, `robots.txt`, XML sitemap, and search-console checklist
- Smart platform finder that suggests the right service for `insta`, `pintrest`, `yt audio` and similar misspelled searches
- Docker/VPS deployment, Nginx example, health check, non-root container, limits, security headers, URL validation, and rate limits

> This project is not a GitHub Pages-only site. Media extraction needs Python, FFmpeg, Node.js, storage, and outbound network access, so deploy the repository on a VPS or a compatible container host.

## Responsible use

Only download content that you own, have permission to use, or are otherwise legally entitled to download. Private/login-only content, DRM bypassing, playlists/channels, and live streams are not supported. Platform terms and applicable law still apply.

## Quick local run

Prerequisites: Python 3.10+, FFmpeg, FFprobe, and Node.js.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --requirement requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

## VPS deployment with Docker

1. Upload or clone this repository on the VPS.
2. Create the environment file:

   ```bash
   cp .env.example .env
   ```

3. The repository is configured for `download.ajaynxt.com`. Add your VPS public IP to the DNS record described below. Keep `ENABLE_HSTS=false` until HTTPS works reliably.
4. Build and start:

   ```bash
   docker compose up -d --build
   docker compose ps
   curl http://127.0.0.1:8080/healthz
   ```

5. Copy `docs/nginx.conf` into the Nginx sites directory, test Nginx, and reload it.
6. Issue a TLS certificate using your established ACME/Certbot process. After HTTPS is verified, set `ENABLE_HSTS=true` and recreate the app container.

The application port is intentionally bound to `127.0.0.1`; expose only Nginx ports 80/443 publicly.

## GoDaddy domain connection

In the DNS manager for `ajaynxt.com`, create this record after you have the VPS public IPv4 address:

| Type | Name | Value | TTL |
|---|---|---|---|
| `A` | `download` | your VPS public IPv4 | default/600 |

Use an `AAAA` record only when the VPS has working public IPv6. Do not point a CNAME at an IP address. After DNS resolves, request the TLS certificate for `download.ajaynxt.com` and then turn on HSTS.

## Configuration

| Variable | Default | Purpose |
|---|---:|---|
| `PUBLIC_BASE_URL` | `https://download.ajaynxt.com` | Canonical URL used by metadata, sitemap and robots |
| `ALLOWED_HOSTS` | local hosts | Comma-separated real domain/host allowlist |
| `TRUST_PROXY` | `false` | Trust `X-Real-IP` only behind the supplied local reverse proxy |
| `ENABLE_HSTS` | `false` | Adds HSTS after HTTPS is verified |
| `MAX_DOWNLOAD_BYTES` | 1 GiB | Per-file size cap |
| `MAX_DURATION_SECONDS` | 10,800 | Three-hour media limit |
| `JOB_TTL_SECONDS` | 3,600 | Temporary file expiry |
| `MAX_WORKERS` | 2 | Concurrent media jobs |
| `ANALYZE_LIMIT_PER_15_MIN` | 20 | Per-IP analyze limit |
| `DOWNLOAD_LIMIT_PER_15_MIN` | 6 | Per-IP job limit |
| `SUPPORT_UPI_ID` | `9929562585@ybl` | Direct support payment deep link and copy button |
| `BUY_ME_A_COFFEE_URL` | blank | Optional external Buy Me a Coffee profile URL |
| `OWNER_AD_TITLE/TEXT/URL` | AJAYNXT service ad | Editable first-party advertisement |
| `GOOGLE_SITE_VERIFICATION` | blank | Search Console HTML meta verification token |
| `ADSENSE_PUBLISHER_ID` | blank | Creates valid `/ads.txt` after an approved `pub-...` ID is supplied |

The owner ad works immediately and is edited only through `.env`. AdSense code is intentionally not injected until an approved publisher ID, ad-unit IDs, privacy/consent requirements, and Google policy eligibility have been confirmed.

## API flow

1. `POST /api/analyze` with `{ "url": "https://..." }`
2. `POST /api/download` with the analyzed URL, output mode, quality ID, and `rights_confirmed: true`
3. Poll the returned `status_url`
4. Download from `file_url` when status becomes `ready`

Interactive API docs are available at `/api/docs` in development and disabled in production.

`requirements.txt` contains direct application dependencies for cross-platform development. `requirements.lock` is the exact Linux deployment/CI lock used by Docker.

## Checks

```bash
python -m compileall -q app tests
python -m unittest discover -s tests -v
docker build -t a-to-z-link-downloader:local .
```

To rebuild the static GitHub Pages preview from the production templates:

```bash
python -m scripts.build_github_pages
```

The generated `pages-dist/` files are published at the repository root. The visual site works on GitHub Pages; actual media extraction still calls the separately deployed FastAPI/FFmpeg backend configured by `FRONTEND_API_BASE_URL`.

## Operational notes

- Jobs are held in process memory and temporary files live in the Docker volume. A restart invalidates active job links; users can start again.
- Site support changes when platforms change. Keep `yt-dlp` current through reviewed dependency updates and CI testing.
- App-level URL validation blocks loopback, private, link-local, reserved addresses, credentials, non-web schemes, and non-standard ports. Because third-party extractors follow their own redirects, production should also block private/link-local destinations at the VPS/container egress layer.
- In-memory rate limiting is suitable for the supplied single-worker deployment. Use a shared rate-limit store before running multiple app replicas.
- Some public Instagram links can still require platform authentication or be rate-limited. The app does not accept or store user cookies.

## Project documents

Architecture, route contracts, UX decisions, security plan, threat model, release checklist, and truthful completion results are in [`docs/`](docs/).

Built for AJAYNXT. Licensed under MIT; dependencies retain their own licenses.
