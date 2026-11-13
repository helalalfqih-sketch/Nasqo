# NASQO Android Offline Accounting — implementation plan

**Status:** Proposed; no implementation started by this document.  
**Depends on:** ADR-0001 (ANDROID_OFFLINE_ARCHITECTURE.md); NASQO Odoo 19 foundation branch.  
**Change policy:** feature branches, reviewed PRs; no edits to Odoo core; no production credentials.

## Intended MVP (vertical slice)

A registered staff user can log in online, download their permitted customers and products, open the Android app offline, create an **unposted invoice draft**, restart the phone without losing it, reconnect and synchronize the draft. Odoo revalidates taxes/totals, returns a single server document and its state, and the app displays an explicit success/conflict/rejection. Official posting is a separate server-authorized online action.

The MVP EXCLUDES bank reconciliation, final offline receipts, offline inventory reservation, automatic invoice posting, third-party payment capture, branch-wide shared balances and robust multi-company switching until independently tested.

## Work packages and dependency order

| Phase | Deliverable | Exit checks |
| --- | --- | --- |
| 0. Specification and baseline | Confirm accounting chart, taxes, roles, Android minSdk, supported offline window, supported currencies and number precision. Start isolated Odoo 19 + PostgreSQL test DB, maintain source SHA. | Verified install of Odoo account, stock, sale where needed; sample company & users; no customer data |
| 1. API + identity + sync ledger | New addons/nasqo_mobile_sync, service-level sync API, identity/device binding, versioned API schema, idempotency receipt, ordered change feed and tombstones. | Unit/integration tests for 401/403, cross-company 403, duplicate requests, bad payloads, transaction rollback |
| 2. Android baseline | New mobile/nasqo_android Flutter app; Arabic RTL, secure online enrollment, encrypted SQLite, migrations, repository interfaces, offline catalog. | App launches disconnected after first login; DB encrypted, cold restart preserves data |
| 3. Two-way sync | Outbox, stable UUIDs, dependency resolution, push/pull, cursor, retries, manual sync, conflict UI and reconciliation. | Simulated packet loss, lost ACK, server 500, 409 conflict, device restart, multi-device |
| 4. Accounting vertical slice | Cached partners/products; offline invoice draft/lines; server authoritative amounts and submission review; record rules. | Create offline, sync once, correct tax/currency, reject insufficient permissions, no official number offline |
| 5. Hardening and field pilot | CI tests, security review, performance under low-end hardware, Odoo migration drills, database+filestore restore rehearsal and pilot sign-off. | Document exact test outcomes, defects, recovery plan, deployment approval separated from PR merge |

**Rough sizing, not a delivery promise:** A small experienced team may need roughly 10–16 weeks for a focused pilot once requirements and test infrastructure are ready. Native printing, fully offline accounting/settlement and advanced regulatory reporting materially expand scope.

## Proposed repository layout

~~~text
Nasqo/
├── addons/
│   ├── nasqo_store/                   # existing ecommerce foundation
│   ├── nasqo_mobile_sync/             # NEW Odoo domain commands & sync log
│   │   ├── __init__.py
│   │   ├── __manifest__.py
│   │   ├── controllers/
│   │   ├── models/
│   │   ├── security/
│   │   ├── data/
│   │   └── tests/
│   └── nasqo_accounting/              # future business extensions, optional
├── mobile/
│   └── nasqo_android/                 # NEW Flutter app
│       ├── lib/core/
│       ├── lib/features/
│       ├── lib/data/local/
│       ├── lib/data/remote/
│       └── test/
├── services/
│   └── sync_gateway/                  # NEW FastAPI/auth, deployed separately
├── docs/
│   ├── ANDROID_OFFLINE_ARCHITECTURE.md
│   ├── ANDROID_IMPLEMENTATION_PLAN.md
│   └── UPDATES.md
├── tests/
├── upstream.json
└── AI_HANDOFF.md
~~~

The paths labelled NEW are plans and must not be mistaken for already-created code. Deployment can later separate Android, gateway and Odoo modules into their own repositories, but start with clear component boundaries and reviewable pull requests.

## Backend tasks

- Define Odoo security groups and record rules. Map authenticated gateway identity to Odoo user and allowed company without trusting caller-supplied fields.
- Implement domain commands, NOT generic create/write/post for arbitrary models.
- Implement idempotency table with unique tenant/company/device/operation key and payload hash, result state and audit trail.
- Implement stable client/server ID mapping, dependency resolution and commit-ordered change log with tombstones.
- Design business transactions and server-side validation for customer, product, invoice draft and payment intent; final invoice posting remains online.
- Publish API schema (OpenAPI), typed mobile client and stable error codes. Include limits and response examples.
- Add Odoo tests: duplicate call concurrency, conflict, invalid partner, inactive product, missing company, restricted user, posting workflow and server restart.

## Mobile tasks

- Flutter module boundaries: presentation -> repository -> encrypted SQLite/outbox; UI never reads from raw network response.
- Implement SQLCipher database setup with random key protected by Android Keystore; verify the actual crypto library and Android ABI builds before committing to it.
- Implement secure sign-in and device enrollment. Support a local unlock policy for disconnected use.
- Model immutable operation_id, local draft UUID, base_revision, dependency queue and idempotent ack application.
- Implement sync visible status: last successful timestamp, pending count, conflicts and errors. Manual retry always offered.
- Write widget, repository, database migration and end-to-end tests; support Arabic RTL and currencies with exact decimal arithmetic.

## CI and release gates

- PR checks: Python static + Odoo unit/integration tests against disposable PostgreSQL; Flutter analyze/test; Android release build; API schema compatibility; dependency/secret scans.
- Use reproducible pinned Odoo commit and reviewed dependency updates; never vendor Enterprise code.
- Gateway service/DB rollout and Android app release are separately versioned; minimum supported API version declared.
- Database changes require forward migration and tested recoverability; backup both Odoo database and filestore. A code-only rollback may not reverse posted transactions.
- Do not merge to main or deploy to production automatically. Protect branch and require code review after CI is stable.

## Acceptance test scenarios (must be automated where feasible)

1. Fresh install requires online enrollment, then 72 hours offline draft work survives restart.
2. Lost response after Odoo successfully created draft: 100 retries create zero duplicates.
3. App crashes between receiving ACK and SQLite update: replay remains safe.
4. Concurrent edit on two devices creates explicit conflict and retains both versions for resolution.
5. Tax/pricelist changes online while phone disconnected: totals shown as revised and must be accepted before posting.
6. Stock quantity shown as stale while offline; cannot reserve/ship stock locally.
7. Permission or company access revoked: next sync rejected; cached scope locked or removed under policy.
8. Attack sends another company's company_id or arbitrary Odoo model: rejected.
9. Interrupted pull page leaves cursor at last fully committed local page.
10. Corrupt local DB, schema migration failure, limited storage and no network: no silent loss; recovery policy documented.

## Open product decisions (do not silently assume)

- Which business is the first pilot: one company/store vs multiple branches?
- Cash-vs-accrual policy, chart of accounts and fiscal localization/tax rules?
- Should receipts be draft only offline? Recommended yes until legal requirements and conflict control are resolved.
- Supported Android version, printer models, device fleet management and offline lock duration?
- Invoicing only or full accounting reports? Odoo Community's account module supplies invoicing basics, but advanced financial reporting may require reviewed custom/Community add-ons.

## Required human approvals before production

Accounting domain owner signs off flows and reports; security owner approves threat model and key management; operations approves tested backup/restore and monitoring; business owner accepts offline/online restrictions; production deployment has a separate explicit approval.
