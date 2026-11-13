import ast
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]

class FoundationTests(unittest.TestCase):
    def test_upstream_pin(self):
        p = json.loads((ROOT / 'upstream.json').read_text())
        self.assertEqual(p['repository'], 'https://github.com/odoo/odoo.git')
        self.assertEqual(p['series'], '19.0')
        self.assertRegex(p['commit'], r'^[0-9a-f]{40}$')

    def test_manifest(self):
        manifests = list((ROOT / 'addons').glob('*/__manifest__.py'))
        self.assertTrue(manifests)
        for path in manifests:
            m = ast.literal_eval(path.read_text())
            self.assertTrue(path.parent.name.startswith('nasqo_'))
            self.assertTrue(m['version'].startswith('19.0.'))
            self.assertIn('website_sale', m['depends'])
            self.assertFalse(m['auto_install'])
            self.assertTrue((path.parent / '__init__.py').is_file())
            for item in m['data']:
                self.assertTrue((path.parent / item).is_file())

    def test_python_syntax(self):
        for p in (ROOT / 'addons').rglob('*.py'):
            ast.parse(p.read_text(), filename=str(p))

    def test_local_config_guardrails(self):
        c = (ROOT / 'config/odoo.dev.conf.example').read_text()
        self.assertIn('http_interface = 127.0.0.1', c)
        self.assertIn('dbfilter = ^nasqo_dev$', c)
        self.assertNotRegex(c, r'(?m)^\s*(db_password|admin_passwd)\s*=')

if __name__ == '__main__':
    unittest.main()
