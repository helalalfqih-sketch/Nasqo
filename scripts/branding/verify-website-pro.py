"""Read-only public identity checks. Run inside either Odoo container.
No form submission, authentication, payments, customer or company writes.
"""
import os, re, unittest
import requests
from lxml import html

BASE = os.environ.get("NASQO_TEST_BASE_URL", "http://127.0.0.1:8069").rstrip("/")
ASSET = "/nasqo_backend_branding/static/img/"
class WebsiteIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.session = requests.Session()
        cls.pages = {}
    def page(self, path, status=200):
        if path not in self.pages:
            response = self.session.get(BASE + path, timeout=120)
            self.assertEqual(response.status_code, status, path)
            self.pages[path] = html.fromstring(response.text)
        return self.pages[path]
    def visible(self, tree):
        tree = html.fromstring(html.tostring(tree))
        for element in tree.xpath("//script|//style"):
            element.drop_tree()
        return re.sub(r"\s+", " ", tree.text_content())
    def test_public_branding_and_no_sample_contact(self):
        for path in ("/", "/nasqo", "/shop", "/shop/cart", "/contactus", "/terms"):
            with self.subTest(path=path):
                tree = self.page(path)
                text = self.visible(tree)
                self.assertIn("نسقو برو", text)
                self.assertNotRegex(text, r"Odoo|أودو|My Website|My Company|اسم الشركة|555-555|yourcompany|Fake Buena")
                self.assertTrue(tree.xpath("//a[contains(@class,'nasqo-site-brand')]"))
                self.assertTrue(tree.xpath("//div[@id='footer'][contains(@class,'nasqo-site-footer')]"))
                self.assertFalse(tree.xpath("//a[contains(@href,'odoo.com')]"))
                self.assertFalse(tree.xpath("//div[@id='footer']//a[@href='#']"))
    def test_favicon_and_touch_icon(self):
        tree = self.page("/nasqo")
        self.assertEqual(tree.xpath("//link[@rel='shortcut icon']/@href"), [ASSET + "favicon.svg"])
        self.assertEqual(tree.xpath("//link[@rel='apple-touch-icon']/@href"), [ASSET + "icon-180.png"])
        for path in (ASSET + "favicon.svg", ASSET + "icon-180.png"):
            self.assertEqual(self.session.get(BASE + path, timeout=30).status_code, 200)
    def test_styles_compiled(self):
        tree = self.page("/nasqo")
        urls = tree.xpath("//link[@rel='stylesheet']/@href")
        self.assertTrue(urls)
        css = []
        for url in urls:
            response = self.session.get(BASE + url, timeout=120)
            self.assertEqual(response.status_code, 200)
            css.append(response.text)
        content = "\n".join(css)
        self.assertIn(".nasqo-footer-grid", content)
        self.assertNotIn("style compilation failed", content.lower())
        self.assertRegex(content, r"max-width:\s*767px")
    def test_arabic_titles_and_rtl(self):
        for path, title in (("/nasqo", "الرئيسية"), ("/shop", "المتجر"), ("/shop/cart", "سلة التسوق"), ("/contactus", "تواصل معنا"), ("/terms", "الشروط والأحكام")):
            with self.subTest(path=path):
                tree = self.page(path)
                self.assertIn(title, tree.findtext(".//title", ""))
                self.assertTrue(tree.xpath("//*[@dir='rtl']"))
    def test_contact_form_is_valid_or_pending(self):
        tree = self.page("/contactus")
        forms = tree.xpath("//form[@id='contactus_form']")
        if forms:
            self.assertEqual(forms[0].get("action"), "/website/form/")
            self.assertTrue(forms[0].xpath(".//input[@name='email_from'][@required]"))
            self.assertTrue(forms[0].xpath(".//input[@name='email_to']"))
        else:
            self.assertIn("نموذج المراسلة غير متاح حاليًا", self.visible(tree))
        self.assertFalse(tree.xpath("//a[starts-with(@href,'mailto:info@yourcompany')]"))
    def test_login_identity_and_native_auth_preserved(self):
        tree = self.page("/web/login")
        self.assertTrue(tree.xpath("//section[contains(@class,'nasqo-login-card')]"))
        self.assertTrue(tree.xpath("//form[@action='/web/login']//input[@name='csrf_token'][string-length(@value)>10]"))
        self.assertTrue(tree.xpath("//input[@name='password']"))
        self.assertNotRegex(self.visible(tree), r"Odoo|أودو|yourcompany|555-555")
    def test_checkout_and_account_links_preserved(self):
        tree = self.page("/shop/cart")
        self.assertTrue(tree.xpath("//div[@id='shop_cart']"))
        footer = self.page("/nasqo").xpath("//div[@id='footer']")[0]
        for path in ("/shop", "/shop/cart", "/my", "/contactus", "/terms"):
            self.assertTrue(footer.xpath(".//a[@href=$path]", path=path), path)
        response = self.session.get(BASE + "/my", timeout=60)
        self.assertEqual(response.status_code, 200)
        self.assertIn("/web/login", response.url)
    def test_sharing_title_and_image(self):
        for path in ("/nasqo", "/shop"):
            tree = self.page(path)
            self.assertEqual(tree.xpath("//meta[@property='og:title']/@content"), [tree.findtext(".//title")])
            self.assertTrue(all("nasqo_backend_branding" in value for value in tree.xpath("//meta[@property='og:image']/@content")))
            self.assertEqual(tree.xpath("//meta[@name='generator']/@content"), ["NASQO PRO"])
    def test_error_page_identity(self):
        tree = self.page("/nasqo-identity-check-not-found", 404)
        self.assertTrue(tree.xpath("//div[@id='footer'][contains(@class,'nasqo-site-footer')]"))
        self.assertNotRegex(self.visible(tree), r"Odoo|أودو|yourcompany|555-555")

if __name__ == "__main__":
    unittest.main(verbosity=2)
