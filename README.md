# NASQO — Odoo Community 19 ecommerce

Development foundation, **not production-ready software**. This public repository is separate from the existing NASQO GrowERP/Moqui system and does not contain customer data, production credentials or automatic deployments.

## Isolated Codespaces integration
Open the [development branch](https://github.com/helalalfqih-sketch/Nasqo/tree/fix/m2-runtime-verification), then **Code → Codespaces → Create codespace on this branch**. The devcontainer uses Docker-in-Docker, a separate PostgreSQL database and the exact Odoo source commit from `upstream.json`, running inside the official dated Odoo 19 image. It installs `website_sale` and `nasqo_store`, performs an upgrade, sets a random development admin password and verifies the login and shop routes.

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

Follow-up review: [Draft PR #4](https://github.com/helalalfqih-sketch/Nasqo/pull/4)
targets [Draft PR #3](https://github.com/helalalfqih-sketch/Nasqo/pull/3). It adds
actual Odoo database-selector regression checks, strict Host/header handling,
source/secret/image security gates and container-log secret checks. Foundation
Odoo mounts only public source and scripts, so it cannot read the M2 registry.
Fresh M1/M2 environments build the reviewed PostgreSQL derivative and use the
updated Nginx image. M1 v2 has new volume names and refuses to bootstrap an old
v1 workspace; existing database volumes are preserved. All four workflows passed on runtime commit `f1ae638`: 21 unit tests, actual M1,
two-store M2/restore and security scans. See [runtime evidence](docs/RUNTIME_SELECTOR_FIX.md).

**Verified follow-up:** [M2 CI evidence](https://github.com/helalalfqih-sketch/Nasqo/actions/runs/43483024980)
and the [recorded report](docs/validation/m2-results-f1ae638.json) contain all 11
passing pilot groups, runtime image IDs and exact code provenance. See the
[security evidence](docs/validation/security-f1ae638.json) and
[detailed M3–M8 plan](docs/PHASE_PLAN_M3_M8.md). No public merchant service was created.

## Actual UI captures

The visual-evidence follow-up captures the anonymous Alpha/Beta storefronts,
blank login form and Alpha at a mobile-width viewport after M2 passes on a fresh
runner. Download `nasqo-m2-visual-evidence` from its successful M2 workflow run.
These are the existing Odoo foundation and synthetic test products, not a custom
NASQO theme or a persistent live store. Only PNGs and provenance are uploaded;
browser profiles, DOM, credentials, databases and backups are excluded.
See [the capture procedure](docs/VISUAL_EVIDENCE.md) for validation and limits.

## Limitations
This setup is not proof of production readiness. The M2 operator pilot has isolation
and restore evidence; merchant lifecycle, product/cart/checkout, COD/payment, taxes,
Arabic/RTL, production security and data migration still need their own tests.
Never import NASQO production data or Shopify credentials into Codespaces.
Keep Draft PRs #1, #3 and #4 open for review. NASQO is not an official Odoo product.
