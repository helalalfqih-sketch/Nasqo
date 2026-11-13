"""Operator-owned registry. No merchant transactions or public API live here."""
from contextlib import contextmanager
import fcntl
import hashlib
import os
from pathlib import Path
import re
import sqlite3
import stat
import uuid


class Conflict(ValueError):
    pass


def validate_slug(slug):
    if not re.fullmatch(r"[a-z][a-z0-9]{2,23}", slug):
        raise ValueError("Use a lowercase alphanumeric slug, 3–24 characters.")
    return slug


def private_directory(path):
    path = Path(path).absolute()
    if path.is_symlink():
        raise PermissionError("State directories must not be symlinks.")
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = path.stat()
    if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
        raise PermissionError("State must be owned by the operator and have mode 0700.")
    return path


def write_private(path, content):
    with open(path, "x", encoding="utf-8") as file:
        os.chmod(path, 0o600)
        file.write(content)


class Registry:
    def __init__(self, directory):
        self.directory = private_directory(directory)
        self.path = self.directory / "registry.sqlite3"
        if self.path.is_symlink():
            raise PermissionError("Registry must not be a symlink.")
        self.db = sqlite3.connect(self.path, timeout=30)
        os.chmod(self.path, 0o600)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS settings (name TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS stores (
                tenant_id TEXT PRIMARY KEY, slug TEXT UNIQUE NOT NULL,
                key_hash TEXT UNIQUE NOT NULL, state TEXT NOT NULL,
                phase TEXT NOT NULL, error_code TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY, tenant_id TEXT NOT NULL, state TEXT NOT NULL,
                phase TEXT NOT NULL, error_code TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.db.execute("INSERT OR IGNORE INTO settings VALUES ('instance', ?)",
                        (uuid.uuid4().hex[:12],))
        self.db.commit()
        self.instance = self.db.execute("SELECT value FROM settings WHERE name='instance'").fetchone()[0]

    def close(self):
        self.db.close()

    @contextmanager
    def lock(self):
        path = self.directory / "operator.lock"
        fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "w") as file:
            fcntl.flock(file, fcntl.LOCK_EX)
            yield

    def get(self, slug):
        row = self.db.execute("SELECT * FROM stores WHERE slug=?", (slug,)).fetchone()
        if not row:
            raise ValueError("Unknown store.")
        return dict(row)

    def stores(self):
        return [dict(row) for row in self.db.execute("SELECT * FROM stores ORDER BY slug")]

    def reserve(self, slug, key):
        validate_slug(slug)
        if not isinstance(key, str) or not 16 <= len(key) <= 200:
            raise ValueError("Idempotency key must contain 16–200 characters.")
        digest = hashlib.sha256(key.encode()).hexdigest()
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            row = self.db.execute("SELECT * FROM stores WHERE key_hash=?", (digest,)).fetchone()
            if row:
                if row["slug"] != slug:
                    raise Conflict("Idempotency key was already used with a different request.")
                return dict(row)
            if self.db.execute("SELECT 1 FROM stores WHERE slug=?", (slug,)).fetchone():
                raise Conflict("Slug already belongs to a different operation.")
            self.db.execute("INSERT INTO stores (tenant_id,slug,key_hash,state,phase) VALUES (?,?,?,'requested','reserved')",
                            (uuid.uuid4().hex, slug, digest))
        self.transition(slug, "requested", "reserved")
        return self.get(slug)

    def transition(self, slug, state, phase, error_code=None):
        with self.db:
            self.db.execute("UPDATE stores SET state=?, phase=?, error_code=? WHERE slug=?",
                            (state, phase, error_code, slug))
            self.db.execute("INSERT INTO events (tenant_id,state,phase,error_code) SELECT tenant_id,?,?,? FROM stores WHERE slug=?",
                            (state, phase, error_code, slug))


def provision(registry, backend, slug, key, *, fault_after=None):
    """Serialized single-host worker. Retry is safe only before tenant activation.

    Completed installation is retained; an ambiguous interrupted step is rechecked
    by the backend. No route is published until installation and HTTP verify pass.
    fault_after is a test seam, deliberately absent from the CLI.
    """
    with registry.lock():
        store = registry.reserve(slug, key)
        if store["state"] == "active":
            return store
        phase = store["phase"]
        try:
            for phase, state, action in (
                ("database", "provisioning", backend.prepare),
                ("modules", "initializing", backend.initialize),
                ("http", "verifying", backend.verify),
            ):
                registry.transition(slug, state, phase)
                action(store)
                if fault_after == phase:
                    raise RuntimeError("Injected failure for integration testing.")
            registry.transition(slug, "active", "verified")
        except Exception:
            try:
                backend.quarantine(store)
            finally:
                # Never persist exception text: it can contain credentials/SQL.
                registry.transition(slug, "failed_needs_review", phase, "PROVISION_FAILED")
            raise
        return registry.get(slug)
