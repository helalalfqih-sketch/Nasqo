# AI_HANDOFF — NASQO Android Offline Accounting

## Status (2026-11-13)

Design **only**, with no Android app, gateway, Odoo sync module or deployment created by this design change. Repository baseline is **chore/odoo19-ecommerce-foundation**, not main. Existing foundation remains untouched.

## What / where / why

- docs/ANDROID_OFFLINE_ARCHITECTURE.md: ADR-0001, trusted sync boundary, encrypted SQLite, Odoo as accounting authority, idempotency, conflict rules and security.
- docs/ANDROID_IMPLEMENTATION_PLAN.md: MVP, phases, acceptance tests, repository layout, release gates and outstanding product decisions.
- This file: implementation handoff and verified limitations.

## Verified inputs

- Account repository: helalalfqih-sketch/Nasqo, foundation branch commit f327a120e8b9f6747150000da5130256931a24d4.
- Odoo 19 source pin recorded in upstream.json: 9cd6f090a8a21d9531c70ceec7f5c51271e24168.
- Existing module nasqo_store depends on website_sale and has no business features yet.
- Prior GitHub static foundation CI completed successfully on this foundation commit, but this does NOT test Android/Odoo runtime.
- Remote Desktop Commander 'شخصي' devices were offline in the last inspection; do not assert access to a running Odoo service.

## Tests for this change

Documentation only; no runtime tests performed and no service or branch merge. Validate links, review security assumptions and update ADR when implementation begins. Future implementation must add Odoo integration tests and Android SQLite encryption/migration tests.

## Risks and next steps

1. Decide accounting MVP and offline document legal status with business owner; treat all offline invoices as unposted.
2. Bring up an isolated Odoo 19 test database and confirm Community module coverage and country-specific accounting configuration.
3. Build security and sync idempotency test harness before the Android app.
4. Implement first vertical slice end to end in a separate feature branch; require review, tests and manual promotion.
5. No credentials, test customer exports or live payment keys in this public repository.

Do not silently merge into main or treat design approval as production authorization.
