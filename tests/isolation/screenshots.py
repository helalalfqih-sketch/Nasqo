"""Capture the real, anonymous M2 UI on a disposable GitHub runner only.

No fixtures, themes, credentials or runtime configuration are changed here.
Only PNGs and a small provenance report are published, never DOM or profiles.
"""
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile

from .run import Browser, check

ROOT = Path(__file__).resolve().parents[2]


class PageEvidence(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.inputs = {}

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(values["id"])
        if tag == "input" and values.get("name") in ("login", "password"):
            self.inputs[values["name"]] = values.get("value", "")


def execute():
    check(os.environ.get("GITHUB_ACTIONS") == "true",
          "Capture is restricted to disposable GitHub Actions test runners")
    report = json.loads((ROOT / "artifacts/m2-results.json").read_text())
    check(report.get("result") == "PASS", "M2 acceptance must pass before capture")
    chrome = next((path for name in ("google-chrome", "google-chrome-stable", "chromium")
                   if (path := shutil.which(name))), None)
    check(chrome is not None, "Runner Chrome/Chromium is unavailable")
    output = ROOT / "artifacts/visual-evidence"
    output.mkdir(exist_ok=False)
    evidence = {
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "checkout_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "odoo_commit": report["source_commit"],
        "browser": subprocess.check_output([chrome, "--version"], text=True).strip(),
        "scope": "Unmodified anonymous Odoo foundation with synthetic M2 products; no custom NASQO design or checkout claim",
        "pages": [],
    }
    pages = (
        ("alpha", "/shop", "store-a-desktop.png", 1440, 1000),
        ("beta", "/shop", "store-b-desktop.png", 1440, 1000),
        ("alpha", "/web/login", "store-a-login.png", 1440, 1000),
        ("alpha", "/shop", "store-a-mobile-width.png", 420, 900),
    )
    for slug, path, filename, width, height in pages:
        # Independent HTTP control before opening an anonymous browser profile.
        status, body = Browser(slug).request(path)
        check(status == 200, "Screenshot HTTP control failed")
        own = "M2-" + slug.upper() + "-"
        other = "M2-" + ("BETA" if slug == "alpha" else "ALPHA") + "-"
        if path == "/shop":
            check(own.encode() in body and other.encode() not in body,
                  "Screenshot fixture/tenant control failed")
        url = f"http://{slug}.nasqo.test:18069{path}"
        target = output / filename
        with tempfile.TemporaryDirectory(prefix="nasqo-anonymous-capture-") as profile:
            command = [
                chrome, "--headless", "--no-first-run", "--no-default-browser-check",
                "--disable-background-networking", "--disable-sync", "--no-proxy-server",
                "--host-resolver-rules=MAP alpha.nasqo.test 127.0.0.1,MAP beta.nasqo.test 127.0.0.1,MAP * ~NOTFOUND",
                "--force-device-scale-factor=1", f"--user-data-dir={profile}",
                f"--window-size={width},{height}", "--virtual-time-budget=10000",
                "--timeout=45000", "--dump-dom", f"--screenshot={target}", url,
            ]
            result = subprocess.run(command, capture_output=True, timeout=90)
        check(result.returncode == 0, "Headless browser failed; raw output suppressed")
        dom = result.stdout.decode(errors="replace")
        parsed = PageEvidence()
        parsed.feed(dom)
        if path == "/shop":
            check("products_grid" in parsed.ids and own in dom and other not in dom,
                  "Rendered shop/tenant evidence is missing")
        else:
            check(parsed.inputs == {"login": "", "password": ""},
                  "Expected a blank anonymous login form")
        png = target.read_bytes()
        check(png[:8] == b"\x89PNG\r\n\x1a\n" and len(png) > 10000, "Invalid screenshot PNG")
        check(struct.unpack(">II", png[16:24]) == (width, height), "Unexpected screenshot dimensions")
        evidence["pages"].append({"file": filename, "url": url, "http_status": status,
                                  "width": width, "height": height,
                                  "sha256": hashlib.sha256(png).hexdigest(),
                                  "rendered_dom_check": "PASS"})
        print(f"PASS anonymous screenshot: {filename}", flush=True)
    (output / "provenance.json").write_text(json.dumps(evidence, indent=2) + "\n")


if __name__ == "__main__":
    execute()
