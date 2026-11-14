# NASQO Admin Identity
Server-only additive Odoo 19 module; no core source edits and no customer/company records updated.

## Scope
Backend title and favicon, application launcher, NASQO palette, user menu, About section,
generic dialogs, session expiration, unavailable-feature dialogs, PWA/offline identity,
and shared login page. Original authentication, CSRF, access checks and business routes remain.
Open-source component attribution is retained in the expandable license section and upstream source.
Technical module names, traceback identifiers, app documentation and third-party descriptions
are not rewritten. The public storefront, outgoing email and business PDF identity are separate work.

## Recovery
Uninstall this module using the standard authenticated administrator module action,
then restart the Odoo application only and refresh assets. No data migration or restore needed.
Test this path on the isolated pilot before production. Keep the source directory until
the uninstall is complete. Never restore an old full database over new business activity.
