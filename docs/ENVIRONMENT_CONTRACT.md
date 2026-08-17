# Environment Contract

The authoritative variable list and defaults are in `.env.example` and `app/config.py`.

## Required production values

- `APP_ENV=production`
- `ALLOWED_HOSTS` must contain the actual public domain
- `TRUST_PROXY=true` only when the app port is private and Nginx sets `X-Real-IP`
- `TEMP_DIR` must point to the dedicated writable non-persistent `/tmp` workspace

## Security-sensitive toggles

- Keep `ENABLE_HSTS=false` until valid HTTPS is tested. Enable only after confirming intended domain/subdomain behavior.
- `ALLOWED_ORIGINS` should stay empty for same-origin deployment. Add only exact trusted origins when a split frontend is intentionally deployed.
- Resource limits must match VPS RAM/tmpfs capacity; the defaults allow one 1 GiB output and two workers inside a 3 GiB tmpfs and 4 GiB container limit.

## Secrets

This version requires no API keys, account cookies, database password, or service credential. Do not add platform cookies or `.env` to Git. If future private integrations need secrets, inject them at deployment and document rotation/least privilege.
