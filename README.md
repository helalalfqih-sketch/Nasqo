# NASQO — Odoo Community 19 ecommerce

Development foundation, **not production-ready software**. This public repository is separate from the existing NASQO GrowERP/Moqui system and does not contain customer data, production credentials or automatic deployments.

## Isolated Codespaces integration
Open the [development branch](https://github.com/helalalfqih-sketch/Nasqo/tree/chore/odoo19-ecommerce-foundation), then **Code → Codespaces → Create codespace on this branch**. The devcontainer uses Docker-in-Docker, a separate PostgreSQL database and the exact Odoo source commit from `upstream.json`, running inside the official dated Odoo 19 image. It installs `website_sale` and `nasqo_store`, performs an upgrade, sets a random development admin password and verifies the login and shop routes.

Port **8069 must remain Private** in the Codespaces Ports tab. See [docs/CODESPACES.md](docs/CODESPACES.md) for the setup, tests, credentials and recovery guidance.

## Source layout
- `addons/nasqo_store`: minimal installable custom module depending on Community `website_sale`; no checkout/payment customization yet.
- `vendor/odoo`: ignored locally fetched Odoo 19 source; do not edit core.
- `upstream.json` and `scripts/fetch_upstream.sh`: pinned source revision.
- `.devcontainer/`: Codespaces configuration and isolated Postgres/Odoo Compose services.
- `scripts/codespace/`: repeatable install, upgrade, smoke tests and resume scripts.
- `tests/`: static safety tests; `.github/workflows/odoo-integration.yml` adds live Odoo/Postgres integration tests.
- `docs/UPDATES.md`: review, update, backup and rollback policy.

## M0–M2 tenant isolation pilot

The next development branch adds a **local operator CLI**, a persistent idempotent
registry, separate Odoo/PostgreSQL/filestore resources per synthetic tenant, and an
allowlisted loopback gateway. Encrypted offline backups restore only into a fresh
isolated project for the same tenant. There is no public signup or billing API.

Read [the M0 review](docs/M0_REVIEW.md), [M2 runbook](docs/M2_RUNBOOK.md),
[acceptance coverage](docs/TEST_PLAN.md), and [M3–M8 backlog](docs/BACKLOG.md).
Run `bash scripts/m2/run.sh` on a disposable Docker host to execute actual
installation, HTTP, data isolation, failure recovery and backup/restore checks.
The `M2 tenant isolation and restore` workflow runs the same checks on a fresh
GitHub runner. See `AI_HANDOFF.md` for the last **observed**, not assumed, result.

**Verified pilot:** runtime commit `175888a` passed 19 unit tests and all 11
reported M0/M1/M2 acceptance groups, including two actual stores and encrypted
restore. [CI evidence](https://github.com/helalalfqih-sketch/Nasqo/actions/runs/43479599787)
and the [recorded report](docs/validation/m2-results-175888a.json) contain the details.

## Limitations
This setup is not proof of production readiness. The M2 operator pilot has isolation
and restore evidence; merchant lifecycle, product/cart/checkout, COD/payment, taxes,
Arabic/RTL, production security and data migration still need their own tests.
Never import NASQO production data or Shopify credentials into Codespaces.
Keep Draft PRs #1 and #3 open for review. NASQO is not an official Odoo product.
