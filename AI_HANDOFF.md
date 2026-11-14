# NASQO Odoo Community 19 — handoff (2026-11-13)

## Update: developer catalogue review, 2026-11-14

The user selected a technical review of the current application catalogue.
This is a read-only audit and documentation change, not approval to install
all applications or begin every planned milestone.

- Review branch: `docs/nasqo-app-catalogue-review`, based on the identity tree.
  GitHub base head: `3e6c3b87c270c1ebb7a836421f6376d7ffb3f2fb`;
  local equivalent parent tree: `1e9a2f346e6fb6639ba69dbe374b9a8828b40828`.
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
