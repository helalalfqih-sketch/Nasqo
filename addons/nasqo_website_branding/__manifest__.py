{
    "name": "NASQO PRO Website Identity",
    "version": "19.0.1.1.0",
    "summary": "Arabic NASQO identity for the public storefront",
    "author": "NASQO",
    "license": "LGPL-3",
    "depends": ["nasqo_backend_branding", "nasqo_storefront", "website_sale"],
    "data": ["views/layout.xml", "views/pages.xml"],
    "assets": {
        "web.assets_frontend": [
            "nasqo_website_branding/static/src/css/website.css",
        ],
    },
    "installable": True,
    "application": False,
}
