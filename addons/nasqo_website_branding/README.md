# NASQO Website Identity
Odoo 19 additive public storefront identity. Depends on the existing NASQO backend and
storefront modules, and reuses the existing logo/icon assets. No original core edits.

Shared logo/favicon, teal/gold palette, Arabic footer and page titles; existing navigation
and routes remain intact. Default fake contact data and dummy footer links are removed.
A real configured company email enables the existing native contact form; no recipient
is invented and no mail is sent by this module or its verification script.
Known default/sample terms are replaced ONLY in presentation with a pending-content
notice; custom terms and all company/customer records are preserved.
Store-preparation notices remain; this is not payment/shipping readiness certification.

Rollback: standard authenticated uninstall of ONLY nasqo_website_branding, restart Odoo
and refresh assets. Do not restore a full database over independent live activity.
