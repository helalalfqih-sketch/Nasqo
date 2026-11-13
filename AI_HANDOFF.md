# NASQO Odoo 19 — M0–M2 handoff (2026-11-13)

## Current branch and scope

Draft PR #4: `fix/m2-runtime-verification`, stacked on Draft PR #3
`feature/m0-m2-tenant-isolation`. PR #3's runtime fix `175888a` and documentation
`ba76677` are integrated without modifying its branch. PR #1 remains Draft at
`ca09ad2`; main, production, Shopify and customer databases are untouched.
No PR was merged, no image/service was published, and no data was migrated.

This round is M0–M2 only. The full attached technical plan and original expanded
11-page functional reference were read. Requirements inform an original NASQO
design; no reference code, visual assets or sample personal/financial data were
imported. The older upstream note saying the Word reference was unavailable is
superseded by this review.

## Observed evidence

| Check | Result | Evidence / limit |
|---|---|---|
| Base PR #3 two-store pilot | PASS | Runtime `175888a`, run 43479599787; preserved report `docs/validation/m2-results-175888a.json` |
| Follow-up M1 installation/upgrade/HTTP and narrow mount checks | PASS | `df95fe7`, run 43480423152 |
| Follow-up M2: two stores, selector/Host/session/ORM/DB/filestore isolation, ACL, failure/retry and encrypted restore | PASS, all 11 groups | `df95fe7`, run 43480422857; includes actual container-log secret checks |
| Follow-up Python unit tests | PASS, 20 cases in CI | Same M2 run; no encryption skip |
| Updated Odoo/Nginx image scans and source secrets | PASS | Security run 43480422883 |
| Official PostgreSQL base before helper remediation | FAIL | 26 high/critical Go stdlib findings; old foundation image had 151 package findings. No waivers |
| Hardened derivative, full-history scan and M1 v2 | PENDING | Runtime commit `346b8e9`; rerun after integration of concurrent documentation removes PR conflict |
| Local tests | 20 PASS, 1 environment ERROR | GPG cannot start its agent here; actual encryption passed in CI |
| Local Docker / actual Codespace | BLOCKED / not accessed | Docker/psql unavailable locally; no persistent Codespace was created. Live evidence comes from disposable GitHub runners |

Historical failures and their root causes remain in `docs/RUNTIME_SELECTOR_FIX.md`.
A failed or unexecuted case is not acceptance. Current image changes require their
own successful run before claiming security/runtime completion.

## What is implemented

- Base PR #3: private local operator registry, durable idempotency and phase/event
  state, per-store PostgreSQL/Odoo/filestore/networks, allowlisted gateway, failure
  quarantine and same-key recovery, encrypted offline backup and fresh restore.
- `provisioning/runtime.py`: native Odoo exact database allowlist regression,
  strict Host/port routing, stripped client X-Odoo-Database, edge network only for
  the loopback proxy, and building the reviewed PostgreSQL image for new projects.
- `tests/isolation/run.py`: actual upstream selector checks, A/B positive and
  negative HTTP/ORM/DB/file tests, foreign-session/write attempts, restricted DB
  role, restored records and bytes, and generated secrets absent from actual logs.
- `.devcontainer/compose.yaml`, `scripts/codespace/`: narrow public-code mounts;
  v2 project and fresh volume names; bootstrap refuses a v1 completion marker
  before credentials or Docker operations. Existing volumes are not converted.
- `docker/postgres/Dockerfile`: pinned PostgreSQL 16.16 Alpine base, same official
  entrypoint/PostgreSQL, replacing only the vulnerable Go-based gosu helper with
  Alpine su-exec 0.3-r0 (MIT). Build checks user/group switching. No image push.
- `.github/workflows/security.yml`: pinned Trivy, exact current image scans,
  source secrets, checksum-verified Gitleaks 8.30.1 over full fetched Git history.
  High/critical or secret findings fail. Matched secret values are not printed.
- Odoo/Nginx and PostgreSQL base digests come from actual successful M2 runtime
  evidence. The derived local image ID is recorded by the next run.
- README, M0/M2 runbook, acceptance traceability and detailed
  `docs/PHASE_PLAN_M3_M8.md` describe scope, tests and next phase decisions.

## Architecture and dependencies

Odoo source remains exactly `9cd6f090a8a21d9531c70ceec7f5c51271e24168`, clean and
unmodified. Twelve relevant Community module manifests are LGPL-3. YER exists;
`l10n_ye` does not exist in this pin. `account` is Invoicing; Enterprise capability
is not assumed. Existing opening, reversal, balance validation and credit-limit
fields require behavioral gap tests before creating custom financial modules.

Odoo 19 with a nonempty dbfilter enumerates role-owned databases. The non-owner
runtime therefore fixes one db_name and leaves dbfilter empty; actual upstream
list_dbs/http.db_filter plus foreign-DB HTTP rejection were tested. The tenant
role has CONNECT-only access to its own empty postgres maintenance catalog for
startup, without TEMP/CREATEDB; no access to another tenant's PostgreSQL network.

Only the trusted proxy has an edge network; Odoo/DB networks remain internal.
The gateway publishes loopback 18069 and M1 loopback 8069. Public DNS/TLS and
Codespaces browser-host routing are not implemented. Docker operators are trusted.

## Remaining limits and decisions

- This is a synthetic, single trusted-operator pilot, not public merchant signup.
  AT-001, complete support RBAC/audit in AT-006, and real HTTP/DB interruption in
  AT-030 remain pending. The latter currently injects worker failure after DB creation.
- AT-032 currently proves source/license availability, not complete accounting
  reports or financial policy. M3–M8 are planned, not implemented.
- Backup is offline, in-memory and limited to 512 MiB, with a local operator-held
  key. No off-host retention, key manager, measured RPO/RTO or SLA is promised.
- No registration/verification, distributed queue, subscription billing, payment
  completion, Arabic visual review or production deployment in this round.
- Adopted image pins still require ongoing maintenance, penetration testing and
  review. A passing scanner is not a security certification.
- Financial sign convention, opening counterpart, tax/localization, FX source/
  precision, credit overrides, payment settlement, pricing/grace and retention
  decisions require approval before their dependent phase.

## Reproduce and next actions

Use a fresh Docker-enabled Codespace on this branch or the disposable CI runner:

```bash
python3 -B -m unittest discover -s tests -v
bash scripts/codespace/bootstrap.sh
bash scripts/m2/run.sh
```

M1 v2 rejects an existing v1 workspace. M2 always creates unique synthetic projects
and preserves old volumes. No reset/down -v/prune or automatic cleanup is provided.

1. Inspect all new CI jobs for the hardened image and M1 v2; fix real failures.
2. Record final sanitized evidence and exact code/run references here and in PR #4.
3. Review Draft PRs #1/#3/#4 and pilot limits before authorizing M3.
4. Follow `docs/PHASE_PLAN_M3_M8.md`; never merge or deploy automatically.
