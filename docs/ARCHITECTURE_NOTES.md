# Architecture Notes

## Decision

Use a modular Python/FastAPI monolith serving a static same-origin frontend. Run one application process with a bounded thread pool for media jobs. Package the system as a non-root Docker container behind Nginx.

## Why

- Media extraction and FFmpeg require server execution; GitHub Pages cannot provide it.
- The yt-dlp Python API avoids constructing shell commands from untrusted input.
- Same-origin UI/API avoids unnecessary CORS exposure.
- A single deployable keeps the first operational version maintainable.

## Components

```text
Browser
  -> Nginx/TLS (public 80/443)
    -> FastAPI (localhost/container port)
      -> URL validation + rate limit
      -> yt-dlp metadata/media requests
      -> FFmpeg merge/audio conversion
      -> temporary Docker volume
```

## Boundaries

- `models.py`: strict request/response contracts
- `security.py`: public URL validation and SSRF preflight
- `services/downloader.py`: yt-dlp/FFmpeg adapter and format mapping
- `services/jobs.py`: bounded background execution, progress, capability IDs, expiry
- `services/rate_limit.py`: single-process sliding window
- `main.py`: HTTP routes, middleware, errors, static delivery

## Rendering and persistence

The landing page is static and progressively enhanced with small client JavaScript. API responses are dynamic and `no-store`. Job state is intentionally ephemeral in memory; output files use a temporary volume and expire. There is no database, authentication, or permanent media library.

## Scale boundary

Before multiple replicas, replace in-memory jobs/rate limits with a shared queue and shared rate-limit store, move outputs to short-lived object storage, and add explicit worker isolation. Do not simply increase Uvicorn workers because each process would have separate job state.

## Rollback

Keep the previous image tag. Roll back Nginx upstream/image, recreate the container, and accept that in-flight ephemeral jobs must be restarted by users. No database migration is involved.
