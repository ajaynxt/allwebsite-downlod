# Security Report

## Executive status

- Project/version: A TO Z Link Downloader 1.0.0
- Date: 2026-08-17
- Scope: local source, unit behavior, HTTP middleware, dependency set, container configuration and deployment documentation
- Risk class: S2 Business
- Overall statement: local application checks passed and no known vulnerability was reported for `requirements.txt`. Public production approval is conditional on VPS TLS/firewall/egress/monitoring checks; this report does not claim the service is hack-proof.

## Architecture and trust boundaries

An anonymous browser uses same-origin static UI/API. FastAPI validates and rate-limits URLs before yt-dlp/FFmpeg process remote media inside a constrained non-root container. Outputs use random per-job directories and capability URLs, then expire. There is no authentication, database, cookie ingestion, upload, payment or permanent media library.

## Controls implemented

| Control | Status | Evidence/notes |
|---|---|---|
| Strict input/business validation | Pass | Pydantic `extra=forbid`, URL/port/credential checks, output mode/quality/rights rules |
| SSRF preflight | Partial | Private/reserved DNS/IP tests pass; network egress is still required for redirects/DNS rebinding |
| Injection/path handling | Pass in reviewed scope | Embedded yt-dlp API, no user shell/SQL, restricted filename, canonical parent verification |
| Resource controls | Pass in code/config | Rate limits, bounded queue/workers, byte/duration/time/retry limits, container CPU/RAM/PID caps |
| Browser/API headers | Pass locally | CSP, nosniff, referrer, permissions, frame denial, API no-store observed |
| Secrets/log minimization | Pass in reviewed scope | No required secrets, `.env` ignored, access log off, no full URL/request body application logging |
| Supply chain | Pass with follow-up | Exact direct and Linux lock versions, pinned CI actions, audit reported no known vulnerability; image digest/SBOM pending |
| Container hardening | Configured, not executed | Non-root UID, read-only root, dropped capabilities, no-new-privileges, localhost bind |

## Commands and tests

| Command/check | Result | Evidence |
|---|---|---|
| `python -m compileall -q app tests` | Pass | No compile error |
| `python -m unittest discover -s tests -v` | Pass | 9 tests passed |
| `node --check app/static/app.js` | Pass | No syntax error |
| HTML parser smoke check | Pass | Document parsed |
| Local Uvicorn + `curl` | Pass | `/`, `/healthz`, CSP and security headers returned HTTP 200 |
| Private URL API test | Pass | `http://127.0.0.1/...` returned 400 |
| Missing rights test | Pass | Download request returned 422 |
| `pip check` | Pass | No broken requirements |
| `pip-audit -r requirements.txt` | Pass | No known vulnerabilities found |
| Repository triage helper | Reviewed | Two “SQL concat” matches were false positives: yt-dlp format selector strings; project has no SQL/database |
| Credential/private-key pattern scan | Pass | No match in application, tests, CI, or deploy config |
| Docker build | Skipped | Docker executable unavailable in workspace |

## Findings

| ID | Severity | Finding | Fix/status | Owner/next action |
|---|---|---|---|---|
| SEC-01 | Medium | App DNS validation cannot fully prevent extractor redirect/DNS-rebinding access to private networks | Residual | AJAYNXT: add/test VPS/container egress deny rules before public production |
| SEC-02 | Medium | In-memory rate limiting is per process and IP-only | Accepted for one worker | AJAYNXT: add edge/shared limiter before replicas or high traffic |
| SEC-03 | Medium | Third-party media parsers retain zero-day risk | Reduced by container and pins | AJAYNXT: patch routinely; consider dedicated worker sandbox at scale |
| SEC-04 | Low | Capability file URL can be shared by its holder until expiry | Expected design | Keep TLS/no-referrer/short expiry; add accounts only if private library is required |
| SEC-05 | Info | User permission checkbox cannot technically prove copyright rights | Product/legal control | Publish abuse/takedown contact and enforce platform/local-law policy |

## Skipped or inconclusive checks

| Check | Reason | Next action |
|---|---|---|
| Real YouTube/Reel end-to-end extraction | Workspace DNS blocked shell outbound resolution | Test only owned/permitted media on staging VPS |
| Docker runtime/health test | Docker unavailable | Build in CI or VPS and record digest |
| TLS/HSTS/Nginx/firewall/open ports | No authorized production target provided | Complete on actual VPS/domain |
| Automated browser, screen reader, mobile hardware | Browser engine unavailable | Run Playwright/axe plus manual device/assistive-tech check in staging |
| Restore/rollback rehearsal | No deployed environment | Rehearse previous image + config restore before launch |

## Deployment and operations

- HTTPS/TLS: Nginx sample supplied; production validation pending
- Headers/CSP: locally verified; HSTS opt-in defaults off
- Secrets: none required; environment contract supplied
- Firewall/ports: app binds localhost in Compose; VPS verification pending
- Logging/alerts: minimal local logging; external monitoring owner pending
- Backups/restore: source/config need backup; ephemeral media intentionally not backed up
- Rollback: previous image/source/config restoration, with in-flight jobs restarted

## Final release decision

Conditional. Suitable for GitHub handoff and staging. Public production remains blocked until SEC-01 and the unchecked VPS/domain items in `PRODUCTION_CHECKLIST.md` are completed.
