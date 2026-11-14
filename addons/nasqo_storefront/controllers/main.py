"""Public NASQO storefront landing page. No customer data is fetched."""
from odoo import http
from odoo.http import request

class NasqoStorefront(http.Controller):
    @http.route("/nasqo", type="http", auth="public", website=True, sitemap=False, methods=["GET"])
    def homepage(self, **kwargs):
        products = request.env["product.template"].sudo().search(
            [("website_published", "=", True), ("sale_ok", "=", True)],
            order="id desc",
            limit=6,
        )
        return request.render("nasqo_storefront.homepage", {"products": products})
