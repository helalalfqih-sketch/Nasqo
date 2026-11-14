from odoo import models
from ..branding import public_contact, has_custom_terms, branded_metadata


class Website(models.Model):
    _inherit = "website"

    def _nasqo_public_contact(self):
        self.ensure_one()
        return public_contact(self.company_id.phone, self.company_id.email)

    def _nasqo_has_custom_terms(self, company):
        return has_custom_terms(company.invoice_terms_html)

    def _nasqo_metadata(self, metadata, title):
        self.ensure_one()
        return branded_metadata(metadata, title, self.get_base_url(), self.id)
