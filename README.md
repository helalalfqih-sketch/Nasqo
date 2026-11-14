# نسقو برو — NASQO PRO on Odoo Community 19

Development foundation, **not production-ready software**. This public repository is separate from the existing NASQO GrowERP/Moqui system and does not contain customer data, production credentials or automatic deployments.

## NASQO PRO identity
The presentation addons now use **نسقو برو / NASQO PRO** for the storefront,
login, administration, generic dialogs, PWA, and notification templates. The
2026-11-14 update was tested on an independent pilot before the requested live
branding update. See [the implementation and verification record](docs/NASQO_PRO_BRANDING.md).
This branch also captures the previously server-only presentation addons for
review. Component licenses, original authorship, technical identifiers, and
standard access checks remain intact. There is no automatic deployment workflow.

## Isolated Codespaces integration
Open the [development branch](https://github.com/helalalfqih-sketch/Nasqo/tree/chore/odoo19-ecommerce-foundation), then **Code → Codespaces → Create codespace on this branch**. The devcontainer uses Docker-in-Docker, a separate PostgreSQL database and the exact Odoo source commit from `upstream.json`, running inside the official dated Odoo 19 image. It installs `website_sale` and `nasqo_store`, performs an upgrade, sets a random development admin password and verifies the login and shop routes.

Port **8069 must remain Private** in the Codespaces Ports tab. See [docs/CODESPACES.md](docs/CODESPACES.md) for the setup, tests, credentials and recovery guidance.

## Source layout
- `addons/nasqo_store`: minimal installable custom module depending on Community `website_sale`; no checkout/payment customization yet.
- `addons/nasqo_backend_branding`, `nasqo_website_branding`, `nasqo_storefront`, and `nasqo_apps_identity`: administration and public identity inherited from standard Community views.
- `addons/nasqo_waha_live_view`, `nasqo_waha_qr_preview`, and `nasqo_whatsapp_center`: existing administration integrations captured for review; this change updates their display names only.
- `scripts/branding/`: the HTTP, JavaScript contract, and QWeb rendering checks used for the branding update. Run only against the intended environment.
- `vendor/odoo`: ignored locally fetched Odoo 19 source; do not edit core.
- `upstream.json` and `scripts/fetch_upstream.sh`: pinned source revision.
- `.devcontainer/`: Codespaces configuration and isolated Postgres/Odoo Compose services.
- `scripts/codespace/`: repeatable install, upgrade, smoke tests and resume scripts.
- `tests/`: static safety tests; `.github/workflows/odoo-integration.yml` adds live Odoo/Postgres integration tests.
- `docs/UPDATES.md`: review, update, backup and rollback policy.

## Limitations
This setup is not proof of production readiness. Product/cart/checkout, COD/payment, taxes, Arabic/RTL, customer isolation and data migration still need real test cases. Never import NASQO production data or Shopify credentials into Codespaces. Keep Draft PR #1 open until the real integration job passes and the changes are reviewed. NASQO is not an official Odoo product.
