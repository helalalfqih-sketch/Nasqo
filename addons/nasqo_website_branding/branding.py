"""Pure formatting helpers. Never modify company or customer records."""
import re
from email.utils import parseaddr
from urllib.parse import quote


def public_contact(phone, email):
    phone = str(phone or "").strip()
    digits = re.sub(r"[^0-9]", "", phone)
    if (not 7 <= len(digits) <= 15 or len(set(digits)) < 2
            or digits in {"15555555556", "15555555555", "15555550100"}):
        phone = ""
    raw_email = str(email or "").strip()
    address = parseaddr(raw_email)[1] if not re.search(r"[\r\n]", raw_email) else ""
    domain = address.rsplit("@", 1)[-1].lower()
    if (not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", address)
            or domain in {"example.com", "example.org", "example.net", "yourcompany.com"}
            or domain.endswith((".example.com", ".example", ".invalid", ".test"))):
        address = ""
    return {
        "phone": phone,
        "phone_href": "tel:" + ("+" if phone.startswith("+") else "") + digits if phone else "",
        "email": address,
        "email_href": "mailto:" + quote(address, safe="@.+-_") if address else "",
    }


def has_custom_terms(content):
    content = str(content or "").strip()
    if not content:
        return False
    # Only suppress the supplied default/sample disclaimer, never rewrite real terms.
    markers = (
        "Below text serves as a suggestion",
        "You should update this document to reflect your T",
        "النص المذكور أدناه هو مجرد اقتراح من شركة أودو",
        "عليك تحديث هذا المستند لتطبيق الشروط والأحكام الخاصة بك",
    )
    return not any(marker.casefold() in content.casefold() for marker in markers)


def branded_metadata(metadata, title, base_url, website_id):
    result = dict(metadata)
    marker = f"/web/image/website/{website_id}/logo"
    brand_image = base_url.rstrip("/") + "/nasqo_backend_branding/static/img/icon-512.png"
    def image(value):
        if isinstance(value, list):
            return [image(item) for item in value]
        return brand_image if isinstance(value, str) and marker in value else value
    for group, title_key, image_key in (
        ("opengraph_meta", "og:title", "og:image"),
        ("twitter_meta", "twitter:title", "twitter:image"),
    ):
        values = dict(result.get(group) or {})
        if title:
            values[title_key] = title
        if image_key in values:
            values[image_key] = image(values[image_key])
        result[group] = values
    return result
