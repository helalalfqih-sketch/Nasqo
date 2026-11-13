# NASQO Odoo 19 — M0–M2 handoff (2026-11-13)

## Visual-evidence follow-up

Branch `test/m2-visual-evidence` starts at verified PR #4 head `3a3c06f`.
The user requested actual screenshots because no NASQO Codespace is connected.
Added `tests/isolation/screenshots.py` and screenshot/artifact steps to the M2
workflow, with `docs/VISUAL_EVIDENCE.md` and a README pointer. The capture reads
anonymous synthetic test pages only and leaves runtime/configuration/fixtures
unchanged. Local Docker remains unavailable. Actual CI capture and visual
inspection are pending; the next action is to run and inspect the four PNGs.
No custom NASQO design or public preview is implied. Prior runtime evidence below
continues to describe PR #4, not a successful screenshot run.

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

## Final observed evidence

All four workflows passed on runtime commit
`f1ae63823a0b9368ac83193e500367c6e20c08ec`. The subsequent evidence/documentation
commit changes no runtime, workflow or test code. Do not confuse the old failed
image scans with this final run, or generalize this pilot to production readiness.

| Check | Result | Evidence / limit |
|---|---|---|
| M0 source/module/license review | PASS | 12 Community manifests; exact clean Odoo pin, no core edits |
| Python unit tests and Bash checks | PASS, 21 tests | [43483025304](https://github.com/helalalfqih-sketch/Nasqo/actions/runs/43483025304), includes GPG roundtrip/tamper and the v1 workspace guard |
| M1 v2 installation, upgrade, module DB state, /web/login and /shop | PASS | [43483024796](https://github.com/helalalfqih-sketch/Nasqo/actions/runs/43483024796); runtime cannot read .m2/.env/.git |
| M2 two stores, exact selector/Host/session/ORM/DB/filestore isolation, idempotency, ACL, failure/retry and encrypted restore | PASS, all 11 reported groups | [43483024980](https://github.com/helalalfqih-sketch/Nasqo/actions/runs/43483024980); includes actual container-log secret checks |
| Source secrets, full fetched Git history, Odoo/Nginx/PostgreSQL image recipes | PASS; zero selected HIGH/CRITICAL findings | [43483024786](https://github.com/helalalfqih-sketch/Nasqo/actions/runs/43483024786); no waivers, not a penetration test |
| Local Docker / actual Codespace | BLOCKED / not accessed | No Docker/psql locally; no persistent Codespace created. Live evidence comes from disposable GitHub runners |
| Local GPG | BLOCKED by agent startup | Corresponding CI encryption/tamper/restore tests PASS; no skip used |
| Full AT-001/006/030/032 and M3–M8 | NOT COMPLETE | Pilot ACL and worker fault recovery are partial; public identity/support/transport-failure and financial gap tests remain |

Machine-readable records: `docs/validation/m2-results-f1ae638.json` and
`docs/validation/security-f1ae638.json`. They preserve code/run IDs, individual
acceptance outcomes and actual runtime image IDs. The older PR #3 report remains
as baseline evidence. Failed iterations and source diagnosis are preserved in
`docs/RUNTIME_SELECTOR_FIX.md`.

The security job and integration jobs build PostgreSQL independently from the
same digest-pinned base and exact helper package. Their generated image IDs may
differ; no registry image is published. Build-once/promote-by-digest and signed
provenance remain production supply-chain work. Odoo and Nginx use exact digests.

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
  evidence. The derived local image ID is recorded in the final report.
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

1. Review Draft PR #4 and its exact runtime/security evidence; it remains Draft/unmerged.
2. Review the stacked foundation PR #1 and pilot PR #3, preserving their changes.
3. Close public merchant identity, support audit and real HTTP/DB fault gaps, then
   approve M3 decisions. M3–M8 have not been started.
4. Follow `docs/PHASE_PLAN_M3_M8.md`; never merge or deploy automatically.

## Git delivery

Published follow-up commits include `2d1117f` (selector/security checks), `df95fe7`
(gateway integration/narrow mounts), `346b8e9` (pinned fresh images, v2 protection,
full-history scan and detailed plan), `ffea016` (concurrent documentation integration),
`9bc1ca3` and `f1ae638` (verified helper replacement and OCI removal metadata).
The final evidence commit contains documentation/JSON only. Local unpublished
branch `local/m0-m2-proof-snapshot` preserves an earlier alternative; it is not
proposed as a competing implementation. No unrelated work was overwritten.
