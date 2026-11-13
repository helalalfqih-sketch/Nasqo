# NASQO Odoo 19 — isolated GitHub Codespaces workspace

This development environment is intentionally separate from NASQO's running GrowERP/Moqui deployment.

## Open in Codespaces
1. Open the repository on branch `chore/odoo19-ecommerce-foundation`.
2. Choose **Code → Codespaces → Create codespace on this branch** (4 cores / 16 GiB recommended if available).
3. The devcontainer installs Docker-in-Docker, fetches the **exact Odoo upstream commit** in `upstream.json`, starts PostgreSQL 16 in its own local Docker network, installs `website_sale` and `nasqo_store`, upgrades the module, rotates the default development admin password, and verifies HTTP routes.
4. Review the Codespace **Ports** tab: port 8069 must remain **Private**, never Public. The Compose mapping also binds only to `127.0.0.1`.
5. Open the forwarded port 8069 to see the test shop. The login is `admin`; the *random development-only password* is saved locally under `.devcontainer/.env` as `NASQO_DEV_ADMIN_PASSWORD`. Do not post it in chat, logs or GitHub.
6. View Codespace setup logs on failure. Run `bash scripts/codespace/bootstrap.sh` again to resume a failed bootstrap, or `bash scripts/codespace/verify.sh` to re-check readiness.

## Safe manual commands
```bash
python3 -B -m unittest discover -s tests -v
bash scripts/codespace/verify.sh
docker compose --env-file .devcontainer/.env -f .devcontainer/compose.yaml ps
docker compose --env-file .devcontainer/.env -f .devcontainer/compose.yaml run --rm -T odoo upgrade
```

## Scope and controls
- Only **disposable development credentials and databases** are used. PostgreSQL is not published outside Docker. Odoo's database role is non-superuser.
- The official dated `odoo:19.0-20261112` image supplies system dependencies; **execution uses the exact pinned Odoo source** mounted under `vendor/odoo`.
- `vendor/odoo`, `.devcontainer/.env`, `.devcontainer/.state`, and database/filestore volumes are not committed.
- Codespaces may sleep, stop or be rebuilt. Restarts attempt to resume services; do **not** rely on it as a persistent server or a backup.
- Do not paste Shopify tokens, NASQO production keys, real customer data, or production database dumps here.
- The CI integration job performs **real install/upgrade and HTTP smoke checks**, not full checkout/payment/tax/RTL/customer migration tests. No production deployment action exists.
- This is a proof of concept: keep the existing NASQO server and Shopify store unchanged.

## Recovery and rollback
If a Codespace fails, inspect errors and rebuild the **disposable Codespace** only after preserving any new code changes in Git. Never delete production data. The development Docker volumes are local to the Codespace and may be lost during rebuild. A GitHub Actions run starts fresh and leaves no lasting database.
