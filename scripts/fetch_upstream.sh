#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
readarray -t pin < <(python3 - <<'PY'
import json, re
p = json.load(open('upstream.json'))
assert p['repository'] == 'https://github.com/odoo/odoo.git'
assert p['series'] == '19.0'
assert re.fullmatch(r'[0-9a-f]{40}', p['commit'])
print(p['repository']); print(p['commit'])
PY
)
[[ ${#pin[@]} == 2 ]] || { echo 'Invalid upstream pin' >&2; exit 1; }
target=vendor/odoo
if [[ -e "$target" ]]; then
  echo 'vendor/odoo already exists; inspect it manually. Nothing overwritten.' >&2
  exit 1
fi
mkdir -p vendor
git init "$target"
git -C "$target" remote add origin "${pin[0]}"
git -C "$target" fetch --depth=1 origin "${pin[1]}"
git -C "$target" checkout --detach FETCH_HEAD
[[ "$(git -C "$target" rev-parse HEAD)" == "${pin[1]}" ]]
echo 'Pinned source fetched; no dependencies installed and no service started.'
