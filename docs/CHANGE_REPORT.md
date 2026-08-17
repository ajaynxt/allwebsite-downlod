# Change Report

## Added

- Full A TO Z Link Downloader responsive interface
- Strict FastAPI request/response contracts
- Public URL/SSRF preflight validation
- yt-dlp metadata analysis and video/audio quality mapping
- FFmpeg video merge, MP3, and M4A outputs
- Bounded direct-download processing with browser transfer progress and immediate cleanup
- Per-IP single-process rate limits and worker/resource caps
- Security headers, same-origin default, generic production errors, no access URL logging
- Non-root read-only Docker service, Nginx sample, health check, CI, unit tests
- Architecture, UX, security, deployment, rollback, and release documents
- Canonical AJAYNXT domain, sitemap, robots, social card, structured data and Search Console plan
- Direct UPI support, optional Buy Me a Coffee link and owner-editable first-party ad
- Privacy, terms, copyright and supported-sites pages
- Client-side platform keyword autocomplete with short-name aliases and fuzzy typo correction
- User-supplied AJAYNXT panther-head logo used unchanged in every public-page header

## Not added

- Login, database, payment processor, loaded third-party analytics/AdSense scripts, platform cookies, private content access, playlist/channel downloads, live streams, DRM bypass, or permanent user file history

UPI is a direct deep link, not an in-app payment processor. Analytics event hooks and `ads.txt` readiness remain inactive until the owner supplies and approves the relevant provider configuration.

## Migration

New project; no data migration. Deployment creates only an isolated request-time temporary output and deletes it after delivery/failure.
