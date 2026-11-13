# NASQO Odoo 19 — M0–M2 handoff (2026-11-13)

## Scope and branch

`feature/m0-m2-tenant-isolation`, based on foundation
`ca09ad2b467610c62f2311a2d935f82b8d94cd3b`. PR #1 remains open Draft and unchanged.
The new PR targets its foundation branch so reviewers see only the M0–M2 delta.
No production, Shopify, GrowERP, customer data, merge, deployment or release work.

## Inspected baseline

All foundation files, recent Git history, PR #1 metadata/comments and the attached
implementation plan were inspected before editing. Baseline static tests: 8/8.
Foundation [integration run 43445738433](https://github.com/helalalfqih-sketch/Nasqo/actions/runs/43445738433)
passed on `ca09ad2`: real Odoo install/upgrade, module DB states, login/shop HTTP.
This corrects the stale pending status in the earlier handoff.

Pinned Odoo source is unchanged:
`9cd6f090a8a21d9531c70ceec7f5c51271e24168`. Community module licenses/manifests and
`base.YER` were inspected. No `l10n_ye` in that source. The original 11-page Word
was not re-read because only the derivative technical plan was attached here.

## Implementation

- `provisioning/registry.py`: private local SQLite operator registry, unique
  key/slug, OS lock, phase/status events, fail-closed provisioning/retry.
- `provisioning/runtime.py`, `scripts/m2/`: independent Odoo/PostgreSQL networks
  and volumes per test store, least-privilege DB roles, exact dbfilter, no public
  tenant ports, narrow mounts, verified activation and allowlisted loopback proxy.
- `provisioning/backup.py`: offline consistent DB+filestore, encrypted GPG archive,
  identity/version/hash/path checks, fresh same-tenant restore, outbound/cron/mail
  disabled in restored runtime; no overwrite or automatic data deletion.
- `provisioning/cli.py`: local trusted-operator interface, not a public SaaS API.
- `tests/test_provisioning.py`: concurrency, idempotency, conflict, fail/retry,
  private state, malicious archive paths, integrity and encryption tests.
- `tests/isolation/`: real HTTP/ORM/DB/filesystem/restore checks with synthetic
  products, orders, users and private attachments; positive controls in both stores.
- `.github/workflows/tenant-isolation.yml`: actual M2 integration on fresh runner.
  Static workflow now parses every shell script (bash -n with many args only parses
  the first script). Existing single-store foundation flow remains separate.
- `docs/M0_REVIEW.md`, `M2_RUNBOOK.md`, `TEST_PLAN.md`, `BACKLOG.md`: decisions,
  exact commands, coverage/limits and ordered M3–M8 work; original plan preserved.

## Observed validation before first PR run

- Python syntax: PASS for all new Python files.
- Bash syntax: PASS for every foundation and M2 shell script.
- Unit tests: 17 PASS, 1 ERROR locally. The failing encryption roundtrip reaches
  GnuPG but this executor disallows Unix sockets: `gpg-agent: can't create socket:
  Operation not permitted`. Treat encryption execution as BLOCKED here, not PASS.
- Local Docker integration: BLOCKED (no Docker CLI/daemon, psql or sudo).
- New M2 GitHub integration: pending; must record actual run result before
  accepting the runtime. No claim of completed M2 based on static checks.

## Remaining limits and decisions

This is a single trusted-operator, synthetic-data proof, not a hosted service.
Merchant registration/verification, platform RBAC/MFA/support audit and distributed
queue are backlog. AT-006/030 cover only the documented pilot portions.
M3–M8 and full accounting capability tests are not implemented. YER tax/ledger/FX
policy requires product/accounting decisions. No SLA is established.

Image tags are recorded at runtime but not yet digest-pinned in configuration;
full image/dependency CVE/history secret scans and penetration testing remain
release gates. Generated values are scanned against tracked files; routine
command output is captured and known credentials redacted on errors.
Backup is offline, in-memory, capped at 512 MiB, with operator-held local key;
off-host retention/key custody must be designed before commercial usage.

## Exact next actions

1. Push the development branch and open a Draft PR against foundation.
2. Inspect every new CI job; fix failures and rerun relevant checks.
3. Record final commit/run URLs and PASS/FAIL/BLOCKED results here and in the PR.
4. Keep both PRs unmerged; review pilot gaps before M3. Do not delete volumes.
