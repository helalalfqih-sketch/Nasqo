{
    "name": "NASQO PRO WhatsApp Connection Preview",
    "version": "19.0.1.1.0",
    "summary": "Isolated QR and WhatsApp connection status demonstration only",
    "author": "NASQO",
    "license": "LGPL-3",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "data/demo_session.xml",
        "views/session_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "nasqo_waha_qr_preview/static/src/scss/qr_mobile.scss",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
