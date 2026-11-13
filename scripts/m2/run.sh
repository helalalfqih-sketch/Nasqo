#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
command -v docker >/dev/null || { echo 'BLOCKED: Docker CLI is not installed.' >&2; exit 2; }
command -v gpg >/dev/null || { echo 'BLOCKED: GnuPG is not installed.' >&2; exit 2; }
if [[ ! -d vendor/odoo/.git ]]; then
  bash scripts/fetch_upstream.sh
fi
# Only public code is made readable across container UIDs; state remains 0700.
chmod a+rx vendor
chmod -R a+rX vendor/odoo
python3 -B -m tests.isolation.run
