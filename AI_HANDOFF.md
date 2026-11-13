# NASQO Odoo 19 — M0–M2 handoff (2026-11-13)

## Current result

**The local-operator M2 pilot passed real integration on GitHub Actions.**
Runtime code commit: `175888af91e719c1ba794c431b6cfcadf79664cf`.
Branch: `feature/m0-m2-tenant-isolation`.
[Draft PR #3](https://github.com/helalalfqih-sketch/Nasqo/pull/3) targets
`chore/odoo19-ecommerce-foundation`. The following documentation commit changes
no runtime or test code. PR #1 remains open Draft at `ca09ad2`; no merge or deployment.

| Validation | Observed result | Evidence |
|---|---|---|
| Python unit tests | PASS, 19 cases, including concurrent reservations and encrypted tamper rejection | M2 job below |
| Bash parsing and ShellCheck | PASS | M2 job below |
| Original single-store install/upgrade, DB and HTTP | PASS | [43479599857](https://github.com/helalalfqih-sketch/Nasqo/actions/runs/43479599857) |
| Two stores, routing, idempotency, failure/retry, isolation, ACL and restore | PASS, all 11 reported groups | [43479599787](https://github.com/helalalfqih-sketch/Nasqo/actions/runs/43479599787) |
| Static workflow | PASS | [43479599803](https://github.com/helalalfqih-sketch/Nasqo/actions/runs/43479599803) |
| Local Docker run | BLOCKED: executor has no Docker/psql/sudo | Actual runtime evidence comes from CI, not this executor |
| Local GPG execution | BLOCKED: gpg-agent Unix sockets denied; corresponding CI tests PASS | Initial local suite had 1 environment error; no skip was used to make CI green |
| Full image CVE/history secret scan, production review | NOT RUN / release gates | No production readiness claim |

The [machine-readable report](docs/validation/m2-results-175888a.json) preserves
actual acceptance results, upstream SHA, OCI image digests, code commit and run URL.
These are ephemeral CI runtimes; no persistent Codespace or public store was created.

## Inspected baseline and source

All foundation files, Git history, PR #1/comments and the attached technical plan
were inspected before editing. Baseline had 8 passing static tests and a passing
single-store integration run 43445738433 at `ca09ad2`; its old handoff was stale.
The separate GrowERP checkout with uncommitted work was not changed.

Odoo remains pinned to `9cd6f090a8a21d9531c70ceec7f5c51271e24168`, with a clean
upstream checkout and no core edits. Twelve relevant Community module manifests
were verified as LGPL-3. `base.YER` exists; `l10n_ye` does not exist in this pin.
Only the derivative implementation plan was attached in this round; the original
11-page Word file was not re-read. See [M0 review](docs/M0_REVIEW.md).

## What changed and why

- `provisioning/registry.py`: private SQLite **operator registry only**, unique
  idempotency key/slug, serialized worker, status/event records and safe retry.
  Store transactions remain exclusively in Odoo/PostgreSQL.
- `provisioning/runtime.py`, `scripts/m2/`: per-store Odoo/PostgreSQL containers,
  distinct networks and volumes, non-owner/non-superuser DB roles and narrow
  mounts. A named operator container prevents concurrent writers after a crash.
- `provisioning/backup.py`: stop the application writer, snapshot DB+filestore,
  encrypt the pair, validate identity/version/hashes/archive paths, and restore
  into a new isolated project with no route. No overwrite or automatic deletion.
- `provisioning/cli.py`: trusted local-operator commands; no public signup/billing API.
- `tests/test_provisioning.py`, `tests/isolation/`: unit tests plus real synthetic
  products/orders/users/attachments and positive/negative access checks.
- `.github/workflows/tenant-isolation.yml`: real M2 execution; foundation/static
  workflows now parse each Bash file separately.
- README and `docs/`: preserved plan, M0 dependency review, operating runbook,
  acceptance mapping and ordered M3–M8 backlog.

## Important implementation decisions verified in CI

1. Odoo 19's `list_dbs` with a regex dbfilter enumerates DB ownership. A non-owner
   runtime must use the configured **single-name db_name allowlist** with empty
   dbfilter. Upstream `http.db_filter` then rejects all other names. This avoids
   both ownership escalation and core modification. HTTP/database-selection
   negative tests passed.
2. Odoo startup needs CONNECT-only access to the empty `postgres` maintenance DB
   inside that tenant's private PostgreSQL container. It has no TEMP/CREATEDB rights.
3. Only Nginx joins a normal edge network, publishing `127.0.0.1:18069`. All tenant
   networks are internal. Unknown Host, forged forwarded headers, foreign DB
   query/login, copied sessions and direct cross-container DB TCP attempts failed
   as expected. A/B still successfully read their own fixtures.
4. GPG encryption/integrity, paired checksums and restored ORM/attachment bytes
   passed. Alpha's backup was rejected for Beta before any Docker mutation.
5. Generated credentials/recovery keys were absent from tracked files. Commands
   capture output and redact known credentials on errors; raw secrets are not logged.

## Scope limits / remaining work

This is a synthetic-data, single trusted-operator proof. Merchant registration and
verification, platform RBAC/MFA/support audit, a distributed queue, public DNS/TLS,
checkout, Arabic visual validation, finance, inventory workflows and billing remain
in [BACKLOG.md](docs/BACKLOG.md). AT-006 and AT-030 cover only their documented pilot
portions; AT-032 has source/license review, not a complete financial capability test.

Image digests are recorded but configuration still uses tags. Pin/review images,
run full vulnerability/history-secret scans and penetration tests before launch.
Backup is offline and in-memory, capped at 512 MiB, with a local operator-held key;
off-host retention, key custody, RPO/RTO and SLA need design and validation.
Accounting/tax/FX/sign/credit policies still require product and accounting approval.

## Reproduce and next actions

```bash
python3 -B -m unittest discover -s tests -v
bash scripts/m2/run.sh
```

Run these on a disposable Docker-enabled Codespace/runner. Every suite creates
fresh isolated test state; it does not delete prior volumes. See
[M2_RUNBOOK.md](docs/M2_RUNBOOK.md) for manual provisioning and backup commands.

Next: review Draft PR #3 and its evidence, close the merchant identity/support/
security gaps, then authorize the next small M3 increment. Keep both PRs unmerged
until reviewed. No production or Shopify/GrowERP changes were made.
