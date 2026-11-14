"""Session-only admin UI; never sends messages or stores QR."""
import html

from odoo import http
from odoo.http import request

from .waha_client import (
    NoQR, NoSession, WahaUnavailable, get_qr_png, get_session_status,
)


HEADERS = [
    ("Cache-Control", "private, no-store, max-age=0"),
    ("Pragma", "no-cache"),
    ("Referrer-Policy", "no-referrer"),
    ("X-Content-Type-Options", "nosniff"),
    ("X-Frame-Options", "DENY"),
    ("Content-Security-Policy",
     "default-src 'none'; img-src 'self'; style-src 'unsafe-inline'; "
     "base-uri 'none'; form-action 'none'; frame-ancestors 'none'"),
]
STATES_AR = {
    "STOPPED": "متوقفة",
    "STARTING": "جارٍ تشغيل الجلسة",
    "SCAN_QR_CODE": "بانتظار مسح QR",
    "WORKING": "متصل",
    "FAILED": "فشل الاتصال",
    "PASSKEY_REQUIRED": "يلزم مفتاح مرور",
    "PASSKEY_CONFIRMATION_REQUIRED": "يلزم تأكيد مفتاح المرور",
    "UNKNOWN": "حالة غير معروفة",
}


def _denied():
    return request.make_response(
        "Forbidden", status=403,
        headers=HEADERS + [("Content-Type", "text/plain; charset=utf-8")],
    )


class NasqoWahaLive(http.Controller):
    @http.route("/nasqo/whatsapp/live", type="http", auth="user",
                methods=["GET"], csrf=False, sitemap=False)
    def live(self, **kw):
        if not request.env.user.has_group("base.group_system"):
            return _denied()
        try:
            status = get_session_status()
            text = STATES_AR[status]
        except NoSession:
            status = "MISSING"
            text = "لا توجد جلسة WAHA حقيقية باسم nasqo-primary. لا يمكن عرض QR قبل إنشاء الجلسة من لوحة WAHA الموثقة."
        except WahaUnavailable:
            status = "UNAVAILABLE"
            text = "تعذر الاتصال الآمن بخدمة WAHA. تحقق من اتصال Docker والملف السري."
        qr = (
            '<img src="/nasqo/whatsapp/qr" width="260" height="260" '
            'alt="رمز ربط واتساب حقيقي متجدد" />'
            '<p>رمز QR حقيقي ومتغير؛ افتح تحديث الحالة للحصول على رمز جديد.</p>'
            if status == "SCAN_QR_CODE" else ""
        )
        body = """<!doctype html><html lang="ar" dir="rtl"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>واتساب نسقو — الاتصال الحقيقي</title>
<style>body{font-family:system-ui,Tahoma,sans-serif;background:#f5f7f8;color:#1d3131;margin:0;padding:20px}
main{max-width:650px;margin:auto;background:white;padding:24px;border-radius:16px;border:1px solid #dce5e5}
h1{font-size:1.5rem}.flag{padding:12px;background:#e9f3f3;border-radius:8px}
a{display:inline-block;margin:8px 0;padding:12px;background:#14675a;color:white;text-decoration:none;border-radius:8px}
img{display:block;max-width:100%;height:auto;margin:16px auto}small{color:#566}
</style></head><body><main><h1>واتساب نسقو — اتصال WAHA الحقيقي</h1>
<p class="flag">الحالة: <strong>STATUS</strong></p>
<p>DETAILS</p>
QR_PLACEHOLDER
<a href="/nasqo/whatsapp/live">تحديث الحالة وQR</a>
<a href="/odoo/apps">العودة إلى تطبيقات نسقو</a>
<p><small>للمسؤول فقط. قراءة حالة الجلسة وعرض QR، دون إرسال رسائل أو تخزين بيانات QR.</small></p>
</main></body></html>"""
        body = (
            body.replace("STATUS", html.escape(text))
                .replace("DETAILS", html.escape("الجلسة: nasqo-primary"))
                .replace("QR_PLACEHOLDER", qr)
        )
        return request.make_response(body, headers=HEADERS + [
            ("Content-Type", "text/html; charset=utf-8"),
        ])

    @http.route("/nasqo/whatsapp/qr", type="http", auth="user",
                methods=["GET"], csrf=False, sitemap=False)
    def qr(self, **kw):
        if not request.env.user.has_group("base.group_system"):
            return _denied()
        try:
            if get_session_status() != "SCAN_QR_CODE":
                raise NoQR("Session is not awaiting QR")
            content = get_qr_png()
        except (NoSession, NoQR):
            return request.make_response(
                "QR is not available", status=404,
                headers=HEADERS + [("Content-Type", "text/plain; charset=utf-8")],
            )
        except WahaUnavailable:
            return request.make_response(
                "WAHA unavailable", status=503,
                headers=HEADERS + [("Content-Type", "text/plain; charset=utf-8")],
            )
        return request.make_response(
            content, headers=HEADERS + [("Content-Type", "image/png")],
        )
