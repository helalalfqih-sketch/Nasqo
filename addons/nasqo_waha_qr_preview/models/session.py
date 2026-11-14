"""Pure in-database WAHA connection simulation; no WAHA API or real QR."""
from odoo import api, fields, models
from odoo.exceptions import UserError

DEMO_SESSION = "nasqo-waha-synthetic"


class WahaDemoSession(models.Model):
    _name = "nasqo.waha.preview.session"
    _description = "NASQO PRO WhatsApp Connection Preview - No Real Account"
    _rec_name = "name"

    _unique_name = models.Constraint(
        "UNIQUE(name)",
        "There can be only one connection demo with this name.",
    )

    name = fields.Char(readonly=True, required=True, default=DEMO_SESSION)
    connection_state = fields.Selection(
        [
            ("stopped", "غير متصل"),
            ("scan_qr", "بانتظار مسح QR (محاكاة)"),
            ("working", "متصل (محاكاة)"),
            ("failed", "فشل (محاكاة)"),
        ],
        required=True, default="stopped", readonly=True,
    )
    demo_warning = fields.Html(
        compute="_compute_demo_warning", string="تنبيه المحاكاة", sanitize=True
    )
    qr_preview = fields.Html(
        compute="_compute_qr_preview", string="رمز QR تجريبي", sanitize=True
    )
    status_panel = fields.Html(
        compute="_compute_status_panel", string="حالة الاتصال التجريبية", sanitize=True
    )
    last_simulated_at = fields.Datetime(readonly=True)
    connection_note = fields.Char(readonly=True)

    @api.depends("connection_state")
    def _compute_status_panel(self):
        states = {
            "stopped": ("غير متصل", "لم يتم إنشاء جلسة واتساب حقيقية.", "secondary"),
            "scan_qr": ("بانتظار مسح QR — محاكاة", "الرمز المعروض اختباري وغير صالح للربط.", "warning"),
            "working": ("متصل تجريبيًا", "نجاح افتراضي فقط؛ لا يوجد حساب واتساب متصل.", "success"),
            "failed": ("فشل الاتصال — محاكاة", "هذا فشل تجريبي لا يعكس حالة خادم WAHA.", "danger"),
        }
        for record in self:
            title, details, tone = states.get(record.connection_state, states["stopped"])
            record.status_panel = (
                '<section class="nasqo-waha-status-card nasqo-waha-status-'
                + tone + '" dir="rtl" role="status" aria-live="polite">'
                '<span class="nasqo-waha-status-caption">حالة الربط في المختبر</span>'
                '<strong class="nasqo-waha-status-title">' + title + '</strong>'
                '<span class="nasqo-waha-status-details">' + details + '</span>'
                '</section>'
            )

    def _compute_demo_warning(self):
        for record in self:
            record.demo_warning = (
                '<div class="alert alert-warning nasqo-waha-demo-alert" role="alert" dir="rtl">'
                '<strong>محاكاة فقط — ليست واتساب حقيقيًا.</strong> '
                'الأزرار والرمز تجريبية، ولا تتصل بالخدمة أو بأجهزة واتساب '
                'ولا ترسل أو تستقبل أي رسائل حقيقية.</div>'
            )

    @api.depends("connection_state")
    def _compute_qr_preview(self):
        for record in self:
            if record.connection_state == "scan_qr":
                record.qr_preview = (
                    '<section class="nasqo-waha-qr-card" dir="rtl">'
                    '<h3>رمز QR للتجربة فقط</h3>'
                    '<div class="nasqo-waha-qr-image">'
                    '<img src="/nasqo_waha_qr_preview/static/img/not-a-whatsapp-qr.png" '
                    'alt="رمز نسقو برو تجريبي غير صالح لمسح واتساب أو ربط أي حساب" '
                    'width="230" height="230" loading="lazy" />'
                    '</div>'
                    '<p class="nasqo-waha-qr-label"><strong>غير صالح للربط</strong>'
                    ' — هذا الرمز يحتوي نصًا اصطناعيًا ثابتًا وليس بيانات مصادقة.</p>'
                    '</section>'
                )
            else:
                record.qr_preview = (
                    '<div class="nasqo-waha-qr-placeholder" dir="rtl">'
                    '<strong>لا يوجد رمز ربط حقيقي.</strong>'
                    '<p>اختر «محاكاة انتظار QR» لعرض رمز تجريبي فقط.</p>'
                    '</div>'
                )

    def _only_admin(self):
        if not self.env.user.has_group("base.group_system"):
            raise UserError("صلاحية محاكاة الاتصال متاحة للمسؤول فقط.")
        if any(rec.name != DEMO_SESSION for rec in self):
            raise UserError("هذا التطبيق مخصص للجلسة التجريبية فقط.")

    def _set_demo_state(self, state, note):
        self._only_admin()
        self.write({
            "connection_state": state,
            "connection_note": note,
            "last_simulated_at": fields.Datetime.now(),
        })
        return True

    def action_show_mock_qr(self):
        return self._set_demo_state("scan_qr", "رمز ثابت اصطناعي — لا تستخدمه لواتساب")

    def action_mock_connected(self):
        for record in self:
            if record.connection_state != "scan_qr":
                raise UserError("اعرض رمز الاختبار أولًا قبل محاكاة الاتصال.")
        return self._set_demo_state("working", "اتصال تجريبي فقط")

    def action_mock_failure(self):
        return self._set_demo_state("failed", "فشل اصطناعي للاختبار")

    def action_reset_mock(self):
        return self._set_demo_state("stopped", "تمت إعادة ضبط المحاكاة")
