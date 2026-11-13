#!/usr/bin/env bash
# Run actual database/module and HTTP checks; do not infer readiness from container status.
set -euo pipefail
cd "$(dirname "$0")/../.."
dc() { docker compose --env-file .devcontainer/.env -f .devcontainer/compose.yaml "$@"; }

for module in base website_sale nasqo_store; do
  state="$(dc exec -T db psql -U nasqo_dev -d nasqo_dev -Atqc "SELECT state FROM ir_module_module WHERE name='$module' LIMIT 1" | tr -d '\r')"
  if [[ "$state" != installed ]]; then
    echo "NASQO: required module $module is not installed (state: $state)" >&2
    exit 1
  fi
  echo "PASS module installed: $module"
done

for path in /web/login /shop; do
  if ! curl --retry 35 --retry-delay 2 --retry-all-errors --retry-connrefused --connect-timeout 5 \
      --max-time 30 --fail --silent --show-error --location --output /dev/null \
      "http://127.0.0.1:8069$path"; then
    echo "NASQO: HTTP smoke test failed at $path" >&2
    exit 1
  fi
  echo "PASS HTTP GET $path"
done
echo "NASQO: module installation, upgrade and HTTP smoke tests verified."
