# Storefront design verification — 2026-11-14

Scope: the new static NASQO storefront concept. No Odoo addon, live Shopify
theme, ERP configuration, user permission, database, or customer record changed.

## Source checks

| Check | Result | Evidence / limitation |
| --- | --- | --- |
| JavaScript syntax | PASS | `node --check dist/app.js` after the final interaction edits |
| Static document references | PASS | Python HTMLParser verified local src/href targets on all three HTML pages |
| Original SVGs | PASS | ElementTree parsed all nine SVGs: eight product drawings and one mark |
| Application network contract | PASS | Source check found no fetch, XMLHttpRequest, WebSocket, sendBeacon, or HTTP URL in app.js; all UI assets are local |
| Hosting identity | PASS | `.openai/hosting.json` matches project `appgprj_6af8ad82d2ec8191bf036d54a829eedd`, static directory `dist` |
| Font attribution | PASS | Three local Noto fonts accompanied by `assets/FONT_LICENSE.txt` |

The network source check is not an exhaustive penetration test, dependency
audit, or browser traffic capture. The review guide links official documentation;
those links navigate only when clicked.

## Actual Chrome interaction checks

| Case | Final status | Observed result |
| --- | --- | --- |
| Arabic search | PASS | سماعات gives one product; unknown text gives an empty state; reset restores eight |
| Category | PASS | المكتب gives two products |
| Price sort | PASS | Ascending order starts at حامل هاتف مكتبي 4,900 and ends at سماعات هدوء 24,500 |
| Favorites | PASS | Saving headphones and opening favorites shows that product |
| Stock zero | PASS | Clock add button is disabled |
| Variant and quantity | PASS | Two olive headphones appear as زيتي, quantity 2, line total 49,000 |
| Mixed subtotal | PASS | Two headphones + one bottle = 55,500 |
| Quantity cap | PASS | Headphones cannot exceed four across the cart; increment becomes disabled |
| Persistence | PASS | Reload retains the cart and 55,500 subtotal |
| Delivery | PASS | 1,500 fee gives 57,000 total |
| Pickup | PASS | Zero fee restores 55,500 |
| Bank option | PASS | Explicit preview-only message with no bank details |
| Finish preview | PASS | Success states no order/payment was sent; local cart becomes empty |
| Empty cart after return | PASS after repair | Immediate post-navigation check initially failed; a settled retry passed. Section scrolling was then made immediate; the same return/open sequence passed on the final source |
| Keyboard modal boundaries | PASS after repair | Initial Shift+Tab containment check failed. Added explicit boundary handling; Shift+Tab from the close button then focused the last dialog control |
| Escape and restored focus | PASS | Dialog closes; focus returns to the mobile cart button and desktop account opener |
| Buyer account example | PASS | Explicit synthetic `NQ-DEMO-104` example displayed; no real authentication implied |
| Mobile search/cart | PASS | Bottle search yields one product; add and mobile cart show 6,500 |
| Main desktop layout/assets | PASS | At browser width 1363, document scroll width 1348; all rendered images loaded |
| Responsive widths | PASS with scope limit | Frames 360/390/768: document client/scroll widths respectively 345/345, 375/375, 753/753 (15px desktop scrollbar). No document horizontal overflow |
| Mobile cart width | PASS | Client and scroll widths both 311 at the 360 frame |
| Page console error query | PASS with scope limit | Query filtered for preview origin returned no error; browser-extension metadata errors unrelated to this source were present in unfiltered logs |

Browser checks used the managed Sites preview and the documented CUA browser.
Responsive checks used real browser iframes with constrained CSS viewports, not
physical phones or mobile browser emulation. Internal screenshots were inspected
for layout; they contain synthetic data only and were not added to Git.

## Explicitly not certified

| Check | Status | Reason |
| --- | --- | --- |
| Odoo install/upgrade of this design | BLOCKED / not attempted | This deliverable is a static design concept; no new Odoo module implementation |
| Real checkout, taxes, currencies, stock and payment | BLOCKED | No application backend or payment provider connected |
| M1/M2 isolation and RBAC acceptance | BLOCKED | Existing gates remain; prototype UI checks cannot certify tenant isolation |
| Physical iOS/Android, screen reader, WCAG, Lighthouse | NOT RUN | No such result collected in this round |
| Live Shopify and ERP deployment | NOT RUN | Outside this selected design task |

## Reproduction

The separate Sites source contains `dist/index.html`, `dist/style.css`,
`dist/app.js`, `dist/design-notes.html`, `dist/responsive-preview.html`, local
assets and its hosting manifest. It is buildless; no npm install/build required.
Use the hosted private preview or `sites-preview start <checkout>` in the managed
environment. In another environment any ordinary local static server suffices.
Repeat the table's user actions through the page controls. No browser session,
authentication token, live customer data, or external API key is required.
