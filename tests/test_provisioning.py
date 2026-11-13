import concurrent.futures
import hashlib
import io
import json
import os
from pathlib import Path
import tarfile
import tempfile
import unittest
import zipfile

from provisioning.backup import crypt, key_bytes, validate_bundle
from provisioning.registry import Conflict, Registry, provision, validate_slug
from provisioning.runtime import ROOT, compose_spec


class FakeRuntime:
    def __init__(self):
        self.calls = []

    def prepare(self, store):
        self.calls.append("database")

    def initialize(self, store):
        self.calls.append("modules")

    def verify(self, store):
        self.calls.append("http")

    def quarantine(self, store):
        self.calls.append("quarantine")


class ProvisioningTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)
        self.registry = Registry(self.path)
        self.backend = FakeRuntime()

    def tearDown(self):
        self.registry.close()
        self.temp.cleanup()

    def test_same_request_has_one_operation_and_no_repeat_side_effect(self):
        first = provision(self.registry, self.backend, "alpha", "idempotency-alpha-01")
        second = provision(self.registry, self.backend, "alpha", "idempotency-alpha-01")
        self.assertEqual(first["tenant_id"], second["tenant_id"])
        self.assertEqual(second["state"], "active")
        self.assertEqual(self.backend.calls, ["database", "modules", "http"])
        self.assertEqual(len(self.registry.stores()), 1)

    def test_reused_key_or_slug_with_different_request_is_rejected(self):
        self.registry.reserve("alpha", "idempotency-alpha-01")
        with self.assertRaises(Conflict):
            self.registry.reserve("beta", "idempotency-alpha-01")
        with self.assertRaises(Conflict):
            self.registry.reserve("alpha", "idempotency-alpha-02")

    def test_failure_quarantines_and_retry_reuses_identity(self):
        with self.assertRaises(RuntimeError):
            provision(self.registry, self.backend, "alpha", "idempotency-alpha-01", fault_after="database")
        failed = self.registry.get("alpha")
        self.assertEqual(failed["state"], "failed_needs_review")
        self.assertEqual(self.backend.calls, ["database", "quarantine"])
        recovered = provision(self.registry, self.backend, "alpha", "idempotency-alpha-01")
        self.assertEqual(recovered["tenant_id"], failed["tenant_id"])
        self.assertEqual(recovered["state"], "active")

    def test_concurrent_reservations_return_one_identity(self):
        def reserve(_):
            registry = Registry(self.path)
            try:
                return registry.reserve("alpha", "idempotency-alpha-01")["tenant_id"]
            finally:
                registry.close()
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            self.assertEqual(len(set(pool.map(reserve, range(12)))), 1)

    def test_slug_cannot_inject_database_path_domain_or_compose_name(self):
        for slug in ("../../other", "a;DROP", "*.evil.test", "aa", "Aaa", "alpha-beta", "a" * 25, "alpha\n"):
            with self.subTest(slug=slug), self.assertRaises(ValueError):
                validate_slug(slug)

    def test_state_must_be_private_and_cannot_be_symlink(self):
        unsafe = self.path / "unsafe"
        unsafe.mkdir(mode=0o755)
        with self.assertRaises(PermissionError):
            Registry(unsafe)
        (self.path / "link").symlink_to(self.path, target_is_directory=True)
        with self.assertRaises(PermissionError):
            Registry(self.path / "link")

    def test_runtime_mounts_only_own_config_and_public_code(self):
        spec = compose_spec(self.path, "nasqo-m2-test-alpha", "nasqo_alpha", {"postgres": "synthetic", "database": "synthetic"})
        self.assertNotIn("ports", spec["services"]["odoo"])
        self.assertNotIn("ports", spec["services"]["db"])
        mounts = spec["services"]["odoo"]["volumes"]
        self.assertNotIn(f"{ROOT}:/workspace:ro", mounts)
        self.assertTrue(spec["networks"]["database"]["internal"])
        self.assertTrue(spec["networks"]["frontend"]["internal"])

    def bundle(self, store, name="nasqo_alpha/aa/file", bad_hash=False, link=False):
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode="w") as archive:
            member = tarfile.TarInfo(name)
            if link:
                member.type, member.linkname = tarfile.SYMTYPE, "/etc/passwd"
                archive.addfile(member)
            else:
                member.size = 5
                archive.addfile(member, io.BytesIO(b"hello"))
        members = {"filestore.tar": stream.getvalue(), "database.dump": b"synthetic-dump"}
        manifest = {"format": 1, "tenant_id": store["tenant_id"], "slug": store["slug"],
                    "odoo_commit": json.loads((ROOT / "upstream.json").read_text())["commit"],
                    "sha256": {k: hashlib.sha256(v).hexdigest() for k, v in members.items()}}
        if bad_hash:
            manifest["sha256"]["database.dump"] = "invalid"
        path = self.path / "bundle.zip"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("manifest.json", json.dumps(manifest))
            for name, data in members.items():
                archive.writestr(name, data)
        return path

    def test_backup_identity_hash_and_path_checks(self):
        store = self.registry.reserve("alpha", "idempotency-alpha-01")
        self.assertEqual(validate_bundle(self.bundle(store), store)["database.dump"], b"synthetic-dump")
        other = self.registry.reserve("beta", "idempotency-beta-001")
        with self.assertRaisesRegex(ValueError, "Cross-tenant"):
            validate_bundle(self.bundle(store), other)
        with self.assertRaisesRegex(ValueError, "checksum"):
            validate_bundle(self.bundle(store, bad_hash=True), store)
        for name in ("nasqo_alpha/../../escape", "/absolute", "nasqo_beta/file"):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "Unsafe"):
                validate_bundle(self.bundle(store, name), store)
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            validate_bundle(self.bundle(store, link=True), store)

    def test_encrypted_archive_roundtrip_and_tamper_rejection(self):
        plaintext = self.path / "plain"
        plaintext.write_bytes(b"NASQO synthetic backup fixture" * 200)
        key = key_bytes(self.path / "recovery.key", create=True)
        encrypted, restored = self.path / "backup.gpg", self.path / "restored"
        crypt(plaintext, encrypted, key)
        self.assertNotIn(b"NASQO synthetic", encrypted.read_bytes())
        crypt(encrypted, restored, key, decrypt=True)
        self.assertEqual(restored.read_bytes(), plaintext.read_bytes())
        data = bytearray(encrypted.read_bytes())
        data[-10] ^= 1
        encrypted.write_bytes(data)
        with self.assertRaises(RuntimeError):
            crypt(encrypted, self.path / "tampered", key, decrypt=True)

    def test_recovery_key_permissions(self):
        key = self.path / "recovery.key"
        key_bytes(key, create=True)
        os.chmod(key, 0o644)
        with self.assertRaises(PermissionError):
            key_bytes(key)
