#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
if [[ ! -f .devcontainer/.state/bootstrapped || ! -f .devcontainer/.env || ! -d vendor/odoo/.git ]]; then
  echo "NASQO: bootstrap has not completed; no service started."
  exit 0
fi
if ! docker info >/dev/null 2>&1; then
  echo "NASQO: Docker not ready; run scripts/codespace/bootstrap.sh when available."
  exit 0
fi
docker compose --env-file .devcontainer/.env -f .devcontainer/compose.yaml up -d
echo "NASQO: local development Odoo/PostgreSQL containers resumed."
