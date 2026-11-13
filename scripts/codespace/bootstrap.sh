#!/usr/bin/env bash
# Idempotent first-boot setup for GitHub Codespaces or a disposable GitHub Actions runner.
set -euo pipefail
cd "$(dirname "$0")/../.."
umask 077
mkdir -p .devcontainer/.state
if [[ ! -f .devcontainer/.env ]]; then
  python3 -B - <<'PY' > .devcontainer/.env
import secrets
for name in ("NASQO_DEV_POSTGRES_PASSWORD", "NASQO_DEV_DB_PASSWORD", "NASQO_DEV_ADMIN_PASSWORD"):
    print(f"{name}={secrets.token_urlsafe(32)}")
PY
fi
chmod 600 .devcontainer/.env

dc() {
  docker compose --env-file .devcontainer/.env -f .devcontainer/compose.yaml "$@"
}

echo "NASQO: validating source and safety checks"
python3 -B -m unittest discover -s tests -v
if [[ -f .devcontainer/.state/bootstrapped ]]; then
  echo "NASQO: existing isolated development environment; resuming"
  bash scripts/codespace/resume.sh
  bash scripts/codespace/verify.sh
  exit 0
fi

if [[ -d vendor/odoo/.git ]]; then
  expected="$(python3 -B -c 'import json; print(json.load(open("upstream.json"))["commit"])')"
  actual="$(git -C vendor/odoo rev-parse HEAD)"
  [[ "$actual" == "$expected" ]] || { echo "Local Odoo checkout differs from pinned commit" >&2; exit 1; }
else
  bash scripts/fetch_upstream.sh
fi

command -v docker >/dev/null || { echo "Docker is unavailable in this development container" >&2; exit 1; }
for _ in $(seq 1 40); do
  docker info >/dev/null 2>&1 && break
  sleep 2
done
docker info >/dev/null

echo "NASQO: starting isolated PostgreSQL"
dc up -d db
ready=0
for _ in $(seq 1 60); do
  if [[ "$(dc exec -T db psql -U postgres -d postgres -Atqc "SELECT 1 FROM pg_roles WHERE rolname='nasqo_dev'" 2>/dev/null || true)" == "1" ]]; then
    ready=1
    break
  fi
  sleep 2
done
[[ "$ready" == 1 ]] || { echo "Development database role initialization failed" >&2; exit 1; }

echo "NASQO: real Odoo 19 module installation (website_sale + nasqo_store)"
dc run --rm -T odoo install
echo "NASQO: real Odoo 19 module upgrade"
dc run --rm -T odoo upgrade

echo "NASQO: replacing the default development administrator password"
dc run --rm -T odoo shell <<'PY'
import os
admin = env.ref('base.user_admin')
admin.write({'password': os.environ['NASQO_DEV_ADMIN_PASSWORD']})
env.cr.commit()
PY

echo "NASQO: starting the development storefront"
dc up -d odoo
bash scripts/codespace/verify.sh
touch .devcontainer/.state/bootstrapped
echo "NASQO: Odoo 19 development tests passed; port 8069 remains private by default."
