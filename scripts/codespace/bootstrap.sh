#!/usr/bin/env bash
# Idempotent first-boot setup for GitHub Codespaces or a disposable GitHub Actions runner.
set -euo pipefail
cd "$(dirname "$0")/../.."
umask 077
mkdir -p .devcontainer/.state
if [[ -f .devcontainer/.state/bootstrapped && ! -f .devcontainer/.state/bootstrapped-v2 ]]; then
  echo "BLOCKED: preserve the existing v1 development workspace; use a fresh Codespace for v2. No existing database volume will be upgraded." >&2
  exit 2
fi
if [[ ! -f .devcontainer/.env ]]; then
  python3 -B - <<'PY' > .devcontainer/.env
import secrets
for name in ("NASQO_DEV_POSTGRES_PASSWORD", "NASQO_DEV_DB_PASSWORD", "NASQO_DEV_ADMIN_PASSWORD"):
    print(f"{name}={secrets.token_urlsafe(32)}")
PY
fi
# Resolve a canonical absolute path for the current Codespace/runner before Docker mounts it.
# Refresh only this local setting if the workspace was moved; preserve dev credentials.
python3 -B - <<'PY'
from pathlib import Path
import os
p = Path('.devcontainer/.env')
lines = [s for s in p.read_text().splitlines() if not s.startswith('NASQO_REPO_ROOT=')]
lines.append('NASQO_REPO_ROOT=' + os.getcwd())
p.write_text('\n'.join(lines) + '\n')
PY
chmod 600 .devcontainer/.env

dc() {
  docker compose --env-file .devcontainer/.env -f .devcontainer/compose.yaml "$@"
}

echo "NASQO: validating source and safety checks"
python3 -B -m unittest discover -s tests -v
if [[ -f .devcontainer/.state/bootstrapped-v2 ]]; then
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

# Public, pinned Odoo source is mounted read-only in a container running as user "odoo".
# The bootstrap umask protects local secrets, but Git must be readable across UIDs.
# Only relax permissions inside the disposable public vendor checkout, never .env.
chmod a+rx vendor
chmod -R a+rX vendor/odoo

command -v docker >/dev/null || { echo "Docker is unavailable in this development container" >&2; exit 1; }
for _ in $(seq 1 40); do
  docker info >/dev/null 2>&1 && break
  sleep 2
done
docker info >/dev/null

echo "NASQO: starting isolated PostgreSQL"
dc build --pull db
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

echo "NASQO: verifying the pinned source is visible inside Docker"
dc run --rm -T --no-deps --entrypoint sh odoo -c 'test -r /workspace/vendor/odoo/odoo-bin' || {
  dc run --rm -T --no-deps --entrypoint sh odoo -c 'for f in /workspace /workspace/vendor /workspace/vendor/odoo /workspace/vendor/odoo/odoo-bin; do ls -ld "$f" 2>&1; done' || true
  echo "NASQO: bind mount error; pinned upstream source is not visible" >&2
  exit 1
}

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
touch .devcontainer/.state/bootstrapped-v2
echo "NASQO: Odoo 19 development tests passed; port 8069 remains private by default."
