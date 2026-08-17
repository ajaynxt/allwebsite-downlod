# Security Plan

## Project

- Name: A TO Z Link Downloader 1.0.0
- Date: 2026-08-17
- Owner: AJAYNXT
- Risk class: S2 Business (public outbound URL processing, server-side media parsing, temporary generated files)
- Environments: local development and production VPS/container

## Architecture

- Frontend: same-origin static HTML/CSS/JavaScript
- Backend: FastAPI/Uvicorn, one process, bounded thread pool
- Authentication/database: none
- External services: arbitrary validated public media host through yt-dlp; no account cookies
- Processing/storage: FFmpeg and temporary Docker volume, one-hour default expiry
- Hosting: non-root container behind Nginx/TLS; public ports limited to 80/443
- CI: read-only GitHub workflow with pinned action revisions
- Logging: application events and job IDs; no full URLs, cookies, tokens, or request bodies
- Backup: source/configuration in Git; media/job data is intentionally ephemeral and excluded

## Sensitive assets

| Asset/data | Classification | Stored where | Access | Retention |
|---|---|---|---|---|
| Pasted source URL | User-provided/possibly sensitive | Request/job memory only | App process | Job lifetime/process restart |
| Downloaded media | User-provided content | Per-job temporary directory | Random job capability URL | 1 hour after terminal update by default |
| App source/config | Internal | Git/VPS image | Maintainers/deployer | Version history |

## Trust boundaries and public entry points

| Boundary/endpoint | Untrusted input | Auth | Validation/rate limit |
|---|---|---|---|
| `POST /api/analyze` | URL | None | Strict schema, public DNS/IP check, scheme/port/credential rules, duration/size/extractor limits, per-IP rate limit |
| `POST /api/download` | URL/mode/quality/permission | None | Strict schema, URL revalidation, allowlisted modes/quality grammar, queue and per-IP limits |
| Job/file GET | Capability ID | Random 144-bit-class token | Length, existence, state and canonical parent-path checks |
| External extraction | Remote metadata/media | N/A | Timeouts, retries, no user config/cookies, no file URLs, resource limits |

## Applicable controls

| Control | Implementation | Verification/owner |
|---|---|---|
| AJX-IV-01 | Pydantic `extra=forbid`, URL/format/business limits | Unit tests/AJAYNXT |
| AJX-SSRF-01 | HTTP(S), standard ports, no credentials, DNS public-IP gate; network egress block remains deployment action | Unit tests + VPS review/AJAYNXT |
| AJX-DB-01 | No database or shell command construction; embedded yt-dlp API | Code review/AJAYNXT |
| AJX-UP-01/02 | No user upload; generated files isolated per random job and served as attachment | Path checks/unit review/AJAYNXT |
| AJX-SC-01 | No required secrets; `.env` ignored | Secret scan/AJAYNXT |
| AJX-HD-01/02 | CSP, nosniff, referrer, permissions and frame policies; HSTS opt-in after TLS | Local header check then production TLS check/AJAYNXT |
| AJX-CO-01 | Same-origin default; exact optional CORS list without credentials | Config review/AJAYNXT |
| AJX-API-02 | Body schemas, rate limits, timeouts, max duration/bytes/workers/PIDs/RAM/CPU | Unit and deployment tests/AJAYNXT |
| AJX-ER-01 | User-safe errors; detailed exception only to protected logs without URL | Error-path review/AJAYNXT |
| AJX-LG-02 | Uvicorn access logging disabled; no URL/request body logging | Config review/AJAYNXT |
| AJX-SW-01 | Exact top-level dependency versions and CI tests | Dependency review/AJAYNXT |
| AJX-VP-01/02 | Localhost app binding, Nginx edge, non-root read-only container, dropped capabilities | VPS deployment/AJAYNXT |

Authentication/session/CSRF/database/webhook/payment controls are inapplicable because this version has no identity, cookies, persistent data, webhooks, or payments.

## Release gates

- Local tests, compile check, secret scan, dependency audit, and container build must be recorded in `SECURITY_REPORT.md`.
- Production TLS, DNS, firewall, private-network egress, monitoring, and restore/rollback checks require the actual VPS and domain.
- High/critical findings block release. The DNS-rebinding/redirect SSRF residual requires a network-layer private/link-local egress rule before public production launch.
