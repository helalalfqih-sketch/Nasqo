# Acceptance traceability

Status is recorded in `AI_HANDOFF.md` and the actual CI job. This table describes
coverage, not a claim that a job has passed. The source contract is
[IMPLEMENTATION_PLAN_v1.0.md](IMPLEMENTATION_PLAN_v1.0.md).

Observed on runtime commit `f1ae638`: **21 unit tests and all 11 reported pilot
acceptance groups PASS** in [run 43483024980](https://github.com/helalalfqih-sketch/Nasqo/actions/runs/43483024980).
The [recorded JSON](validation/m2-results-f1ae638.json) includes image IDs and provenance.
[Security run 43483024786](https://github.com/helalalfqih-sketch/Nasqo/actions/runs/43483024786)
passed all source/history/image jobs without CVE waivers.
This does not mark the deferred or partially covered AT cases below complete.

| Test | Coverage / next gate |
|---|---|
| AT-001 | Backlog: merchant signup, email verification and ownership binding |
| AT-002 | M2 live: two Odoo installs/upgrades, module DB state, login/shop HTTP, gateway |
| AT-003 | M2 live duplicate request/container identity; unit concurrent reservation and conflict cases |
| AT-004 | M2 live: positive/negative products, orders, attachments, copied sessions, attempted write, DB privilege and filestore scope |
| AT-005 | M2 live: unknown Host, forged forwarded headers, explicit foreign DB parameter/auth, blocked database/legacy RPC routes |
| AT-006 | Partial pilot: anonymous/portal admin denial. Dedicated support role and audited temporary access remain backlog |
| AT-007–010 | M3: Arabic mobile RTL, COD, bank transfer, checkout retry; not implemented here |
| AT-011–020 | M4: accounting/opening/vouchers/statements/FX/credit; not implemented here |
| AT-021–024 | M5: transfers/UoM/import/Arabic PDF-XLSX; not implemented here |
| AT-025–026 | M7: consent, official provider, retry and no-send; not implemented here |
| AT-027 | M6: expiry/grace/export without deletion; not implemented here |
| AT-028 | M2 live: stop writer, DB+filestore encrypted pair, integrity/hash/path checks, isolated fresh restore, ORM/attachment byte equality and HTTP |
| AT-029 | M2 live: wrong tenant rejected before Docker mutation; unit hash/path/symlink and encrypted tamper cases |
| AT-030 | Partial pilot: real failure injected after DB creation, quarantine and safe same-key recovery. Distributed queue/network-chaos cases remain backlog |
| AT-031 | M4: posted-entry ACL/reversal/audit; not implemented here |
| AT-032 | M0 manifest/license/source review complete; detailed Community accounting capability execution is an M4 gate |

Extra checks: generated secret values are compared against tracked files and
actual tenant/restore/gateway container logs, without printing those logs.
Foundation runtime checks ensure operator state and repository credentials are
not mounted. Trivy separately scans source secrets and all runtime image
dependencies; high/critical findings fail the gate, with no waivers. Git-history
secret scanning now runs in CI; penetration testing remains a launch requirement.
No type-checker is configured for the stdlib-only Python code; syntax,
unittest, Bash parsing and CI ShellCheck cover the current implementation.

Acceptance requires positive controls as well as denial: each tenant must read
its own fixtures first. Equal numeric IDs in two databases are expected; tests
compare unique marker contents and confirm the source record is unchanged after
an attempted cross-database write. A 404 alone does not prove tenant isolation.
