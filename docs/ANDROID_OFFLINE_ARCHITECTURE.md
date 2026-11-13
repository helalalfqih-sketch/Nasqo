# ADR-0001 — NASQO Android Accounting: Offline-first architecture

**Status:** Proposed — design only, not implemented.  
**Target:** Odoo Community 19.0 (self-hosted), Android first, Arabic RTL, Flutter + encrypted SQLite.  
**Parent foundation:** chore/odoo19-ecommerce-foundation.  
**Scope:** MVP for one authorized company context on each device. Multi-company switching and offline sales across competing devices require separate acceptance tests.

## 1. Non-negotiable invariants

1. Odoo PostgreSQL and Odoo business methods are the authoritative system for posted invoices, accounting entries, customer balances, inventory and permissions.
2. Encrypted SQLite is the immediate source of data for the Android UI; it stores cached views and **unposted drafts**, never a second independent general ledger.
3. No official invoice number, posted journal entry, confirmed payment, inventory reservation, or fiscal receipt is created while offline. Local documents display **مسودة غير معتمدة**.
4. No double processing: a retry of an acknowledged operation must return the same result (effectively-once business effect, not guaranteed exactly-once network delivery).
5. Only the server can authenticate, authorize, validate, allocate official sequences, calculate final taxes and exchange rates, and decide whether an action may be posted.

## 2. Logical architecture

~~~text
Flutter Android (Arabic/RTL)
  Screens + Riverpod state
      |
  Repository layer (only reads/writes local data)
      +-- Encrypted SQLite (SQLCipher): catalog, drafts, synced snapshots,
      |   entity mappings, conflicts, outbox, cursor
      +-- Outbox transaction: local data change + pending operation atomically
      +-- Sync worker: push pending ops, pull deltas, retry/backoff
      |
      | HTTPS / TLS + short-lived user access token + device binding
      v
NASQO Sync Gateway (FastAPI or equivalent)
  OIDC authorization code + PKCE login, authz, rate limits, validation,
  audit, per-device revocation, restricted versioned endpoints
      |
      | Private authenticated service-to-service link; never a mobile key
      v
Odoo 19 add-on: nasqo_mobile_sync (new)
  Trusted identity mapping -> effective Odoo user / companies
  Access rights + record rules; business method validation; NO unsafe sudo
  Idempotency receipts, revision-ordered change log, conflict handling
  Uses standard account, sale, stock and res.partner business methods
      |
      v
Odoo ORM --> PostgreSQL (authoritative accounting and business records)
~~~

The gateway must not accept a client-supplied user_id/company_id as an authorization fact. It derives identity and allowed companies from validated credentials, and the Odoo add-on independently enforces rights and record rules. The gateway and Odoo are separate services for security isolation and independent API versioning; use internal network access and credential management. This gateway is a proposed component, not already deployed.

## 3. Technology choices

| Layer | Proposed choice | Notes |
| --- | --- | --- |
| Android | Flutter / Dart + Riverpod | Arabic RTL, predictable state and testability |
| Local persistence | SQLite + SQLCipher, e.g. sqflite_sqlcipher | Encrypted at rest; verify supported plugin versions, Android build and migration before locking |
| Database access | Explicit DAO/repository layer | Avoid coupling widgets to SQL; a Drift integration may be evaluated only after encryption compatibility testing |
| Key storage | Android Keystore | Random per-install database key; never embed key in code or plain preferences |
| Scheduler | Android WorkManager | Network constraints, exponential backoff; manual in-app sync always available because background runs are not immediate |
| Service | FastAPI (proposed) + OIDC Identity Provider | Public sync gateway, short-lived tokens and refresh rotation |
| Odoo | Custom module nasqo_mobile_sync | Constrained domain actions; no generic arbitrary model write from Android |
| Source updates | Pinned Odoo 19 commit | Reuse upstream.json and docs/UPDATES.md from foundation |

IMPORTANT: Odoo 19's legacy external /jsonrpc and /xmlrpc APIs are deprecated. Odoo's custom @route(type='jsonrpc') controllers are distinct and remain supported. Do not couple the Android app directly to generic external Odoo model APIs; the gateway must expose a narrow versioned contract and never embed a long-lived Odoo API key on a handset.

References:
- https://www.odoo.com/documentation/19.0/developer/reference/backend/http.html
- https://www.odoo.com/documentation/19.0/developer/reference/external_rpc_api.html
- https://developer.android.com/topic/architecture/data-layer/offline-first
- https://developer.android.com/develop/background-work/background-tasks/persistent
- https://pub.dev/packages/sqflite_sqlcipher
- https://pub.dev/packages/sqlcipher_flutter_libs (deprecated package; do not adopt)

## 4. Local SQLite schema (proposed)

- company_scopes(company_id, user_id, scope_version, last_checked_at, expires_at)
- partners(local_uuid, server_id nullable, company_id, name, base_revision, updated_at, sync_state)
- products(server_id, company_id, sku, name, uom, currency_id, price_string, active, revision)
- stock_snapshots(product_id, warehouse_id, quantity_string, observed_at, revision) — last known only, NOT stock reservation
- invoice_drafts(local_uuid, server_id nullable, company_id, partner_ref, currency_id, state, base_revision, server_totals_json nullable, created_at)
- invoice_draft_lines(local_uuid, invoice_uuid, product_ref, qty_string, unit_price_string, tax_ids_json)
- payment_intents(local_uuid, invoice_ref, amount_string, currency_id, state) — not an Odoo-confirmed payment
- outbox(operation_id UUID, entity_type, local_uuid, company_id, action, payload_json, base_revision, dependencies_json, payload_hash, attempt_count, next_attempt_at, state, last_error)
- entity_id_map(entity_type, local_uuid, server_id, company_id)
- sync_cursors(company_id, scope_version, cursor, updated_at)
- conflicts(operation_id, entity_ref, server_version_json, local_version_json, resolution, recorded_at)
- deletion_tombstones(entity_type, server_id, revision)
- schema_meta(schema_version, encrypted_key_version)

Store monetary quantities as exact decimal strings or integer minor units with currency-specific rounding rules; never persist accounting amounts as binary floating-point and assume correctness. Server recomputes taxes and final totals. SQLite migrations must be backward-safe for pending drafts.

## 5. Minimal versioned API contract (DESIGN — not implemented)

- POST /api/v1/devices/register — authorized enrollment and device public identity
- GET /api/v1/bootstrap — scoped initial catalog/partners/currency/taxes + initial cursor
- POST /api/v1/sync/push — ordered batch of up to a bounded number of operations, per-operation result
- GET /api/v1/sync/pull?cursor=... — ordered incremental changes, tombstones, pagination, scope changes
- GET /api/v1/sync/status — per-device health and reconciliation summary
- POST /api/v1/devices/revoke — authorized device revocation

Example conceptual push request:

~~~json
{
  "device_id": "<registered device ID>",
  "operations": [
    {
      "operation_id": "<UUID>",
      "action": "invoice_draft.create",
      "entity_id": "<local UUID>",
      "base_revision": null,
      "depends_on": [],
      "payload": {
        "partner_ref": "<server ID or resolvable local UUID>",
        "lines": [
          {"product_ref": "<server product ID>", "qty": "2", "price_hint": "10.00"}
        ]
      }
    }
  ]
}
~~~

Example reply: each operation returns accepted/conflict/rejected/retryable, authoritative server_id, server_revision and authoritative totals if applicable. Returning the same idempotency key with the same payload must yield the same original business outcome; a different payload with that key is rejected.

Proposed actions are allowlisted domain commands (draft, update, submit-for-review), NOT arbitrary write operations on account.move or payment journals. Server-side permission and accounting validation apply to each command.

## 6. Synchronization algorithm

### Push
1. Save the draft update and outbox command in one local SQLite transaction. A UI response indicates saved locally, not posted in Odoo.
2. On reconnection or manual sync, authenticate, select authorized company, and send queued operations ordered by explicit dependencies and per-entity sequence.
3. Server verifies token/device/scope, then validates unique (company, device, operation_id) + payload hash.
4. In an Odoo transaction, server performs business validation, records the business result and idempotency receipt atomically. Retry returns the same receipt.
5. Apply acknowledged result and local_uuid-to-server_id mappings in one SQLite transaction. Do not discard unacknowledged work.
6. Conflicts are held for user resolution; retryable failures use capped exponential backoff with jitter.

### Pull
1. Request changes using per-company opaque cursor and current authorized scope; paginate with bounded batch sizes.
2. Server emits changes from a **commit-ordered** revision feed with deletions/tombstones. Generate revisions under a serialized per-scope transaction lock or equivalent commit-order mechanism; never assume write_date or an uncoordinated database sequence alone guarantees safe ordering.
3. Apply page contents, resolved server mappings and new cursor atomically to SQLite. Replaying a page must be harmless.
4. Invalidate/clear unauthorized cached scopes when access changes and the handset reconnects. Expired cursors trigger safe re-bootstrap without dropping unsent drafts.

### Conflict rules

| Condition | Rule |
| --- | --- |
| Same operation retried after timeout | Idempotent re-ack; no second invoice/payment |
| Partner metadata edited on two devices | Optimistic revision check; user review for collision |
| Price/tax/currency changed while offline | Recalculate on Odoo; show changed totals and request confirmation |
| Product inactive or insufficient stock | Reject/hold draft for correction; never assume last-known stock |
| Invoice already posted in Odoo | Never overwrite; create authorized adjustment/credit workflow |
| Remote delete or permissions revoked | Tombstone or lock local snapshot; stop unauthorized push |
| Customer payment intent | Keep pending until server validates and confirms; no local posted receipt |

## 7. Security model

- Interactive sign-in must be online first; OAuth2/OIDC Authorization Code + PKCE with short-lived access tokens, rotated refresh tokens and per-device revocation. Secrets and gateway service credentials stay SERVER-SIDE.
- Use encrypted SQLite + Android Keystore; protect sensitive screens, logs, backups and exported files. Forbid raw DB backup or ensure separately encrypted, approved backups. Test lost-device and reinstall scenarios.
- Offline unlock can use OS biometrics/PIN for an already authorized device, with an explicitly chosen maximum offline window. Remote revocation cannot erase an already-offline device instantly; it takes effect at next contact or local policy expiry.
- Every request verifies identity, company, record rights, rate limits, schema version, payload limits and business invariants. Keep Odoo service authentication internal, and avoid broad sudo.
- Store tamper-evident audit of device, operation UUID, effective actor, company, server timestamp, result and request hash without storing passwords/tokens/payment details in logs.
- Use TLS; ensure no cleartext traffic on Android; apply OS patching, secure config, dependency audit and threat-model review before production.
- Currency, journals, accounts, taxes and fiscal localization are configured on Odoo. Verify the legal invoice requirements in target jurisdiction before enabling fiscal documents.

## 8. MVP screens and behavior

1. Login/device enrollment (online only); profile, company, sync health.
2. Dashboard based on last synchronized data with freshness label.
3. Customers (read cached; create/edit drafts offline, subject to permission).
4. Products, prices and inventory snapshots (read cached, show last sync timestamp).
5. Draft sales invoices/quotes: add lines, save offline, queue changes, review updated server totals.
6. Pending operations and conflicts: retry, resolve, export diagnostic IDs, no destructive purge.
7. Invoice submission/official posting only after the server approves; reports reflect server-confirmed values only.

## 9. Non-functional acceptance criteria (targets, not verified)

- A lost acknowledgment plus 100 replays produces ONE business invoice (same idempotency key).
- 72-hour offline use preserves all saved drafts without corrupting SQLite across app restarts and device reboot; no claim of guaranteed remote revocation during full disconnection.
- Two devices editing a stale same invoice produce explicit conflict, not silent overwrite.
- Every pushed operation is scoped and permission checked in Odoo; no cross-company data leakage.
- Product/partner bootstrap and 1000+ queued operations tested under weak/limited network and storage pressure.
- App can resume after an interrupted SQLite schema migration without losing pending operations.
- Odoo server retains official transaction semantics. No production payment, invoice posting, stock reservation or live-mail testing until separate approval.

## 10. Existing NASQO baseline

The parent branch has an empty custom nasqo_store foundation, Odoo 19 pin, static tests and update policy. No mobile project, sync gateway, OAuth, SQLCipher runtime, integration test, production database, or deployed Odoo service has been verified. This ADR introduces **no running code** and authorizes no deployment.
