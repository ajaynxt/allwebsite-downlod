# Environment Contract

The authoritative variable list and defaults are in `.env.example` and `app/config.py`.

## Required production values

- `APP_ENV=production`
- `ALLOWED_HOSTS` must contain the actual public domain
- `TRUST_PROXY=true` only when the app port is private and Nginx sets `X-Real-IP`
- `DATA_DIR` must be writable by container UID/GID 10001

## Security-sensitive toggles

- Keep `ENABLE_HSTS=false` until valid HTTPS is tested. Enable only after confirming intended domain/subdomain behavior.
- `ALLOWED_ORIGINS` should stay empty for same-origin deployment. Add only exact trusted origins when a split frontend is intentionally deployed.
- Resource limits must match VPS disk/RAM capacity; the defaults allow one 1 GiB output and two workers but the container memory limit is separate.

## Secrets

This version requires no API keys, account cookies, database password, or service credential. Do not add platform cookies or `.env` to Git. If future private integrations need secrets, inject them at deployment and document rotation/least privilege.
