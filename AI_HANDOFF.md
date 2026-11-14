# NASQO Odoo Community 19 — handoff (2026-11-13)

## Update: original storefront design concept, 2026-11-14

The user selected analysis of the attached Shopify theme and preparation of a
NASQO storefront design. This is a separate static design prototype, not an
Odoo integration or a live ERP/Shopify deployment.

- Branch: `design/shopify-theme-to-nasqo`, based on the tree of GitHub
  `test/merchant-admin-rbac` head `b066c7244c4908ac24b9dce92603aa7e02c4e7a5`.
  Existing worktrees were clean and preserved; no force update or merge.
- Delivery review: [Draft PR #9](https://github.com/helalalfqih-sketch/Nasqo/pull/9).
  First published evidence commit `ad6a3572cf34967aaa37de1dfab83b41b79ed93a`
  has tree `81e6a2a152a645cd90980f8e21f5d94cabe5844b`, matching local commit
  `1b656c3`. Different local/API parentage explains different commit hashes.
  The following documentation-only commit records this PR; no merge requested.
- [Theme analysis](docs/NASQO_STOREFRONT_DESIGN.md) records the exact archive
  fingerprint, 597 files, 101 Indexes-named files, five active home sections,
  editor-only manager controls and client-side order-bridge limitations.
  Original source, live contact details and protected assets are excluded.
- [Private preview](https://nasqo-storefront-concept-20261114.hlalalfqyh87.chatgpt.site)
  is published successfully from separate Sites source commit
  `4aadf4c24c7a9d6aa387abfa4337c40a49f63750`. It requires the owner's ChatGPT
  login; the unauthenticated cloud browser reached that login gate. Local
  browser QA is recorded separately from native publication confirmation.
- Original teal/gold Arabic design, eight synthetic products and original SVGs,
  local Noto fonts with OFL, search/filter/sort/favorites, bounded local cart,
  delivery arithmetic and account/order examples. No backend/API, personal
  fields, actual checkout, payment or outbound messages.
- [Verification](docs/storefront-design/2026-11-14/verification.md) preserves two
  initial failures and their targeted passing retests (navigation timing and
  modal keyboard boundary). Static references/SVG/JS checks and actual Chrome
  interactions passed within the documented scope. Responsive frames are not
  physical mobile-device or WCAG certification.
- Only README, this handoff and `docs/` changed in NASQO. Runtime addons, Docker,
  dependencies, workflows and production data are untouched. Source provenance
  for the preview is in `docs/storefront-design/2026-11-14/delivery.json`.

Next: review the design, then close the existing M1/M2 and RBAC gates before
mapping it into `nasqo_storefront` with QWeb, `website_sale` and Portal. Do not
copy Liquid/Shopify Ajax or treat this visual prototype as completed M3.


## Update: merchant/developer RBAC audit, 2026-11-14

The user selected an actual permission-separation audit. This is evidence and
test infrastructure, not authorization to change live users or deploy roles.

- Branch `test/merchant-admin-rbac`, stacked on `docs/nasqo-app-catalogue-review`.
  Reviewed GitHub base `449923e236259bfdc4fb651032c73663cc9220fa`; matching local
  parent tree `7e5618d6f3db6474b5fe3c3db303f2b71a9e360a`. Other worktrees and the
  server's foundation checkout were preserved. PR #1/#6/#7 remain unmerged.
- Delivery: [Draft PR #8](https://github.com/helalalfqih-sketch/Nasqo/pull/8),
  evidence commit `b90320ec0db1cfc6ac0299f31b2e458fe4aa64ef`, verified tree
  `a663c4668ccb8b224e031409d8f632d2a6c9a7d1`. Local evidence commit `9a0c077`
  has the same tree with different Git parentage; publication used the GitHub
  API without forcing any existing branch. The follow-up only links this PR.
- [Arabic report](docs/RBAC_AUDIT.md), guarded `scripts/rbac/` probes and
  `docs/rbac/2026-11-14/` contain the scope, reproduction commands, metadata,
  source hashes, JSON test results and all twelve RBAC coverage limits.
- Read-only live role inventory before/after: **one active internal user** with
  system/access-management rights; no NASQO-defined role XMLIDs. No names,
  email addresses, business records, credentials or session tokens exported.
- New Docker project `nasqo-rbac-20261114-1815`: internal network, no published
  ports, no production secrets, fresh database/filestore, restricted PG role,
  disabled cron and external SMTP. Installed 182 observed runtime modules plus
  an empty probe: **183 installed**. Seven actors and all business records are
  synthetic. Developer is ordinary authenticated user ID 2, not superuser 1.
- Exact image IDs and all nine NASQO addon source hashes are recorded. Nine
  selected permission/source files match upstream pin `9cd6f09`; this does not
  establish full-image equivalence or certify all dependencies/licenses.
- Main actual HTTP/RPC run: **117 PASS / 6 FAIL**, exit 1. The failures are Apps
  menu visibility (two menu records per merchant profile) and allowed module
  metadata reads (one per profile), caused by installed `base_install_request`.
  They were retained, not changed to PASS. Settings and WhatsApp menus remained
  hidden. A direct URL returning HTML 200 is not an authorization result.
- Both limited merchant profiles created/edited products and quotations;
  persistence was verified. Six install/upgrade/uninstall methods, debug,
  call_button, batch records, technical writes and group injection were denied.
  Private admin attachments were blocked by RPC and guessed download IDs.
  The developer installed/upgraded/uninstalled only an empty synthetic addon,
  with observed state transitions, and could edit the protected setting/user.
- Follow-up **9 PASS / 0 FAIL** verifies the install-review wizard guard and
  intentionally demonstrates unsafe delegation: `base.group_erp_manager`
  allows its holder to add `base.group_system` and then read a technical setting.
  Candidate groups were restored. This is a privileged-role design mistake,
  not an asserted Odoo vulnerability. Never grant this group just for staff
  invitations. Limited merchants cannot create an allowed-role employee yet:
  **RBAC-03 FAIL**, constrained invitations remain absent.
- Disabling a synthetic employee invalidated its old RPC session; its old file
  link returned 404 with no contents. Removing the candidate's administrative
  group denied the next protected read from its existing session.
- A plain internal support candidate could read a synthetic contact and its
  attachment. There is no actual dedicated support/grant/audit implementation:
  RBAC-04/05/11 remain BLOCKED, not accepted through standard internal-user ACLs.
- Main run has no authenticated visual-browser walkthrough. Cross-tenant
  Host/DB/filestore, support expiry/outages, backup/restore and financial posting
  were not retested here. A second company is not a second tenant. M2/M8 and
  AT-032 remain unaccepted by this audit.
- Zero exact matches for the ten generated lab credentials in inspected Docker
  and harness/setup logs and JSON. This is bounded evidence, not a full history,
  CI, dependency or unknown-secret scan. Raw logs/credentials remain off Git.
- Initial PG startup failed because host umask made the mounted init directory
  unreadable. Only public lab source/init permissions were normalized; private
  workspace remained 0700 and credentials 0600. Same lab resumed without deleting
  volumes; installation then exited 0. Preserve this failure in reports.
- At completion only the new lab containers were stopped; their volumes remain.
  Live Odoo/PG remained running and the foundation checkout stayed clean at
  `ca09ad2`. Live PG reports OOMKilled=true but StartedAt is 2026-11-13,
  RestartCount=0, and no OOM/die/start events were returned since 18:10 UTC.
  Historical cause is uninvestigated; no live restart was performed. Closure
  metadata preserves the observation instead of claiming a clean health audit.
- Existing eight repository tests passed; script AST, Bash syntax, diff checks
  and evidence consistency are delivery checks, separate from actual HTTP tests.
  Existing Actions only cover the foundation, not this RBAC matrix. On the base
  commit, runs 43619262022 (static) and 43619262033 (Odoo integration) were both
  confirmed successful; no claim about a later review head is implied.

Next: approve the merchant business-role scope and Apps-catalogue policy, then
implement constrained invitations/technical-role separation in a small addon.
Support needs a distinct audited, expiring authorization design. Add CI and
cross-tenant/browser cases before claiming the whole RBAC gate. No live role
change, production deploy, outbound message or PR merge is included here.

## Update: developer catalogue review, 2026-11-14

The user selected a technical review of the current application catalogue.
This is a read-only audit and documentation change, not approval to install
all applications or begin every planned milestone.

- Review branch: `docs/nasqo-app-catalogue-review`, based on the identity tree.
  GitHub base head: `3e6c3b87c270c1ebb7a836421f6376d7ffb3f2fb`;
  local equivalent parent tree: `1e9a2f346e6fb6639ba69dbe374b9a8828b40828`.
  Draft review: [PR #7](https://github.com/helalalfqih-sketch/Nasqo/pull/7),
  inventory/report commit `a36d1ad`; stacked on PR #6, no merge/deployment.
- [Arabic report](docs/NASQO_APP_CATALOGUE_REVIEW.md) records the complete
  55-application decision matrix, functional gaps, priorities and acceptance
  gates. Raw metadata and CSV are under `docs/catalogue/2026-11-14/`.
- Actual runtime results: **24 installed / 11 uninstalled with source /
  20 uninstallable without source**. The 35 source manifests declare LGPL-3;
  the 20 metadata-only cards declare OEEL-1. Licenses of all transitive assets
  have not been independently audited.
- The unavailable Accounting card is **`accountant`**, ID 702 in this database.
  `account` and `account_payment` are installed. Do not equate UI naming with
  engine capability or assume Enterprise reporting is present.
- Verified schema: opening-entry references, debit/credit, reversal/posting,
  partner credit limits and dated currency rates. This does not prove their
  configured business behavior or permissions. `stock.valuation.layer` is not
  registered; `stock.move.value` and `stock.quant.value` exist in this runtime.
- YER exists but is inactive (rounding 0.01); `l10n_ye`, `account_reports`,
  `report_xlsx` and the five planned NASQO finance/notification modules are
  absent from the inspected source paths. No currency setting was changed.
- `barcodes` is installed; `hr_timesheet` is present but uninstalled. Among
  the 11 available apps, `website_event` additionally needs uninstalled
  `event`; no missing module source was found in dependency closure.
- Scripts in `scripts/audit/` reproduce the probes using Odoo shell metadata
  reads and rollback. They do not query business records or perform writes.
  Keep raw shell logs, credentials and business data outside Git.
- Runtime identifies as `19.0-20261112`; equality with the pinned upstream
  source was not established by this audit. Do not apply these observations
  unconditionally to the separate pinned-source CI environment.
- The 11-page functional reference was read; only requirements were used.
  No names, balances, screenshots or competing identity were copied.
- Delivery checks passed: 55 unique JSON/CSV decision rows, 24/11/20 states,
  manifest/license consistency, 23 schema probes, report links, two Python
  script AST/compile checks and no ORM write/commit calls in those probes.
  `python3 -B -m unittest discover -s tests -v`: 8 existing tests passed;
  `git diff --check` passed. Targeted credential-pattern scan had no matches,
  but is not a full secrets or vulnerability audit. No new transactional,
  permission, restore or financial acceptance tests were run. AT-032 and the
  relevant RBAC/phase gates remain unaccepted here.
- PR #1 and #6 were checked and remain draft/unmerged. No core edits,
  deployments, module installs, customer writes or outbound messages occurred.

Next: review the catalogue decisions, reconcile the runtime/source baseline
and existing M1/M2 gates, then execute a small isolated capability-test batch.
For finance, the first batch must prove Community behavior with synthetic
fixtures before creating `nasqo_finance`, `nasqo_fx`, `nasqo_partner_credit`
or `nasqo_reports`. Control Plane subscriptions remain outside store ledgers;
the WAHA/QR centre does not certify an official notifications provider.

## Update: NASQO PRO identity, 2026-11-14

The user explicitly requested replacement of Odoo-facing identity with
**نسقو برو**. The separately requested live branding work is recorded in
[docs/NASQO_PRO_BRANDING.md](docs/NASQO_PRO_BRANDING.md); the older foundation
notes below remain historical. Do not infer SaaS, RBAC, or checkout readiness
from this presentation update.

- Review branch: `feat/nasqo-pro-identity`, based on `ca09ad2` from the foundation branch.
- Draft review: [PR #6](https://github.com/helalalfqih-sketch/Nasqo/pull/6).
  Implementation commit: `c2bf1f0`; no automatic merge or release.
- Published baseline commit `519a65b` captures seven existing server presentation addons;
  the following commit contains the PRO delta, verification scripts and docs.
- All seven addon upgrades passed on an independent pilot and on the requested
  live site. Live verification: 35 authenticated HTTP checks, 9 public tests,
  JavaScript title/dialog contracts, and four rendered notification/report layouts.
- A consistent local database/filestore backup preceded the update. SHA checks
  passed; no restore test was performed in this branding task.
- Hash comparison of 12 business tables passed. Only the system bot contact was
  intentionally excluded because its display name/icon were updated. Company,
  customer, product, order, accounting and stock data were preserved.
- Preserve all translations of customized website views, including pending
  `_en_US` entries. Plain per-language `arch_db.write` synchronizes structure and
  can discard custom markup; the live footer was repaired from its guarded
  snapshot through the ORM translation cache, with `clear_cache('templates')`.
  The explicit Odoo Facebook promotional widget was removed; social links remain.
- `web.web_app_name`, the existing website display name and system bot identity
  are environment settings, not generalized automatic tenant migrations.
- Logs, database snapshots, configurations, credentials and customer data stay
  off Git. PR #1 remains unmerged. GitHub Actions status must be checked on the
  current review head; only the separately listed local/pilot/live results are
  certified here.

Next: review the branding diff and manually inspect authenticated business
screens with the user's intended roles. Real PDF output and full responsive
end-to-end tests remain separate; no message was sent and no order was created.

## Scope
Isolated proof of concept on GitHub branch `chore/odoo19-ecommerce-foundation` and Draft PR #1. Do not merge automatically or touch the legacy NASQO VPS.

## Architecture
- GitHub Codespace on `mcr.microsoft.com/devcontainers/base:ubuntu-24.04` with Docker-in-Docker.
- Separate Docker Compose project `nasqo-odoo19-development`.
- Postgres 16 with private storage and a **non-superuser** role `nasqo_dev`.
- Odoo dependencies supplied by official date-tagged `odoo:19.0-20261112` image.
- Application starts with the exact Odoo source SHA recorded in `upstream.json`, fetched to ignored `vendor/odoo`.
- First two CI integration runs could not read vendor/odoo/odoo-bin inside the non-root Odoo container. The repo was fetched under umask 077, which protects secrets but also restricted public Git checkout to the host UID. The isolated public checkout and its parent vendor/ directory now get read/execute permissions (chmod a+rx vendor and chmod -R a+rX vendor/odoo) after cloning; .env retains 0600. GitHub Actions output identified vendor as 0700. Await CI verification.
- The local `nasqo_store` module depends on Odoo Community `website_sale`.
- Port 8069 binds to loopback. Codespaces port visibility must remain Private.
- Passwords are fresh random dev-only secrets stored in ignored `.devcontainer/.env` (mode 0600).

## Reproducible validation
- `python3 -B -m unittest discover -s tests -v` — static configuration checks.
- `bash -n scripts/codespace/*.sh .devcontainer/db-init/*.sh scripts/fetch_upstream.sh` — shell syntax.
- `bash scripts/codespace/bootstrap.sh` — real PostgreSQL role initialization, Odoo module install/upgrade, admin password rotation, and HTTP login/shop smoke checks.
- `bash scripts/codespace/verify.sh` — read-only module state/HTTP checks.

## Status and remaining blockers
- GitHub Actions on commit a99a9146 **PASS**: real Odoo 19 installation of website_sale/nasqo_store and module upgrade, plus DB module state checks. First HTTP request hit a transient connection reset immediately after service start; verify.sh now retries temporary socket failures. Await a full green integration run.
- Module has no custom storefront logic yet.
- E2E product/cart/checkout/COD, Arabic/RTL, roles, invoicing, migration and rollback still require separate tests.
- No Codespace or deployment is persistent. Never bring live customer or production secrets into this repo.
- Keep Draft PR #1 open for review.
