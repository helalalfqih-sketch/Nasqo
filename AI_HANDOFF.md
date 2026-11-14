# NASQO Odoo Community 19 — handoff (2026-11-13)

## Update: NASQO PRO identity, 2026-11-14

The user explicitly requested replacement of Odoo-facing identity with
**نسقو برو**. The separately requested live branding work is recorded in
[docs/NASQO_PRO_BRANDING.md](docs/NASQO_PRO_BRANDING.md); the older foundation
notes below remain historical. Do not infer SaaS, RBAC, or checkout readiness
from this presentation update.

- Review branch: `feat/nasqo-pro-identity`, based on `ca09ad2` from the foundation branch.
- Published baseline commit `519a65b` captures seven existing server presentation addons;
  the following commit contains the PRO delta, verification scripts and docs.
- All seven addon upgrades passed on an independent pilot and on the requested
  live site. Live verification: 35 authenticated HTTP checks, 9 public tests,
  JavaScript title/dialog contracts, and four rendered notification/report layouts.
- A consistent local database/filestore backup preceded the update. SHA checks
  passed; no restore test was performed in this branding task.
- Hash comparison of 12 business tables passed. Only the system bot contact was
  intentionally excluded because its display name/icon were updated. Company,
  customer, product, order, accounting and stock data were preserved.
- Preserve all translations of customized website views, including pending
  `_en_US` entries. Plain per-language `arch_db.write` synchronizes structure and
  can discard custom markup; the live footer was repaired from its guarded
  snapshot through the ORM translation cache, with `clear_cache('templates')`.
  The explicit Odoo Facebook promotional widget was removed; social links remain.
- `web.web_app_name`, the existing website display name and system bot identity
  are environment settings, not generalized automatic tenant migrations.
- Logs, database snapshots, configurations, credentials and customer data stay
  off Git. PR #1 remains unmerged. Follow up with the published review status.

Next: review the branding diff and manually inspect authenticated business
screens with the user's intended roles. Real PDF output and full responsive
end-to-end tests remain separate; no message was sent and no order was created.

## Scope
Isolated proof of concept on GitHub branch `chore/odoo19-ecommerce-foundation` and Draft PR #1. Do not merge automatically or touch the legacy NASQO VPS.

## Architecture
- GitHub Codespace on `mcr.microsoft.com/devcontainers/base:ubuntu-24.04` with Docker-in-Docker.
- Separate Docker Compose project `nasqo-odoo19-development`.
- Postgres 16 with private storage and a **non-superuser** role `nasqo_dev`.
- Odoo dependencies supplied by official date-tagged `odoo:19.0-20261112` image.
- Application starts with the exact Odoo source SHA recorded in `upstream.json`, fetched to ignored `vendor/odoo`.
- First two CI integration runs could not read vendor/odoo/odoo-bin inside the non-root Odoo container. The repo was fetched under umask 077, which protects secrets but also restricted public Git checkout to the host UID. The isolated public checkout and its parent vendor/ directory now get read/execute permissions (chmod a+rx vendor and chmod -R a+rX vendor/odoo) after cloning; .env retains 0600. GitHub Actions output identified vendor as 0700. Await CI verification.
- The local `nasqo_store` module depends on Odoo Community `website_sale`.
- Port 8069 binds to loopback. Codespaces port visibility must remain Private.
- Passwords are fresh random dev-only secrets stored in ignored `.devcontainer/.env` (mode 0600).

## Reproducible validation
- `python3 -B -m unittest discover -s tests -v` — static configuration checks.
- `bash -n scripts/codespace/*.sh .devcontainer/db-init/*.sh scripts/fetch_upstream.sh` — shell syntax.
- `bash scripts/codespace/bootstrap.sh` — real PostgreSQL role initialization, Odoo module install/upgrade, admin password rotation, and HTTP login/shop smoke checks.
- `bash scripts/codespace/verify.sh` — read-only module state/HTTP checks.

## Status and remaining blockers
- GitHub Actions on commit a99a9146 **PASS**: real Odoo 19 installation of website_sale/nasqo_store and module upgrade, plus DB module state checks. First HTTP request hit a transient connection reset immediately after service start; verify.sh now retries temporary socket failures. Await a full green integration run.
- Module has no custom storefront logic yet.
- E2E product/cart/checkout/COD, Arabic/RTL, roles, invoicing, migration and rollback still require separate tests.
- No Codespace or deployment is persistent. Never bring live customer or production secrets into this repo.
- Keep Draft PR #1 open for review.
