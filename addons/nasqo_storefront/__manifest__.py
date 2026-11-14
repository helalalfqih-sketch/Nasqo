{
    "name": "NASQO Arabic Storefront Pilot",
    "version": "19.0.1.0.0",
    "summary": "Arabic RTL mobile-friendly storefront proof-of-concept",
    "author": "NASQO",
    "category": "Website/eCommerce",
    "license": "LGPL-3",
    "depends": ["website_sale"],
    "data": ["views/storefront.xml"],
    "assets": {
        "web.assets_frontend": [
            "nasqo_storefront/static/src/css/storefront.css",
            "nasqo_storefront/static/src/js/rtl.js",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
