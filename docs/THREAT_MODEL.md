# Threat Model

## Scope

A TO Z Link Downloader 1.0.0, public UI/API, outbound extractor, media processing, temporary storage, container and Nginx deployment. Third-party platform internals and the user's legal rights are outside technical control.

## Roles

| Role | Intended permissions | High-impact action |
|---|---|---|
| Anonymous visitor | Analyze one public URL and request one direct permitted attachment | Consume outbound bandwidth/CPU/temporary disk |
| Operator | Deploy/configure/update/observe service | Change limits, image, domain, logs, or network controls |
| Remote media host | Return metadata/media to extractor | Supply malformed, oversized, redirected, or hostile content |

## Components and trust boundaries

```text
[Anonymous browser] -> [Nginx/TLS] -> [FastAPI validation/rate limit]
                                      -> [yt-dlp/FFmpeg container]
                                      -> [isolated request /tmp]
                                      -> [direct attachment + cleanup]
                                      -> [public internet media host]
[GitHub/CI] -> [container image] -> [VPS]
```

## Abuse cases

| ID | Attacker goal | Impact/likelihood | Controls | Residual risk |
|---|---|---|---|---|
| T1 | Use URL input to reach localhost, metadata service, or private network | High/possible | Scheme/host/credentials/port rules, DNS public-IP validation | Extractor redirects/DNS rebinding require VPS egress deny rules |
| T2 | Exhaust CPU, RAM, disk, bandwidth, or workers | High/likely on public launch | Per-IP limits, duration/size/timeouts, bounded workers, tmpfs, container RAM/CPU/PID limits, immediate cleanup | Distributed abuse needs edge/shared rate limiting |
| T3 | Exploit malformed media in yt-dlp/FFmpeg | High/possible | Maintained pinned dependencies, non-root/read-only container, dropped caps, no host mounts, updates | Parser zero-days remain possible; stronger worker sandbox is a scale-up action |
| T4 | Escape request directory/path traversal | High/unlikely | Server-owned template, restricted filenames, random directory, canonical parent check, attachment response | Third-party library regression |
| T5 | Retrieve another user's prepared file | Medium/unlikely | No file/status GET route or capability URL; attachment exists only in active response | Infrastructure-level compromise remains out of scope |
| T6 | Inject script through title/creator/thumbnail | High/possible | DOM `textContent`, no raw HTML, CSP, validated external thumbnail URL | Remote image still reveals requester IP to image host |
| T7 | Trick service into private/login/DRM access | Medium/possible | No cookie input/storage, no credentials in URLs, public-only copy, no DRM mechanism | Public endpoints can still change access behavior |
| T8 | Supply malicious dependency/build | High/possible | Exact top-level pins, pinned CI actions, read-only CI token, container build/test | Transitive lock/SBOM and image digest pinning remain improvements |
| T9 | Abuse service for copyright infringement | Legal/business/likely | Explicit ownership checkbox, responsible-use copy, no private/DRM features | Attestation cannot prove rights; operator needs policy/takedown process |

## Decisions

- No authentication in version 1 because there is no personal library or private data; public abuse is controlled through limits and infrastructure.
- No user cookies are accepted because they would introduce account/secret handling and private-content access.
- Temporary outputs are isolated per active request and deleted after delivery/failure; there is no backup or Cloud Storage for link/media data.
- Best quality preserves available streams/merges where possible; the product does not claim invented resolution.
