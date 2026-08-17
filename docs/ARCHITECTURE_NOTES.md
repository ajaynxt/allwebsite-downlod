# Architecture Notes

## Decision

Use a modular Python/FastAPI monolith serving a static same-origin frontend. Run one application process with bounded direct-download preparation. Package the system as a non-root Docker container behind Nginx.

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
      -> isolated request folder in non-persistent /tmp
      -> attachment response to browser
      -> immediate folder deletion
```

## Boundaries

- `models.py`: strict request/response contracts
- `security.py`: public URL validation and SSRF preflight
- `services/downloader.py`: yt-dlp/FFmpeg adapter and format mapping
- `services/rate_limit.py`: single-process sliding window
- `main.py`: direct attachment response, immediate cleanup, middleware, errors, static delivery

## Rendering and persistence

The landing page is static and progressively enhanced with small client JavaScript. API responses are dynamic and `no-store`. A download is prepared once in an isolated `/tmp` request folder, sent as an attachment, and removed by a response background task. There is no database, Cloud Storage, job history, authentication, or permanent media library.

## Scale boundary

Before multiple replicas, replace the in-memory rate limiter with a shared edge/rate-limit store and add explicit worker isolation. Direct requests remain stateless and must not be moved into permanent object storage.

## Rollback

Keep the previous image tag. Roll back Nginx upstream/image and recreate the container. In-flight requests must be restarted by users; no database migration is involved.
