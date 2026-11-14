{
    "name": "NASQO Admin Identity",
    "version": "19.0.1.0.0",
    "summary": "NASQO identity for the administration interface",
    "author": "NASQO",
    "license": "LGPL-3",
    "depends": ["web", "base_setup", "website"],
    "data": ["views/branding.xml", "views/settings.xml"],
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
