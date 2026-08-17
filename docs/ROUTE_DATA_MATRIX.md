# Route and Data Matrix

| Route | Rendering/data | Input | Output/state | Cache | Main failure states |
|---|---|---|---|---|---|
| `/` | Static HTML/CSS/JS | None | Downloader UI | Static default | Static file unavailable |
| `/healthz` | Server JSON | None | Service status | No sensitive data | Process unavailable |
| `POST /api/analyze` | Server/external extraction | One public HTTP(S) URL | Media metadata and safe format options | `no-store` | Invalid/private URL, unsupported/private media, timeout, rate limit |
| `POST /api/download` | Server validation/direct preparation | URL, output mode, quality ID, rights confirmation | Attachment response; request folder deleted afterward | `no-store` | Validation, permission missing, resource limit, rate limit |

No route accepts uploads, credentials, browser cookies, arbitrary headers, playlists, or user-defined yt-dlp options.
