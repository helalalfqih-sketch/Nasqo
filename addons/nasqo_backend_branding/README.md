# NASQO PRO Admin Identity
Additive Odoo Community 19 module; no core source edits or business-model replacements.

## Scope
Backend title and favicon, application launcher, NASQO palette, user menu, About section,
generic dialogs, session expiration, unavailable-feature dialogs, PWA/offline identity,
and shared login page. Version 19.0.1.1.0 adds the explicit `mail` dependency,
notification footers, report HTML fallback titles and website-information text.
Original authentication, CSRF, access checks and business routes remain.
Open-source component attribution is retained in the expandable license section and upstream source.
Technical module names, traceback identifiers, app documentation and third-party descriptions
are not rewritten. Outgoing mail was rendered with synthetic content, not sent.
Report HTML layouts were rendered; actual PDF generation was not tested.
The public storefront uses `nasqo_website_branding`.

Set `web.web_app_name` and the intended website display name separately after
reviewing the environment. Preserve customized translated views and existing
system-account identities; see `docs/NASQO_PRO_BRANDING.md` in the repository.

## Recovery
Uninstall this module using the standard authenticated administrator module action,
then restart the Odoo application only and refresh assets. No data migration or restore needed.
Test this path on the isolated pilot before production. Keep the source directory until
the uninstall is complete. Never restore an old full database over new business activity.
