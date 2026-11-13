"""Docker Compose adapter; a separate PostgreSQL and Odoo runtime per store."""
import json
import os
from pathlib import Path
import secrets
import subprocess
import time

from .registry import private_directory, write_private

ROOT = Path(__file__).resolve().parents[1]
ODOO_IMAGE = "odoo:19.0-20261112"
POSTGRES_IMAGE = "postgres:16"
GATEWAY_IMAGE = "nginx:1.28-alpine"


def run(args, *, input=None, timeout=180, check=True):
    result = subprocess.run(args, input=input, capture_output=True, timeout=timeout)
    if check and result.returncode:
        # Suppress raw Docker/config/SQL output; it may contain a secret.
        raise RuntimeError(f"Local runtime command failed (exit {result.returncode}); raw output suppressed to protect credentials.")
    return result


def preflight():
    if os.environ.get("DOCKER_HOST", "unix://").split(":", 1)[0] != "unix":
        raise ValueError("M2 only supports a local Unix Docker socket.")
    endpoint = run(["docker", "context", "inspect", "--format", "{{.Endpoints.docker.Host}}"])
    if not endpoint.stdout.decode().strip().startswith("unix://"):
        raise ValueError("Remote Docker contexts are outside the M2 test scope.")
    run(["docker", "info"], timeout=30)
    pin = json.loads((ROOT / "upstream.json").read_text())["commit"]
    result = run(["git", "-C", str(ROOT / "vendor/odoo"), "rev-parse", "HEAD"])
    if result.stdout.decode().strip() != pin:
        raise ValueError("Odoo source differs from upstream.json.")
    if run(["git", "-C", str(ROOT / "vendor/odoo"), "status", "--porcelain"]).stdout.strip():
        raise ValueError("Pinned Odoo checkout has local modifications.")


def compose_spec(directory, project, db_name, password):
    """Only public source and the current store's config enter its container."""
    return {
        "name": project,
        "services": {
            "db": {
                "image": POSTGRES_IMAGE,
                "environment": {"POSTGRES_PASSWORD": password["postgres"],
                                "NASQO_DB_NAME": db_name, "NASQO_DB_PASSWORD": password["database"]},
                "volumes": ["postgres:/var/lib/postgresql/data",
                            f"{ROOT}/scripts/m2/db-init.sh:/docker-entrypoint-initdb.d/01-nasqo.sh:ro"],
                "networks": ["database"],
                "healthcheck": {"test": ["CMD-SHELL", "pg_isready -h 127.0.0.1 -U postgres -d postgres"],
                                "interval": "2s", "timeout": "3s", "retries": 60},
            },
            "odoo": {
                "image": ODOO_IMAGE, "init": True,
                "entrypoint": ["bash", "/opt/nasqo/scripts/entrypoint.sh"], "command": ["serve"],
                "environment": {"PYTHONDONTWRITEBYTECODE": "1"},
                "depends_on": {"db": {"condition": "service_healthy"}},
                "volumes": [f"{ROOT}/vendor/odoo:/opt/nasqo/odoo:ro",
                            f"{ROOT}/addons:/opt/nasqo/addons:ro",
                            f"{ROOT}/scripts/m2:/opt/nasqo/scripts:ro",
                            f"{directory}/odoo.conf:/run/nasqo/odoo.conf:ro",
                            "filestore:/var/lib/odoo"],
                "networks": {"database": {}, "frontend": {"aliases": [project]}},
                "security_opt": ["no-new-privileges:true"],
            },
        },
        "networks": {"database": {"internal": True},
                     "frontend": {"name": f"{project}-frontend", "internal": True}},
        "volumes": {"postgres": {}, "filestore": {}},
    }


def create_config(directory, project, db_name):
    directory = private_directory(directory)
    credential_path = directory / "credentials.json"
    if credential_path.exists():
        passwords = json.loads(credential_path.read_text())
    else:
        passwords = {name: secrets.token_urlsafe(32) for name in ("postgres", "database", "admin", "master", "portal")}
        write_private(credential_path, json.dumps(passwords))
    conf = directory / "odoo.conf"
    if not conf.exists():
        write_private(conf, f"""[options]
addons_path = /opt/nasqo/odoo/addons,/opt/nasqo/addons
data_dir = /var/lib/odoo
db_host = db
db_port = 5432
db_user = {db_name}
db_password = {passwords['database']}
db_name = {db_name}
; Odoo 19 list_dbs with dbfilter queries database ownership. This non-owner
; runtime uses the exact db_name allowlist instead (http.db_filter fallback).
dbfilter =
admin_passwd = {passwords['master']}
list_db = False
proxy_mode = False
http_interface = 0.0.0.0
http_port = 8069
max_cron_threads = 0
workers = 0
log_level = warn
""")
        # Parent is 0700 on the host; only this store receives the read-only file.
        os.chmod(conf, 0o444)
    path = directory / "compose.json"
    if not path.exists():
        write_private(path, json.dumps(compose_spec(directory, project, db_name, passwords), indent=2))
    return directory


class Runtime:
    def __init__(self, registry):
        self.registry = registry

    def project(self, store):
        return f"nasqo-m2-{self.registry.instance}-{store['slug']}"

    def directory(self, store):
        return self.registry.directory / store["slug"]

    def db_name(self, store):
        return "nasqo_" + store["slug"]

    def safe_output(self, store, output):
        diagnostic = output.decode(errors="replace")
        passwords = json.loads((self.directory(store) / "credentials.json").read_text())
        for value in passwords.values():
            diagnostic = diagnostic.replace(value, "[REDACTED]")
        return diagnostic[-10000:]

    def dc(self, store, *args, input=None, timeout=180, check=True):
        # One named operator container per tenant prevents a retry from starting
        # another writer after a worker/client crash. Volumes are never removed.
        one_off = bool(args and args[0] == "run")
        job = self.project(store) + "-operator"
        if one_off:
            args = ("run", "--name", job, *args[1:])
        try:
            result = run(["docker", "compose", "-p", self.project(store), "-f",
                          str(self.directory(store) / "compose.json"), *args],
                         input=input, timeout=timeout, check=False)
        except subprocess.TimeoutExpired:
            if one_off:
                run(["docker", "stop", "--time", "10", job], check=False)
            raise RuntimeError("Local runtime timed out; operator stop attempted. Inspect before retry; the job name prevents concurrent writers.") from None
        if check and result.returncode:
            diagnostic = self.safe_output(store, result.stdout + result.stderr)
            raise RuntimeError(f"M2 command failed (exit {result.returncode}):\n{diagnostic}")
        return result

    def sql(self, store, query):
        return self.dc(store, "exec", "-T", "db", "psql", "-v", "ON_ERROR_STOP=1", "-U", "postgres",
                       "-d", self.db_name(store), "-At", input=query.encode()).stdout.decode().strip()

    def shell(self, store, source):
        return self.dc(store, "run", "--rm", "-T", "--no-deps", "odoo", "shell",
                       input=source.encode(), timeout=600).stdout.decode()

    def prepare(self, store):
        create_config(self.directory(store), self.project(store), self.db_name(store))
        self.dc(store, "up", "-d", "--wait", "db", timeout=300)

    def initialize(self, store):
        # This path is only entered for never-activated test stores. Keep a completed
        # install after a worker crash; never reinitialize an active tenant.
        installed = self.sql(store, "SELECT to_regclass('public.ir_module_module') IS NOT NULL;") == "t"
        if installed:
            installed = self.sql(store, "SELECT count(*) FROM ir_module_module WHERE name IN ('website_sale','nasqo_store') AND state='installed';") == "2"
        if not installed:
            self.dc(store, "run", "--rm", "-T", "odoo", "install", timeout=1200)
        self.dc(store, "run", "--rm", "-T", "odoo", "upgrade", timeout=600)
        password = json.loads((self.directory(store) / "credentials.json").read_text())["admin"]
        self.shell(store, f"env.ref('base.user_admin').write({{'login': 'operator', 'password': {password!r}}})\nenv.cr.commit()\n")

    def verify(self, store):
        self.dc(store, "up", "-d", "odoo")
        probe = """import urllib.request
for path in ('/web/login', '/shop'):
    response = urllib.request.urlopen('http://127.0.0.1:8069' + path, timeout=20)
    assert response.status == 200
"""
        for _ in range(45):
            result = self.dc(store, "exec", "-T", "odoo", "python3", "-c", probe, timeout=50, check=False)
            if result.returncode == 0:
                return
            time.sleep(2)
        logs = self.dc(store, "logs", "--no-color", "--tail", "100", "odoo", check=False)
        diagnostic = self.safe_output(store, result.stdout + result.stderr + logs.stdout + logs.stderr)
        raise RuntimeError("Odoo login/shop readiness failed:\n" + diagnostic)

    def quarantine(self, store):
        if (self.directory(store) / "compose.json").exists():
            run(["docker", "stop", "--time", "10", self.project(store) + "-operator"], check=False)
            self.dc(store, "stop", "odoo", check=False)

    def gateway(self):
        stores = [s for s in self.registry.stores() if s["state"] == "active"]
        if not stores:
            raise ValueError("No verified active stores to route.")
        directory = private_directory(self.registry.directory / "gateway")
        servers = ["server { listen 8080 default_server; server_name _; return 421; }"]
        for store in stores:
            host = store["slug"] + ".nasqo.test"
            servers.append(f"""server {{
listen 8080; server_name {host};
client_max_body_size 8m;
location ^~ /web/database {{ return 403; }}
location ^~ /jsonrpc {{ return 403; }}
location ^~ /xmlrpc {{ return 403; }}
location / {{
proxy_pass http://{self.project(store)}:8069;
proxy_set_header Host {host};
proxy_set_header X-Forwarded-Host "";
proxy_set_header X-Forwarded-For "";
proxy_set_header X-Forwarded-Proto "";
proxy_set_header Forwarded "";
proxy_redirect off;
}}
}}""")
        (directory / "nginx.conf").write_text("events {}\nhttp { access_log off;\n" + "\n".join(servers) + "\n}")
        spec = {"services": {"gateway": {"image": GATEWAY_IMAGE,
                "ports": ["127.0.0.1:18069:8080"],
                "volumes": [f"{directory}/nginx.conf:/etc/nginx/nginx.conf:ro"],
                "networks": [s["slug"] for s in stores]}},
                "networks": {s["slug"]: {"external": True, "name": self.project(s) + "-frontend"} for s in stores}}
        (directory / "compose.json").write_text(json.dumps(spec))
        command = ["docker", "compose", "-p", f"nasqo-m2-{self.registry.instance}-gateway", "-f", str(directory / "compose.json")]
        run([*command, "up", "-d"], timeout=300)
        run([*command, "exec", "-T", "gateway", "nginx", "-t"])
        run([*command, "exec", "-T", "gateway", "nginx", "-s", "reload"])
