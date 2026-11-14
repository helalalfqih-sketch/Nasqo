# NASQO PRO identity — 2026-11-14

## Current state and scope

The user requested **نسقو برو** as the customer-facing identity of the existing
site. Seven presentation addons were already installed outside the server Git
checkout. This branch captures that existing source in a baseline commit and
then applies the PRO change. It does not advance financial, inventory,
subscription, provisioning or access-control milestones.

The tested runtime is the dated official Community 19 image `19.0-20261112`.
The foundation's pinned source SHA in `upstream.json` is unchanged. Results on
the deployed image are not a claim that this branding diff has passed the
foundation's separate pinned-source CI environment.

## Implementation

Twenty-two deployment source files changed across these seven addons:

| Addon | Display changes |
| --- | --- |
| `nasqo_backend_branding` | Login, page titles, launcher, user menu, About, generic dialogs, expired sessions, PWA/offline, settings, email notification footers and report HTML titles |
| `nasqo_website_branding` | Header/footer, common pages, metadata and accessible labels |
| `nasqo_storefront` | Homepage and storefront labels |
| `nasqo_apps_identity` | Application descriptions and administration labels |
| `nasqo_whatsapp_center` | Menu title |
| `nasqo_waha_qr_preview` | Existing preview labels |
| `nasqo_waha_live_view` | Existing live status page labels |

Versions are `19.0.1.1.0`. The backend addon explicitly depends on `mail` and
adds `views/communications.xml`. Existing NASQO icons and palette were reused.
Odoo core, routes, model/XML identifiers, standard business models, access
checks, original authorship and LGPL notices remain intact. Original component
attribution is available in the expandable licensing section and module source.
No unavailable licensed feature was enabled by this change.

The live environment also received these scoped configuration changes:

- Website display name: `نسقو برو | NASQO PRO`.
- `web.web_app_name`: `نسقو برو`.
- The existing system bot's `Nasqo` display name and icon now use the PRO identity.
- The website-specific `nasqo_website_branding.layout_identity` override retained
  its custom links and translated content. Its explicit Odoo Facebook embed was
  removed. Other social links were kept; their destination configuration was not
  changed or certified by this work.

## Deployment and actual verification

The pilot uses its own database and filestore. All seven modules were upgraded
there before applying the same 22 source files to the requested live site.
Only the Odoo app service was stopped; the database, other applications and
volumes remained in place. A local database/filestore backup was taken while
the app was stopped, validated with archive checks and SHA-256 checksums.
Backup marker: `20261114T153055Z`. No restore or offsite-encryption claim is made.

| Check | Actual result |
| --- | --- |
| Seven addon upgrades, pilot and live | PASS |
| Authenticated HTTP, native login/CSRF, assets, menus, settings, Apps and PWA | PASS — 35 checks on each environment |
| Public home/shop/cart/contact/terms/login/404, identity, CSS and metadata | PASS — 9 tests on each environment |
| Titles, counters, account actions, dialog defaults and error meanings | PASS — JavaScript contracts against installed Odoo utilities, with dialog stubs |
| Two email notification layouts | PASS — QWeb rendering with synthetic content and unsubscribe link preserved; no email sent |
| Report layout and preview layout | PASS — rendered HTML titles/content; no actual PDF generated |
| Business-data preservation | PASS — hashes and counts of 12 tables unchanged, excluding the intentionally renamed system bot |
| Customized footer | PASS — all stored languages/pending translations retained; custom anchor attributes preserved; Odoo promotional embed removed |
| `web_tour.interactive` descriptor, normal and `debug=assets` | PASS — HTTP 200, valid JSON array and referenced asset responses |
| Browser visual inspection | PASS — public homepage/footer and hydrated login form; no authenticated interactive backend session used |
| Repository unit/static checks | PASS — 8 tests; these are not a substitute for the runtime checks above |
| Full PDF/mobile/business workflow coverage | NOT RUN in this branding task |

The existing GitHub Actions workflows still verify foundation installation and
static checks; they do not yet execute this full branding suite. This limitation
must remain visible in review rather than presenting a static green check as
functional coverage.

## Problems encountered and resolved

The first pilot upgrade failed because the new public XML source was mode 0600,
unreadable to the Odoo container user. Only that public source was changed to
0644; the retry and subsequent upgrades passed. Private files stayed private.

A guarded live setting update initially rejected the different existing website
name. The verified value was reviewed before retrying; the failed transaction
did not commit.

Ordinary `arch_db.write` synchronized translation structure and removed pending
translation markup. The guarded pre-update snapshot was used to restore every
translation through the ORM field cache, then template caches were invalidated
with `env.registry.clear_cache('templates')` and signaled. The final patch removed
only the recognized Odoo Facebook widget and preserved other links. Original
and final custom view data stay in protected server evidence, never in Git.

One rendering test initially assumed the pilot's bot name on the live system.
The live system already used `Nasqo`; it was updated to `نسقو برو`. The assertion
now accepts the intended PRO names, and the final rendering run passed.

## Reproduction and recovery

`scripts/branding/verify-admin-pro.py` runs inside the intended Odoo container.
It uses the existing `PILOT_ADMIN_PASSWORD` or `STAGE_ODOO_ADMIN_PASSWORD`
environment variable and never prints its value, cookies or response bodies.
`NASQO_TEST_BASE_URL` selects the intended HTTP origin. Never copy real credentials
into GitHub Actions. The public verifier submits no forms.

`test-admin-pro.cjs` runs on a Docker host with Node; set `NASQO_TEST_CONTAINER`
to the intended container. `test-template-rendering.py` runs through an Odoo
shell; synthetic wrapper views are rolled back and no messages are sent.

For rollback, first inspect current file hashes and concurrent edits. Restore
only the saved presentation source/configuration affected by this change,
upgrade only the intended addons and restart only the app if required. Preserve
newer user edits and translated custom views. Do not restore a whole old database
over independent activity. Standard module uninstall remains a broader, separately
testable fallback, not an action performed here.

## Handoff

Review branch: `feat/nasqo-pro-identity`, based on foundation commit `ca09ad2`.
Draft review: [PR #6](https://github.com/helalalfqih-sketch/Nasqo/pull/6), with
baseline commit `519a65b` and implementation commit `c2bf1f0`.
The original server checkout and unrelated local work remain unchanged. PR #1
is not merged. Protected deployment evidence is under the server's
`docs/nasqo-pro-branding-20261114/`; its logs, settings snapshots, database
content, filestore and backups are deliberately excluded from this repository.

Next work is review of this identity change and role-specific visual checks.
Actual PDF branding, full mobile flows and automation of the branding suite in
isolated CI remain follow-ups; this change does not establish launch readiness.
