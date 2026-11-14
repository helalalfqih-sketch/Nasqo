{
    "name": "NASQO PRO Admin Identity",
    "version": "19.0.1.1.0",
    "summary": "NASQO identity for the administration interface",
    "author": "NASQO",
    "license": "LGPL-3",
    "depends": ["web", "base_setup", "website", "mail"],
    "data": ["views/branding.xml", "views/settings.xml", "views/communications.xml"],
    "assets": {
        "web.assets_backend": [
            "nasqo_backend_branding/static/src/js/branding.js",
            "nasqo_backend_branding/static/src/xml/branding.xml",
            "nasqo_backend_branding/static/src/css/backend.css",
        ],
        "web.assets_frontend": [
            "nasqo_backend_branding/static/src/css/login.css",
        ],
    },
    "installable": True,
    "application": False,
}
