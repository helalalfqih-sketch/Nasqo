# NASQO Odoo Community 19 — handoff (2026-11-13)

## Scope
Isolated proof of concept on GitHub branch `chore/odoo19-ecommerce-foundation` and Draft PR #1. Do not merge automatically or touch the legacy NASQO VPS.

## Architecture
- GitHub Codespace on `mcr.microsoft.com/devcontainers/base:ubuntu-24.04` with Docker-in-Docker.
- Separate Docker Compose project `nasqo-odoo19-development`.
- Postgres 16 with private storage and a **non-superuser** role `nasqo_dev`.
- Odoo dependencies supplied by official date-tagged `odoo:19.0-20261112` image.
- Application starts with the exact Odoo source SHA recorded in `upstream.json`, fetched to ignored `vendor/odoo`.
- The local `nasqo_store` module depends on Odoo Community `website_sale`.
- Port 8069 binds to loopback. Codespaces port visibility must remain Private.
- Passwords are fresh random dev-only secrets stored in ignored `.devcontainer/.env` (mode 0600).

## Reproducible validation
- `python3 -B -m unittest discover -s tests -v` — static configuration checks.
- `bash -n scripts/codespace/*.sh .devcontainer/db-init/*.sh scripts/fetch_upstream.sh` — shell syntax.
- `bash scripts/codespace/bootstrap.sh` — real PostgreSQL role initialization, Odoo module install/upgrade, admin password rotation, and HTTP login/shop smoke checks.
- `bash scripts/codespace/verify.sh` — read-only module state/HTTP checks.

## Status and remaining blockers
- Code is staged for GitHub Action integration; do not claim runtime PASS until GitHub CI/Codespace confirms.
- Module has no custom storefront logic yet.
- E2E product/cart/checkout/COD, Arabic/RTL, roles, invoicing, migration and rollback still require separate tests.
- No Codespace or deployment is persistent. Never bring live customer or production secrets into this repo.
- Keep Draft PR #1 open for review.
