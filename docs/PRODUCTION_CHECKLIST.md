# Production Checklist

## Application evidence

- [x] Compile check passed
- [x] Unit tests passed (9/9)
- [x] Dependency audit reviewed with no known vulnerability reported for direct requirements
- [x] Secret pattern scan reviewed; no credential/private-key match
- [ ] Docker image built
- [x] Local health/API/static/header smoke tests passed

## VPS/domain actions

- [ ] Supported VPS OS patched; named sudo user and SSH keys configured
- [ ] Firewall default-deny inbound; only 22 (restricted), 80, and 443 exposed
- [ ] Private/link-local/cloud-metadata outbound destinations blocked for the app/container
- [ ] Real domain added to `ALLOWED_HOSTS`
- [ ] Nginx config tested; app remains bound to localhost
- [ ] Valid HTTPS certificate and renewal tested
- [ ] HSTS enabled only after HTTPS/domain verification
- [ ] DNS/registrar, GitHub and VPS accounts protected with MFA
- [ ] Disk/CPU/RAM/certificate/service alerts have a named owner
- [ ] Abuse/takedown policy and contact are published before public promotion
- [ ] Restore/rollback rehearsal completed for repository, `.env`, Nginx and previous image

## Functional launch tests

- [ ] One owned/permitted YouTube video: analyze, quality select, ready file
- [ ] One owned/permitted public Reel where platform allows extraction
- [ ] MP3 and M4A outputs play correctly
- [ ] Invalid/private/playlist/live links fail safely
- [ ] Mobile narrow viewport, keyboard path, 200% zoom and screen reader status tested
- [ ] File disappears after configured expiry
- [ ] Rate limits and queue-full states return actionable errors
