"""Offline DB+filestore backup and fresh, same-tenant restore drill.

GnuPG encrypts and integrity-protects the complete archive. The recovery key is
kept outside the archive. Never overwrite a running tenant or extract user paths.
"""
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import secrets
import stat
import tarfile
import tempfile
import uuid
import zipfile

from .registry import private_directory, write_private
from .runtime import ROOT, Runtime, create_config, run

MAX_ARCHIVE = 512 * 1024 * 1024  # Synthetic pilot only, not a large-database service.


def key_bytes(path, *, create=False):
    path = Path(path)
    if path.is_symlink():
        raise PermissionError("Recovery key must not be a symlink.")
    if create and not path.exists():
        write_private(path, secrets.token_hex(32) + "\n")
    info = path.stat()
    if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
        raise PermissionError("Recovery key must be operator-owned with mode 0600.")
    key = path.read_bytes()
    if len(key.strip()) < 32:
        raise ValueError("Recovery key is too short.")
    return key


def crypt(source, target, key, *, decrypt=False):
    if Path(target).exists():
        raise FileExistsError("Refusing to overwrite an archive.")
    with tempfile.TemporaryDirectory(prefix="nasqo-gpg-") as home:
        args = ["gpg", "--homedir", home, "--batch", "--no-tty", "--no-symkey-cache",
                "--pinentry-mode", "loopback", "--passphrase-fd", "0", "--output", str(target)]
        args += ["--decrypt"] if decrypt else ["--symmetric", "--cipher-algo", "AES256", "--force-mdc"]
        run([*args, str(source)], input=key, timeout=120)
    os.chmod(target, 0o600)


def validate_bundle(path, store):
    with zipfile.ZipFile(path) as archive:
        expected = {"manifest.json", "database.dump", "filestore.tar"}
        if len(archive.infolist()) != 3 or set(archive.namelist()) != expected:
            raise ValueError("Invalid backup members.")
        if sum(x.file_size for x in archive.infolist()) > MAX_ARCHIVE:
            raise ValueError("Backup exceeds the pilot size limit.")
        manifest = json.loads(archive.read("manifest.json"))
        if (manifest.get("format") != 1 or manifest.get("tenant_id") != store["tenant_id"]
                or manifest.get("slug") != store["slug"]):
            raise ValueError("Cross-tenant restore rejected.")
        if manifest.get("odoo_commit") != json.loads((ROOT / "upstream.json").read_text())["commit"]:
            raise ValueError("Restore requires the matching Odoo version.")
        members = {name: archive.read(name) for name in ("database.dump", "filestore.tar")}
    for name, data in members.items():
        if hashlib.sha256(data).hexdigest() != manifest["sha256"].get(name):
            raise ValueError("Backup checksum mismatch.")
    # A tar file may contain path traversal, devices, hardlinks or symlinks.
    # Only plain directories and files under this tenant's DB name are accepted.
    with tarfile.open(fileobj=io.BytesIO(members["filestore.tar"])) as archive:
        total = 0
        for member in archive:
            path = PurePosixPath(member.name)
            if (path.is_absolute() or ".." in path.parts or not path.parts
                    or path.parts[0] != "nasqo_" + store["slug"]
                    or not (member.isfile() or member.isdir())):
                raise ValueError("Unsafe filestore archive member.")
            total += member.size
            if total > MAX_ARCHIVE:
                raise ValueError("Filestore exceeds the pilot size limit.")
    return members


def backup(registry, runtime, slug, key_path):
    with registry.lock():
        store = registry.get(slug)
        if store["state"] != "active":
            raise ValueError("Only verified active stores can be backed up.")
        directory = private_directory(registry.directory / "backups")
        key = key_bytes(key_path, create=True)
        destination = directory / f"{slug}-{uuid.uuid4().hex}.gpg"
        runtime.dc(store, "stop", "odoo")
        try:
            # No application writers run between these two snapshots.
            database = runtime.dc(store, "exec", "-T", "db", "pg_dump", "-U", "postgres",
                                  "-Fc", "--no-owner", "--no-acl", runtime.db_name(store), timeout=300).stdout
            files = runtime.dc(store, "run", "--rm", "-T", "--no-deps", "--entrypoint", "tar", "odoo",
                               "-C", "/var/lib/odoo/filestore", "-cf", "-", runtime.db_name(store), timeout=300).stdout
            if len(database) + len(files) > MAX_ARCHIVE:
                raise ValueError("Backup exceeds the pilot size limit.")
            manifest = {"format": 1, "tenant_id": store["tenant_id"], "slug": slug,
                        "odoo_commit": json.loads((ROOT / "upstream.json").read_text())["commit"],
                        "sha256": {"database.dump": hashlib.sha256(database).hexdigest(),
                                   "filestore.tar": hashlib.sha256(files).hexdigest()}}
            with tempfile.TemporaryDirectory(dir=directory) as temporary:
                bundle = Path(temporary) / "bundle.zip"
                with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_STORED) as archive:
                    archive.writestr("manifest.json", json.dumps(manifest))
                    archive.writestr("database.dump", database)
                    archive.writestr("filestore.tar", files)
                crypt(bundle, destination, key)
        finally:
            runtime.verify(store)
        registry.transition(slug, "active", "verified")
        return destination


class RestoreRuntime(Runtime):
    def __init__(self, registry, restore_id):
        super().__init__(registry)
        self.restore_id = restore_id

    def project(self, store):
        return f"nasqo-m2-{self.registry.instance}-restore-{self.restore_id}"

    def directory(self, store):
        return self.registry.directory / "restores" / self.restore_id


def restore(registry, slug, source, key_path):
    with registry.lock():
        store = registry.get(slug)
        key = key_bytes(key_path)
        if Path(source).stat().st_size > MAX_ARCHIVE + 1048576:
            raise ValueError("Encrypted backup exceeds the pilot limit.")
        # Validate completely before creating any Docker resources.
        with tempfile.TemporaryDirectory(dir=registry.directory) as temporary:
            bundle = Path(temporary) / "bundle.zip"
            crypt(source, bundle, key, decrypt=True)
            members = validate_bundle(bundle, store)
        restore_id = uuid.uuid4().hex[:12]
        private_directory(registry.directory / "restores")
        runtime = RestoreRuntime(registry, restore_id)
        create_config(runtime.directory(store), runtime.project(store), runtime.db_name(store))
        try:
            runtime.prepare(store)
            runtime.dc(store, "exec", "-T", "db", "pg_restore", "-U", "postgres", "--exit-on-error",
                       "--no-owner", "--no-acl", "--no-comments", "--role=" + runtime.db_name(store),
                       "-d", runtime.db_name(store), input=members["database.dump"], timeout=600)
            runtime.dc(store, "run", "--rm", "-T", "--no-deps", "--entrypoint", "sh", "odoo", "-c",
                       "mkdir -p /var/lib/odoo/filestore && tar -C /var/lib/odoo/filestore -xf -",
                       input=members["filestore.tar"], timeout=300)
            # Rotate restored credentials and neutralize scheduled/outbound activity.
            password = json.loads((runtime.directory(store) / "credentials.json").read_text())["admin"]
            runtime.shell(store, f"env.ref('base.user_admin').write({{'password': {password!r}}})\n"
                          "env['ir.cron'].search([]).write({'active': False})\n"
                          "env['ir.mail_server'].search([]).write({'active': False})\n"
                          "env.cr.commit()\n")
            runtime.verify(store)
        except Exception:
            runtime.quarantine(store)
            raise
        # No host port, no tenant gateway, separate volumes and network.
        return runtime, store
