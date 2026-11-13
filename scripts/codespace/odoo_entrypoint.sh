#!/usr/bin/env bash
# Start the exact pinned upstream Odoo source, not the image's possibly newer Odoo package.
set -euo pipefail
source_dir=/workspace/vendor/odoo
test -f "$source_dir/odoo-bin" || { echo "Pinned Odoo source not found; run scripts/fetch_upstream.sh" >&2; exit 2; }
mode="${1:-serve}"
shift || true
common=(
  "--database=nasqo_dev"
  "--db-filter=^nasqo_dev$"
  "--addons-path=$source_dir/addons,/workspace/addons"
  "--data-dir=/var/lib/odoo"
  "--no-database-list"
  "--max-cron-threads=0"
  "--workers=0"
)
case "$mode" in
  serve)
    exec python3 "$source_dir/odoo-bin" "${common[@]}" \
      "--http-interface=0.0.0.0" "--http-port=8069" "$@"
    ;;
  install)
    exec python3 "$source_dir/odoo-bin" "${common[@]}" \
      "--no-http" "--stop-after-init" "--without-demo" "-i" "nasqo_store" "$@"
    ;;
  upgrade)
    exec python3 "$source_dir/odoo-bin" "${common[@]}" \
      "--no-http" "--stop-after-init" "--without-demo" "-u" "nasqo_store" "$@"
    ;;
  shell)
    exec python3 "$source_dir/odoo-bin" shell "${common[@]}" "$@"
    ;;
  *)
    echo "Unsupported development command (use serve/install/upgrade/shell)" >&2
    exit 2
    ;;
esac
