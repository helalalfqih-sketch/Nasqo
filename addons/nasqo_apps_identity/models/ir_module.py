"""Presentation-only app catalogue formatting. Original metadata remains unchanged."""
import io
import re

from docutils.core import publish_parts

from odoo import api, fields, models, tools


_ANCHOR = re.compile(r"<a\b[^>]*>(.*?)</a\s*>", re.IGNORECASE | re.DOTALL)
_HTML_TAG = re.compile(r"</?(?:a|p|br|b|i|em|strong|span|div|ul|ol|li|h[1-6])\b[^>]*>", re.I)
_OD_MARK = re.compile(r"(?<![\w])Odoo(?![\w])", re.IGNORECASE)
_OD_AR = re.compile(r"أودو|اودو")
_OD_LINK = re.compile(r"https?://(?:www[.])?(?:odoo[.]com|apps[.]odoo[.]com)[^ ]*", re.I)


def clean_description(raw):
    """Clean legacy HTML embedded in RST without executing markup or changing source data."""
    if not raw:
        return ""
    text = _ANCHOR.sub(lambda match: match.group(1).strip(), raw)
    text = _HTML_TAG.sub("", text)
    text = _OD_LINK.sub("", text)
    # User-facing platform nomenclature only: source authorship remains intact.
    text = _OD_MARK.sub("نسقو برو", text)
    text = _OD_AR.sub("نسقو برو", text)
    # Remove whitespace-only empty links caused by raw HTML stripping.
    text = re.sub(r"\(\s*\)", "", text)
    return text


class IrModuleModule(models.Model):
    _inherit = "ir.module.module"

    nasqo_description_html = fields.Html(
        string="وصف التطبيق", compute="_compute_nasqo_description_html", sanitize=True
    )
    nasqo_summary = fields.Char(
        string="ملخص التطبيق", compute="_compute_nasqo_summary"
    )

    @api.depends("summary")
    def _compute_nasqo_summary(self):
        for module in self:
            module.nasqo_summary = clean_description(module.summary or "")

    @api.depends("description", "name")
    def _compute_nasqo_description_html(self):
        for module in self:
            raw = clean_description(module.description or "")
            if not raw.strip():
                module.nasqo_description_html = module.description_html or ""
                continue
            warnings = io.StringIO()
            try:
                rendered = publish_parts(
                    source=raw,
                    writer_name="html",
                    settings_overrides={
                        "embed_stylesheet": False,
                        "doctitle_xform": False,
                        "file_insertion_enabled": False,
                        "raw_enabled": False,
                        "report_level": 5,
                        "halt_level": 6,
                        "warning_stream": warnings,
                    },
                )["html_body"]
            except Exception:
                rendered = tools.html_escape(raw).replace("\n", "<br/>")
            module.nasqo_description_html = tools.html_sanitize(rendered)
