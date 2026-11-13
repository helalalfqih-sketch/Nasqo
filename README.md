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

## Limitations
This setup is not proof of production readiness. Product/cart/checkout, COD/payment, taxes, Arabic/RTL, customer isolation and data migration still need real test cases. Never import NASQO production data or Shopify credentials into Codespaces. Keep Draft PR #1 open until the real integration job passes and the changes are reviewed. NASQO is not an official Odoo product.
