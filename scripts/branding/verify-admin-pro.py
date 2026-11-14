"""Read-only HTTP/authentication checks. Run inside the intended Odoo container.
Passwords stay in its environment; never print credentials, cookies or response bodies.
"""
import os, json, re, sys, struct
import requests
from lxml import html

base = os.environ.get("NASQO_TEST_BASE_URL", "http://127.0.0.1:8069").rstrip("/")
pilot = "PILOT_ADMIN_PASSWORD" in os.environ
db = "nasqo_pilot" if pilot else "nasqo_odoo19"
password = os.environ["PILOT_ADMIN_PASSWORD" if pilot else "STAGE_ODOO_ADMIN_PASSWORD"]
session = requests.Session()
session.headers["User-Agent"] = "NASQO PRO-Identity-Verification/1.0"
checks = []

def check(name, condition):
    if not condition:
        print("FAIL", name)
        sys.exit(1)
    checks.append(name)
    print("PASS", name)

def get(path):
    response = session.get(base + path, timeout=120)
    check("HTTP " + path.split("?")[0], response.status_code == 200)
    return response

def visible(document):
    clone = html.fromstring(html.tostring(document))
    for node in clone.xpath("//script|//style"):
        node.drop_tree()
    return re.sub(r"\s+", " ", clone.text_content()).strip()

login = get("/web/login")
doc = html.fromstring(login.text)
check("NASQO PRO login title", "نسقو برو" in doc.findtext(".//title", ""))
check("Login visible branding", "نسقو برو" in visible(doc) and "Odoo" not in visible(doc))
check("Native auth and CSRF retained", bool(doc.xpath("//form[@action='/web/login']//input[@name='csrf_token'][string-length(@value)>10]")))
check("Login favicon", bool(doc.xpath("//link[@rel='shortcut icon'][contains(@href,'nasqo_backend_branding')]")))
response = session.post(base + "/web/session/authenticate", json={
    "jsonrpc": "2.0", "method": "call", "id": 1,
    "params": {"db": db, "login": "admin", "password": password}
}, timeout=90)
data = response.json()
check("Administrator authentication", bool(data.get("result", {}).get("uid")))
backend = get("/odoo/apps")
check("Authenticated backend", "/web/login" not in backend.url)
doc = html.fromstring(backend.text)
check("Backend initial title", "نسقو برو" in doc.findtext(".//title", ""))
check("Backend favicon", bool(doc.xpath("//link[@rel='shortcut icon'][contains(@href,'nasqo_backend_branding')]")))
bundles = []
for url in doc.xpath("//script[@src]/@src"):
    if "/web/assets/" in url:
        result = session.get(base + url, timeout=120)
        check("JavaScript asset", result.status_code == 200)
        bundles.append(result.text)
js = "\n".join(bundles)
check("Backend identity JavaScript bundled", "nasqo_brand" in js)
check("Backend OWL templates bundled", "nasqo_backend_branding.AppsMenu" in js and "nasqo_backend_branding.About" in js)
check("Expired session and upgrade templates bundled", "nasqo_backend_branding.SessionExpired" in js and "nasqo_backend_branding.Upgrade" in js)
css = []
for url in doc.xpath("//link[@rel='stylesheet']/@href"):
    result = session.get(base + url, timeout=120)
    check("Stylesheet asset", result.status_code == 200)
    css.append(result.text)
check("NASQO PRO CSS compiled", "--nasqo-ink" in "\n".join(css) and "style compilation failed" not in "\n".join(css).lower())
manifest = get("/web/manifest.webmanifest").json()
check("PWA identity and route", manifest["short_name"] == "NASQO PRO" and "نسقو برو" in manifest["name"] and manifest["scope"] == "/odoo")
for icon in manifest["icons"]:
    content = get(icon["src"]).content
    size = int(icon["sizes"].split("x")[0])
    check("PWA icon " + str(size), content.startswith(b"\x89PNG") and struct.unpack(">II", content[16:24]) == (size, size))
offline = html.fromstring(get("/odoo/offline").text)
check("Offline identity", "نسقو برو" in visible(offline) and "Odoo" not in visible(offline))
menus = get("/web/webclient/load_menus").json()
check("Applications menu available", len(menus) > 1)

def rpc(model, method, args, kwargs):
    result = session.post(base + "/web/dataset/call_kw/" + model + "/" + method, json={
        "jsonrpc": "2.0", "method": "call", "id": 2,
        "params": {"model": model, "method": method, "args": args, "kwargs": kwargs},
    }, timeout=90).json()
    check(model + "." + method, "result" in result and "error" not in result)
    return result["result"]

settings = rpc("res.config.settings", "get_view", [], {"view_type": "form"})
check("Settings inheritance", 'placeholder="NASQO PRO"' in settings["arch"])
apps = rpc("ir.module.module", "get_view", [], {"view_type": "kanban"})
check("Apps view inheritance", "odoo.com/pricing" not in apps["arch"] and "غير متاح في هذه النسخة" in apps["arch"])
for path in ("/", "/shop", "/shop/cart"):
    get(path)
logout = session.get(base + "/web/session/logout?redirect=/web/login", timeout=30)
check("Logout", logout.status_code == 200 and "/web/login" in logout.url)
print(json.dumps({"status": "PASS", "checks": len(checks), "target": base, "database": db}, ensure_ascii=False))
