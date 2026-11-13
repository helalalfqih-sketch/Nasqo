#!/usr/bin/env bash
set -euo pipefail
source_dir=/opt/nasqo/odoo
mode="${1:-serve}"
common=(--config=/run/nasqo/odoo.conf --max-cron-threads=0 --workers=0)
case "$mode" in
  serve) exec python3 "$source_dir/odoo-bin" "${common[@]}" ;;
  install|upgrade)
    flag=-i
    [[ "$mode" != upgrade ]] || flag=-u
    exec python3 "$source_dir/odoo-bin" "${common[@]}" --no-http --stop-after-init --without-demo "$flag" nasqo_store ;;
  shell) exec python3 "$source_dir/odoo-bin" shell "${common[@]}" --no-http ;;
  *) echo 'Unsupported M2 runtime command' >&2; exit 2 ;;
esac
