# Route and Data Matrix

| Route | Rendering/data | Input | Output/state | Cache | Main failure states |
|---|---|---|---|---|---|
| `/` | Static HTML/CSS/JS | None | Downloader UI | Static default | Static file unavailable |
| `/healthz` | Server JSON | None | Service status | No sensitive data | Process unavailable |
| `POST /api/analyze` | Server/external extraction | One public HTTP(S) URL | Media metadata and safe format options | `no-store` | Invalid/private URL, unsupported/private media, timeout, rate limit |
| `POST /api/download` | Server validation/job enqueue | URL, output mode, quality ID, rights confirmation | Capability job ID/status URL | `no-store` | Validation, permission missing, queue full, rate limit |
| `GET /api/jobs/{id}` | In-memory state | Random job ID | Queued/downloading/processing/ready/failed | `no-store` | Unknown/expired ID |
| `GET /api/jobs/{id}/file` | Temporary file | Random job ID | Attachment | `no-store` | Not ready, expired, invalid path |

No route accepts uploads, credentials, browser cookies, arbitrary headers, playlists, or user-defined yt-dlp options.
