import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CodespacesFoundationTests(unittest.TestCase):
    def test_v1_workspace_is_blocked_before_credentials_or_docker_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = root / '.devcontainer/.state'
            state.mkdir(parents=True)
            marker = state / 'bootstrapped'
            marker.write_text('existing-test-workspace')
            script = root / 'scripts/codespace/bootstrap.sh'
            script.parent.mkdir(parents=True)
            script.write_bytes((ROOT / 'scripts/codespace/bootstrap.sh').read_bytes())
            result = subprocess.run(['bash', str(script)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('fresh Codespace for v2', result.stderr)
            self.assertEqual(marker.read_text(), 'existing-test-workspace')
            self.assertFalse((root / '.devcontainer/.env').exists())
            self.assertFalse((state / 'bootstrapped-v2').exists())

    def test_codespace_targets_disposable_own_environment(self):
        config = json.loads((ROOT / ".devcontainer/devcontainer.json").read_text())
        self.assertIn(8069, config["forwardPorts"])
        self.assertIn("docker-in-docker", " ".join(config["features"]))
        self.assertIn("bootstrap.sh", config["postCreateCommand"])
        self.assertIn("resume.sh", config["postStartCommand"])

    def test_compose_never_references_production(self):
        c = (ROOT / ".devcontainer/compose.yaml").read_text()
        for banned in ("erp.indexesstore.com", "185.197.31.233", "waha-shopify-test"):
            self.assertNotIn(banned, c)
        self.assertIn("127.0.0.1:8069:8069", c)
        self.assertIn("odoo:19.0-20261112", c)
        self.assertIn("postgres:16", c)
        self.assertIn("NASQO_DEV_DB_PASSWORD", c)
        self.assertNotIn("5432:5432", c)
        self.assertIn("nasqo-odoo19-postgres", c)
        self.assertIn("NASQO_REPO_ROOT", c)

    def test_uses_pinned_odoo_source_and_no_default_password(self):
        entrypoint = (ROOT / "scripts/codespace/odoo_entrypoint.sh").read_text()
        self.assertIn("vendor/odoo/odoo-bin", entrypoint.replace("$source_dir", "vendor/odoo"))
        self.assertIn("nasqo_store", entrypoint)
        self.assertIn("shell", entrypoint)
        bootstrap = (ROOT / "scripts/codespace/bootstrap.sh").read_text()
        self.assertIn("secrets.token_urlsafe", bootstrap)
        self.assertIn("base.user_admin", bootstrap)
        self.assertIn("os.getcwd()", bootstrap)
        self.assertIn("chmod a+rx vendor", bootstrap)
        self.assertIn("chmod -R a+rX vendor/odoo", bootstrap)
        self.assertIn("scripts/codespace/verify.sh", bootstrap)
        self.assertIn("--retry-all-errors", (ROOT / "scripts/codespace/verify.sh").read_text())

    def test_secret_files_are_ignored(self):
        text = (ROOT / ".gitignore").read_text()
        self.assertIn("/.devcontainer/.env", text)
        self.assertIn("/.devcontainer/.state/", text)


if __name__ == "__main__":
    unittest.main()
