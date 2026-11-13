# M3–M8 backlog — no implementation in this round

Every item needs a small reviewed PR, synthetic fixtures, updated Handoff and
recorded runtime evidence. No production launch or merge is authorized by CI.
See [the detailed Arabic phase plan](PHASE_PLAN_M3_M8.md) for proposed PR scope,
standard models, financial invariants, test fixtures and open decisions.

| Order | Work | Standard base / custom only if needed | Gate / acceptance |
|---|---|---|---|
| 1 / P0 | Close pilot gaps: verified merchant owner, authenticated control API, MFA/support roles, durable queue | Registry contract evolves into control-plane PostgreSQL; retain idempotency and store identity | AT-001, full AT-006/030; ownership and failure handling before public creation |
| 2 / M3 P0 | Arabic mobile catalog/cart/checkout, YER configuration, COD/manual bank transfer and delivery | website_sale, sale_management, delivery, payment; nasqo_store UI inheritance only | AT-007–010; one E2E order, no false payment, retries safe, RTL visual/accessibility review |
| 3 / M4 P0-F | Execute Community accounting gap matrix and define ledger/partner distinction | account/account_payment; compare required reports and models first | AT-032; approve accounting owner, sign convention, tax/localization and opening counterpart |
| 4 / M4 P0-F | Opening wizard, cash/bank vouchers and transfers, immutable operation key and reversal | account.move, account.payment; nasqo_finance only for proven gaps | AT-011–015/031, balanced debit/credit, duplicate/concurrent submission, authorized reversal |
| 5 / M4 P0-F | Statements and dated FX buy/sell with decimal rounding and gains/losses | account.move.line, res.currency/rate; nasqo_fx and nasqo_reports as justified | AT-016–019; known numerical cases, opening/running balance, quote/base and rounding approved |
| 6 / M4 P1 | Credit limits and approved override log | res.partner; nasqo_partner_credit after warning/block policy | AT-020, concurrent sales cannot exceed chosen policy |
| 7 / M5 P1 | Suppliers, purchase receipts, vendor bills, returns | purchase, purchase_stock, stock, stock_account | AT-013/021; matched document chain, no duplicated movement |
| 8 / M5 P1 | Warehouse transfers/UoM/valuation, import preview and RTL reports | stock.picking/move, product, standard QWeb; UI/report extensions only | AT-021–024; quantities conserved, rejected bad rows, consistent totals and PDF rendering |
| 9 / M6 P0 paid | Trial, entitlements, plan renewal, platform invoices, grace and export | Separate control plane, never parallel store accounting tables | AT-027; failed/late/duplicate billing events, no tenant deletion, policy agreed |
| 10 / M7 P2 | Official SMS/WhatsApp provider, consent modes, templates, throttled retries | mail plus nasqo_notifications adapter | AT-025/026; zero outbound with no-send, opt-in before any send, secret vault |
| 11 / M8 launch | TLS/DNS ownership, limits, support access audit, off-host encrypted backups, monitoring | Infrastructure, secret manager, pinned image digests, vulnerability scans and incident runbooks | Full security review; 100% applicable P0, RPO/RTO measured, independent restore and rollback drill |

## Decisions required before their dependent work

1. Accounting: distinguish partner accounts from general ledger; define له/عليه,
   opening counterpart, posting/lock dates, reversal and approval authority.
2. FX: base/quote, source and date of rates, precision, buy/sell spread and FX
   difference accounts. No rate inferred from screenshots or prices.
3. Store: approved payment/shipping options and manual settlement authority;
   local tax/invoice requirements reviewed by a qualified local accountant.
4. SaaS: pricing/limits, notification/grace/export policy and retention; backup
   key custody, destination, recovery objectives and support authorization.

All requirements use original NASQO implementation. No competitor source code,
UI assets, pricing or assumed internal accounting rules are imported.
