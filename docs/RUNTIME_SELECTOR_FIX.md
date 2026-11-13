# Follow-up: non-owner database selection (2026-11-13)

The concurrent M0–M2 implementation in Draft PR #3 was discovered before publishing
an independent local implementation. Its history, handoff, runbook, tests and
latest CI were reviewed. The independent snapshot is not proposed as a competing
runtime. PR #3 independently received the same selector fix in `d33af5d55a518422cbe869f67a477f9946406cdd`
during this review. This follow-up is based on that new commit and
targets `feature/m0-m2-tenant-isolation` without modifying that branch or PR #1.

## Root cause and minimal fix

[M2 run 43477216705](https://github.com/helalalfqih-sketch/Nasqo/actions/runs/43477216705)
failed during anonymous login/shop readiness with HTTP 404. At pinned Odoo SHA
`9cd6f090a8a21d9531c70ceec7f5c51271e24168`, `odoo/service/db.py:list_dbs`
returns the configured `db_name` list only if `dbfilter` is empty. Otherwise it
queries `pg_database` for databases **owned by** the runtime role. The lab
deliberately keeps ownership with postgres, so that query returns no store.
`odoo/http.py:Request._get_session_and_dbname` cannot select the one database.

The upstream fix sets `db_name = nasqo_<validated slug>` and leaves `dbfilter` empty. In this
same upstream pin, `http.db_filter` then intersects every candidate with the exact
configured `db_name` list, including session authentication. It does not accept
an arbitrary database. This follow-up keeps that fix. The gateway still enforces exact Host names and now also
rejects unexpected ports and removes caller-supplied `X-Odoo-Database` headers.
No core patch, shared transaction DB, DB ownership grant or additional privilege.

Do not solve the failure by granting database ownership. Do not inject a trusted
`X-Odoo-Database` header to select browser sessions: this Odoo path is stateless.
The live suite now executes the actual upstream list/filter functions and requires
both HTTP positive controls and foreign-database authentication rejection.

Existing generated operator configs are deliberately not rewritten. For a failed
local pilot, preserve its state and review that one config change before retrying;
the automated suite creates new uniquely named synthetic projects on every run.

## Additional review inputs

The original expanded `downloadfile-1.docx` was located and all 11 pages read in
this follow-up, as well as the attached technical plan. It distinguishes visible
UI capabilities from proposed internal rules. Sections 4–6 and annexes 2–6 support
the future account/opening/voucher/statement/FX requirements; sections 7–8 support
purchase/stock; annexes 1/7 support consent and licensing requirements. Existing
BACKLOG.md remains ordered M3–M8. No reference names, transactions, images, visual
identity or prices are imported. Actual `account` source already has opening move,
reversal and credit-limit fields; validate their behavior before custom add-ons.

## Verification status at follow-up creation

- Previous foundation integration at `3b39d77`: run 43477216839 PASS.
- Previous M2 integration: run 43477216705 FAIL at readiness; later checks not run.
- Local Docker unavailable. GnuPG roundtrip hits the environment's agent/socket
  restriction. These checks must be judged from CI, never relabeled PASS locally.
- New regression and live-selector checks added. New Trivy jobs scan source
  secrets and actual runtime image dependencies, fail on high/critical findings,
  and print identifiers/counts without matched secret values. No findings waived.
- No merge/deployment/production change. Final CI results to be recorded below.

## First observed follow-up run and next correction

At `2d1117f`, static/unit CI passed (20 tests) and
[M1 43479043717](https://github.com/helalalfqih-sketch/Nasqo/actions/runs/43479043717)
passed real installation, upgrade and HTTP. M2 43479044015 reached two verified
stores but failed connecting to the gateway. The concurrent PR #3 fix `175888a`
adds an edge network to only the gateway and an actual unknown-Host readiness
probe. It is integrated here; tenant/DB networks remain internal.

Security run 43479043894 found high/critical image dependencies (151 PostgreSQL
package findings, 76 Nginx), while source/secrets and Odoo passed. The replacement
M2 tags were verified against official-images definitions and source Dockerfiles:

- PostgreSQL 16.16 Alpine 3.24: docker-library/postgres
  `168a848e5905af32aaa5fd6fad4f30906c80af95`, `16/alpine3.24/Dockerfile`.
- Nginx 1.30.6 Alpine 3.24 slim: nginx/docker-nginx
  `4b9f658be76820b24e4ef4605413a5c08707a512`, `stable/alpine-slim/Dockerfile`.

These apply only to newly generated pilot projects. The existing foundation
`postgres:16` remains in the security matrix rather than hiding its findings or
silently changing existing-volume UID/collation behavior. Image digest pinning,
history secret scanning and foundation dependency remediation remain gates.

## PostgreSQL helper remediation

The updated official PostgreSQL image still produced 26 high/critical Go stdlib
findings in security run 43480422883; updated Nginx and Odoo passed. The official
PostgreSQL entrypoint uses `gosu postgres <entrypoint> <args>` only to switch user.
The new Dockerfile replaces that helper with Alpine's `su-exec=0.3-r0`, verifies
UID/GID switching, and retains PostgreSQL and its entrypoint unchanged.
[Alpine's package definition](https://github.com/alpinelinux/aports/blob/3.24-stable/main/su-exec/APKBUILD)
specifies MIT licensing; [upstream semantics](https://github.com/ncopa/su-exec)
provide direct exec after user/group switching. This is remediation in the final
runtime filesystem, not a CVE exclusion. The resulting image must pass a new scan.

M1 v2 uses new named volumes/project; old workspace bootstrap is explicitly
blocked. No existing PostgreSQL volume is converted across Debian/Alpine. The
security matrix now scans the actual current M1/M2 derivative; historical v1
findings remain recorded and v1 must not be used for a new deployment.

M2 [run 43480422857](https://github.com/helalalfqih-sketch/Nasqo/actions/runs/43480422857)
at `df95fe7` passed all 11 acceptance groups, including actual log-secret checks;
20 unit tests passed. The next image-remediation commit must repeat the runtime
checks. Its Odoo, PostgreSQL base and Nginx references are digest-pinned to the
actual images recorded by this successful run. The derived PostgreSQL image is
built locally, never published, and its image ID is recorded in the next report.

Run 43482120855 passed source and full-history secret scans, Odoo and Nginx;
the symlink-based PostgreSQL helper replacement still reported all 26 Go findings.
The next revision replaces the helper with a regular byte-identical su-exec
binary and asserts that fact during build. No finding is ignored. Sanitized
vulnerability target/type metadata is now included to diagnose any remaining
finding; runtime and scanner results must again be checked.
