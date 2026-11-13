#!/usr/bin/env bash
# Runs only when the isolated development Postgres volume is first initialized.
set -euo pipefail
: "${NASQO_DEV_DB_PASSWORD:?missing local development role password}"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres \
  -v "nasqo_password=$NASQO_DEV_DB_PASSWORD" <<'SQL'
CREATE ROLE nasqo_dev WITH LOGIN PASSWORD :'nasqo_password' NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
CREATE DATABASE nasqo_dev OWNER nasqo_dev;
SQL
