#!/usr/bin/env bash
# Only on a new, isolated M2 PostgreSQL volume. Never run against an existing server.
set -euo pipefail
psql -v ON_ERROR_STOP=1 -U postgres -d postgres \
  -v "role=$NASQO_DB_NAME" -v "password=$NASQO_DB_PASSWORD" <<'SQL'
CREATE ROLE :"role" WITH LOGIN PASSWORD :'password' NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
CREATE DATABASE :"role" OWNER postgres;
REVOKE ALL ON DATABASE :"role" FROM PUBLIC;
GRANT CONNECT, TEMPORARY ON DATABASE :"role" TO :"role";
REVOKE CONNECT ON DATABASE postgres FROM PUBLIC;
REVOKE CONNECT ON DATABASE template1 FROM PUBLIC;
SQL
psql -v ON_ERROR_STOP=1 -U postgres -d "$NASQO_DB_NAME" -v "role=$NASQO_DB_NAME" <<'SQL'
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE, CREATE ON SCHEMA public TO :"role";
SQL
