from odoo.addons.web.controllers.webmanifest import WebManifest


class NasqoWebManifest(WebManifest):
    def _get_webmanifest(self):
        manifest = super()._get_webmanifest()
        manifest.update({
            "name": "نسقو برو | NASQO PRO",
            "short_name": "NASQO PRO",
            "background_color": "#123b42",
            "theme_color": "#123b42",
            "icons": [{
                "src": f"/nasqo_backend_branding/static/img/icon-{size}.png",
                "sizes": f"{size}x{size}",
                "type": "image/png",
            } for size in (192, 512)],
        })
        return manifest

    def _icon_path(self):
        return "nasqo_backend_branding/static/img/icon-192.png"
