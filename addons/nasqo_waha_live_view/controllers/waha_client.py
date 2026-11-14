"""Pilot Odoo client for authenticated, fixed GET-only QR gateway.

No WAHA API keys are present here. Not deployed to Odoo production.
"""
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

BASE = "http://nasqo-wa-qr-gateway:18075"
SESSION = "nasqo-primary"
KEY_FILE = Path("/run/secrets/nasqo_gateway_client_key")
LIMIT = 262144


class WahaUnavailable(Exception):
    pass


class NoSession(Exception):
    pass


class NoQR(Exception):
    pass


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _api_get(path, accept="application/json"):
    if path not in {"/status", "/qr"}:
        raise ValueError("Gateway path not allowed")
    try:
        secret = KEY_FILE.read_text(encoding="ascii").strip()
    except (OSError, UnicodeError):
        raise WahaUnavailable("Gateway identity unavailable") from None
    if not 24 <= len(secret) <= 256 or "\n" in secret or "\r" in secret:
        raise WahaUnavailable("Invalid client identity")
    req = Request(BASE + path, headers={
        "X-Nasqo-Gateway-Key": secret, "Accept": accept,
    }, method="GET")
    try:
        with build_opener(ProxyHandler({}), NoRedirects()).open(req, timeout=5) as res:
            mime = res.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if int(res.headers.get("Content-Length") or 0) > LIMIT:
                raise WahaUnavailable("Gateway response too large")
            raw = res.read(LIMIT + 1)
            if len(raw) > LIMIT:
                raise WahaUnavailable("Gateway response too large")
            return mime, raw
    except HTTPError as ex:
        if ex.code == 404:
            if path == "/qr":
                raise NoQR("No QR available") from None
            raise NoSession("Session does not exist") from None
        raise WahaUnavailable("Gateway unavailable") from None
    except (URLError, OSError, TimeoutError, ValueError):
        raise WahaUnavailable("Gateway unavailable") from None


def get_session_status():
    mime, raw = _api_get("/status")
    if mime != "application/json":
        raise WahaUnavailable("Unexpected type")
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        raise WahaUnavailable("Invalid status response") from None
    if not isinstance(data, dict) or data.get("name") != SESSION:
        raise WahaUnavailable("Unexpected session")
    status = str(data.get("status", "UNKNOWN"))
    if status not in {
        "STOPPED", "STARTING", "SCAN_QR_CODE", "WORKING",
        "FAILED", "PASSKEY_REQUIRED", "PASSKEY_CONFIRMATION_REQUIRED",
    }:
        status = "UNKNOWN"
    return status


def get_qr_png():
    mime, raw = _api_get("/qr", "image/png")
    if mime != "image/png" or not raw.startswith(b"\x89PNG\r\n\x1a\n"):
        raise NoQR("Not a valid QR PNG")
    return raw
