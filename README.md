# NASQO — Odoo Community 19 ecommerce

Development foundation, not production-ready software. No production connection or automatic deployment is configured.

## Layout
- `addons/nasqo_store`: small installable custom module depending on Community `website_sale`.
- `vendor/odoo`: locally fetched, ignored upstream source. Never edit Odoo core for custom features.
- `upstream.json`: reviewed exact upstream commit. No floating branch in builds.
- `config/odoo.dev.conf.example`: local-only example; actual credentials stay outside Git.
- `scripts/fetch_upstream.sh`: fetches the pinned source only, does not install packages or launch services.
- `tests/test_foundation.py`: dependency-free static checks, not Odoo integration tests.
- `docs/UPDATES.md`: review, update and rollback gates.

## First development setup
1. Run `python3 -m unittest discover -s tests -v`.
2. Review `upstream.json`, then run `bash scripts/fetch_upstream.sh`.
3. In an isolated development environment, install Odoo's requirements from its checked-out `requirements.txt` following the Odoo 19 source-install documentation. Use a separate PostgreSQL development role and database, never production credentials.
4. Copy the example config to ignored `config/odoo.dev.conf`, set absolute addon paths and local connection settings. The database role should not be a superuser. Keep outbound email/payment integrations disabled.
5. Only after reviewing that config, initialize the module with `python3 vendor/odoo/odoo-bin -c config/odoo.dev.conf -d nasqo_dev -i nasqo_store --without-demo=all --stop-after-init`.
6. Test upgrades using `-u nasqo_store --stop-after-init` against a disposable development database. Do not use `-u all` against production.

The module introduces no checkout/payment behavior yet. Functional checkout, Arabic/RTL, access rules, taxes, delivery, email and payment sandbox tests remain required. See `docs/UPDATES.md`.

Odoo retains its own upstream license and notices. Review licenses of every third-party add-on before use. NASQO is not an official Odoo product.
