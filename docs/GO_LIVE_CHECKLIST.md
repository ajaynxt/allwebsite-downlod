# Secure Go-Live Checklist

## Scope and access

- [x] S2 risk class and architecture recorded
- [x] Threat model completed
- [x] No default accounts/passwords; authentication is not present
- [x] Strict server-side request validation, canonical temp-path checks and cleanup implemented
- [x] Production owner and incident contact published

## Application and supply chain

- [x] SSRF preflight, resource caps, generic errors, direct attachment and immediate cleanup implemented
- [x] Exact top-level dependency versions and pinned CI action revisions present
- [ ] Transitive lock/SBOM generated and reviewed
- [ ] Production artifact digest recorded
- [ ] Critical/high dependency findings fixed or accepted with owner/expiry

## Browser, API and transport

- [x] CSP, nosniff, frame, referrer and permissions policies implemented
- [x] Same-origin default and strict optional CORS allowlist
- [x] Per-IP action rate limits and worker bounds
- [ ] Production HTTPS/TLS/certificate/redirect checked
- [ ] HSTS decision checked on real domain

## Infrastructure and recovery

- [x] Container configured non-root, read-only, capability-dropped, PID/RAM/CPU limited
- [x] App port bound to localhost in Compose
- [ ] VPS firewall, SSH, patching, Nginx, DNS and private-network egress verified
- [ ] Monitoring/alerts tested
- [ ] Source/config rollback and restore rehearsal recorded

Unchecked items require the actual GitHub/VPS/domain environment and block an evidence-based public production approval.
