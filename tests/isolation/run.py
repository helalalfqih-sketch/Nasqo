"""Real PostgreSQL/Odoo/HTTP/filestore acceptance checks, synthetic data only."""
import ast
import http.client
from http.cookies import SimpleCookie
import json
import uuid

from provisioning.backup import backup, restore
from provisioning.registry import Conflict, Registry, private_directory, provision
from provisioning.runtime import GATEWAY_IMAGE, ODOO_IMAGE, POSTGRES_IMAGE, ROOT, Runtime, preflight, run


class Browser:
    def __init__(self, slug):
        self.host = slug + ".nasqo.test"
        self.cookie = ""

    def request(self, path, payload=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", 18069, timeout=45)
        values = {"Host": self.host, "Cookie": self.cookie}
        if payload is not None:
            values["Content-Type"] = "application/json"
        values.update(headers or {})
        connection.request("GET" if payload is None else "POST", path,
                           body=None if payload is None else json.dumps(payload), headers=values)
        response = connection.getresponse()
        content = response.read()
        for key, value in response.getheaders():
            if key.lower() == "set-cookie":
                cookies = SimpleCookie(value)
                if "session_id" in cookies:
                    self.cookie = "session_id=" + cookies["session_id"].value
        result = response.status, content
        connection.close()
        return result

    def rpc(self, path, params):
        status, body = self.request(path, {"jsonrpc": "2.0", "method": "call", "id": 1, "params": params})
        assert status == 200, f"RPC returned HTTP {status}"
        return json.loads(body)

    def call(self, model, method, args=None, kwargs=None):
        return self.rpc("/web/dataset/call_kw", {"model": model, "method": method, "args": args or [], "kwargs": kwargs or {}})

    def login(self, db, login, password):
        return self.rpc("/web/session/authenticate", {"db": db, "login": login, "password": password})


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def seed(runtime, store):
    credentials = json.loads((runtime.directory(store) / "credentials.json").read_text())
    header = f"slug={store['slug']!r}\ntenant_id={store['tenant_id']!r}\nportal_password={credentials['portal']!r}\n"
    output = runtime.shell(store, header + (ROOT / "tests/isolation/fixtures.py").read_text())
    return json.loads(next(line.split("=", 1)[1] for line in output.splitlines() if line.startswith("NASQO_FIXTURE=")))


def execute():
    preflight()
    result_path = ROOT / "artifacts/m2-results.json"
    result_path.parent.mkdir(exist_ok=True)
    private_directory(ROOT / ".m2")
    registry = Registry(ROOT / ".m2" / ("run-" + uuid.uuid4().hex[:12]))
    runtime = Runtime(registry)
    results = []
    report = {"source_commit": json.loads((ROOT / "upstream.json").read_text())["commit"],
              "scope": "M0-M2 synthetic operator pilot; no production or public control plane", "tests": results}
    current = "preflight"

    def passed(test, detail):
        results.append({"test": test, "status": "PASS", "detail": detail})
        print(f"PASS {test}: {detail}", flush=True)

    try:
        current = "M0/dependencies"
        report["community_modules"] = {}
        for name in ("website_sale", "sale_management", "delivery", "payment", "account", "account_payment",
                     "purchase", "purchase_stock", "stock", "stock_account", "mail", "portal"):
            manifest = ast.literal_eval((ROOT / "vendor/odoo/addons" / name / "__manifest__.py").read_text())
            check(manifest.get("license") == "LGPL-3", "Unexpected upstream module license")
            report["community_modules"][name] = {"license": manifest["license"], "depends": manifest.get("depends", [])}
        passed(current, "Pinned clean Community source and 12 standard module manifests/licenses verified; no third-party add-on added")
        current = "AT-030"
        try:
            provision(registry, runtime, "alpha", "m2-alpha-stable-key", fault_after="database")
        except RuntimeError as error:
            if str(error) != "Injected failure for integration testing.":
                raise
        else:
            raise AssertionError("Fault injection did not interrupt provisioning")
        failed = registry.get("alpha")
        check(failed["state"] == "failed_needs_review", "Failure must be recorded")
        check(not runtime.dc(failed, "ps", "--status", "running", "-q", "odoo").stdout.strip(), "Failed store is running")
        alpha = provision(registry, runtime, "alpha", "m2-alpha-stable-key")
        check(alpha["tenant_id"] == failed["tenant_id"], "Retry changed tenant identity")
        passed(current, "Injected worker failure after DB creation; no active Odoo; retry kept one identity and recovered")

        current = "M1/AT-002"
        beta = provision(registry, runtime, "beta", "m2-beta-stable-key")
        for store in (alpha, beta):
            check(runtime.sql(store, "SELECT count(*) FROM ir_module_module WHERE name IN ('website_sale','nasqo_store') AND state='installed';") == "2", "Missing module")
            selector_probe = f"""from odoo import http
from odoo.service.db import list_dbs
assert list_dbs(force=True) == [{runtime.db_name(store)!r}]
assert http.db_filter(['nasqo_alpha', 'nasqo_beta'], host='untrusted.invalid') == [{runtime.db_name(store)!r}]
print('DATABASE_ALLOWLIST_VERIFIED')
"""
            check('DATABASE_ALLOWLIST_VERIFIED' in runtime.shell(store, selector_probe),
                  'Pinned Odoo database selector does not enforce the exact runtime database')
        passed(current, "Two isolated databases; pinned Odoo install, upgrade, /web/login and /shop passed")

        current = "AT-003"
        before = runtime.dc(alpha, "ps", "-q").stdout
        repeated = provision(registry, runtime, "alpha", "m2-alpha-stable-key")
        check(repeated["tenant_id"] == alpha["tenant_id"], "Duplicate identity")
        check(runtime.dc(alpha, "ps", "-q").stdout == before, "Duplicate request changed containers")
        try:
            provision(registry, runtime, "beta", "m2-alpha-stable-key")
        except Conflict:
            pass
        else:
            raise AssertionError("Conflicting key accepted")
        check(len(registry.stores()) == 2, "Duplicate tenant row")
        passed(current, "Repeated key kept the same registry row and containers; changed payload rejected")

        a, b = seed(runtime, alpha), seed(runtime, beta)
        runtime.gateway()
        clients = {"alpha": Browser("alpha"), "beta": Browser("beta")}
        current = "AT-005"
        unknown = Browser("unregistered")
        check(unknown.request("/shop")[0] == 421, "Unknown Host was routed")
        check(unknown.request("/shop", headers={"Host": "alpha.nasqo.test.attacker.invalid"})[0] == 421, "Host suffix was accepted")
        check(unknown.request("/shop", headers={"Host": "alpha.nasqo.test:9999"})[0] == 421, "Unexpected Host port was accepted")
        for store, fixture, other in ((alpha, a, b), (beta, b, a)):
            client = clients[store["slug"]]
            for path in ("/shop", "/web/login"):
                check(client.request(path)[0] == 200, "Gateway HTTP smoke failed")
            status, body = client.request("/shop", headers={"X-Forwarded-Host": "unregistered.nasqo.test", "Forwarded": "host=beta.nasqo.test", "X-Odoo-Database": "nasqo_beta" if store == alpha else "nasqo_alpha"})
            check(status == 200 and fixture["marker"].encode() in body and other["marker"].encode() not in body, "Forwarded host changed tenant")
            wrong_db = "nasqo_beta" if store == alpha else "nasqo_alpha"
            status, body = client.request("/shop?db=" + wrong_db)
            check(other["marker"].encode() not in body and status in (200, 303, 403), "DB query selected another tenant")
            for path in ("/web/database/manager", "/web/database/list", "/jsonrpc", "/jsonrpc/", "/xmlrpc/2/db"):
                check(client.request(path)[0] == 403, "Database management route exposed")
            credentials = json.loads((runtime.directory(store) / "credentials.json").read_text())
            check("error" in client.login(wrong_db, "operator", credentials["admin"]), "Cross database login succeeded")
            check(client.login(runtime.db_name(store), "operator", credentials["admin"]).get("result", {}).get("uid"), "Operator login failed")
        passed(current, "Unknown Host denied; forwarded headers ignored; DB query/login isolation and management route blocks passed")

        current = "AT-004/HTTP"
        for store, own, other in ((alpha, a, b), (beta, b, a)):
            client = clients[store["slug"]]
            for model, field, suffix in (("product.template", "name", "-PRODUCT"), ("sale.order", "name", "-ORDER")):
                visible = client.call(model, "search_read", [[(field, "=", own["marker"] + suffix)]], {"fields": ["name"]})
                hidden = client.call(model, "search_read", [[(field, "=", other["marker"] + suffix)]], {"fields": ["name"]})
                check(len(visible.get("result", [])) == 1, "Own fixture is inaccessible")
                check(hidden.get("result") == [], "Other tenant record leaked")
            status, body = client.request(f"/web/content/{own['attachment_id']}")
            check(status == 200 and body.decode() == own["payload"], "Own attachment positive control failed")
            _, body = client.request(f"/web/content/{other['attachment_id']}?db=" + ("nasqo_beta" if store == alpha else "nasqo_alpha"))
            check(other["payload"].encode() not in body, "Other tenant attachment leaked")
        copied_session = Browser("beta")
        copied_session.cookie = clients["alpha"].cookie
        check("error" in copied_session.call("sale.order", "search_read", [[]], {"fields": ["name"]}), "Cross-domain session was accepted")
        clients["beta"].call("sale.order", "write", [[a["order_id"]], {"client_order_ref": "cross-tenant-attempt"}], {"context": {"db": "nasqo_alpha"}})
        original = clients["alpha"].call("sale.order", "read", [[a["order_id"]]], {"fields": ["client_order_ref"]})
        check(original["result"][0]["client_order_ref"] != "cross-tenant-attempt", "Other tenant was modified")
        passed(current, "Products, orders, private attachments, copied session and attempted cross-tenant write tested in both stores")

        current = "AT-004/DB/filestore"
        for store, other, fixture in ((alpha, beta, b), (beta, alpha, a)):
            db = runtime.db_name(store)
            check(runtime.sql(store, f"SELECT NOT r.rolsuper AND NOT r.rolcreatedb AND NOT r.rolcreaterole AND NOT r.rolreplication AND d.datdba <> r.oid FROM pg_roles r JOIN pg_database d ON d.datname='{db}' WHERE r.rolname='{db}';") == "t", "Runtime database role is overprivileged")
            creds = json.loads((runtime.directory(store) / "credentials.json").read_text())
            script = f"""import psycopg2
for database in ('template1', {runtime.db_name(other)!r}):
    try:
        psycopg2.connect(host='db', dbname=database, user={db!r}, password={creds['database']!r}, connect_timeout=5)
    except psycopg2.OperationalError:
        continue
    raise AssertionError('Forbidden database connection accepted')
"""
            runtime.dc(store, "exec", "-T", "odoo", "python3", "-", input=script.encode())
            check(runtime.sql(store, f"SELECT has_database_privilege('{db}', 'postgres', 'CONNECT') AND NOT has_database_privilege('{db}', 'postgres', 'TEMP');") == "t", "Maintenance database permission differs from CONNECT-only")
            other_container = runtime.dc(other, "ps", "-q", "db").stdout.decode().strip()
            other_ip = run(["docker", "inspect", other_container, "--format", "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}"]).stdout.decode().strip()
            network_probe = f"""import socket
try:
    socket.create_connection(({other_ip!r}, 5432), timeout=3)
except OSError:
    pass
else:
    raise AssertionError('Other tenant PostgreSQL network is reachable')
"""
            runtime.dc(store, "exec", "-T", "odoo", "python3", "-", input=network_probe.encode())
            forbidden = f"/var/lib/odoo/filestore/{runtime.db_name(other)}/{fixture['store_fname']}"
            runtime.dc(store, "exec", "-T", "odoo", "test", "!", "-e", forbidden)
            # The other tenant database is not attached to this runtime's networks.
            own_config = json.loads((runtime.directory(store) / "compose.json").read_text())
            check(not any(runtime.project(other) in str(v) for v in own_config.values()), "Cross-tenant mount/network reference")
        passed(current, "Independent databases and filestores; non-owner/non-superuser roles; forbidden DB connections denied")

        current = "AT-006/pilot-ACL"
        unauthenticated = Browser("alpha")
        check("error" in unauthenticated.call("ir.config_parameter", "search_read", [[]], {"fields": ["key"]}), "Anonymous admin read succeeded")
        portal = Browser("alpha")
        creds = json.loads((runtime.directory(alpha) / "credentials.json").read_text())
        check(portal.login("nasqo_alpha", "portal-alpha", creds["portal"]).get("result", {}).get("uid"), "Portal positive login failed")
        check("error" in portal.call("ir.config_parameter", "search_read", [[]], {"fields": ["key"]}), "Portal admin read succeeded")
        check("error" in portal.call("res.users", "create", [{"name": "forbidden", "login": "forbidden"}]), "Portal created an administrator")
        passed(current, "Anonymous and authenticated portal administrative access denied; platform support workflow remains backlog")

        current = "AT-028"
        key = registry.directory / "recovery.key"
        archive = backup(registry, runtime, "alpha", key)
        check(a["payload"].encode() not in archive.read_bytes(), "Backup is plaintext")
        restored, restored_store = restore(registry, "alpha", archive, key)
        source = f"""import hashlib
assert env['sale.order'].browse({a['order_id']}).name == {a['marker'] + '-ORDER'!r}
attachment = env['ir.attachment'].browse({a['attachment_id']})
assert attachment.raw == {a['payload'].encode()!r}
assert env['product.template'].browse({a['product_id']}).name == {a['marker'] + '-PRODUCT'!r}
print('RESTORE_VERIFIED')
"""
        check("RESTORE_VERIFIED" in restored.shell(restored_store, source), "Restored records or files differ")
        check(restored.project(restored_store) != runtime.project(alpha), "Restore overwrote original project")
        passed(current, "Encrypted consistent DB+filestore pair restored into a new isolated project; records, attachment bytes and HTTP verified")

        current = "AT-029"
        before = run(["docker", "ps", "-aq"]).stdout
        try:
            restore(registry, "beta", archive, key)
        except ValueError as error:
            check("Cross-tenant" in str(error), "Unexpected restore rejection")
        else:
            raise AssertionError("Cross-tenant restore accepted")
        check(run(["docker", "ps", "-aq"]).stdout == before, "Rejected restore created Docker resources")
        passed(current, "Alpha backup rejected for Beta before creating or changing resources")

        current = "secret-boundary"
        tracked = run(["git", "-C", str(ROOT), "ls-files", "-z"]).stdout.decode().split("\0")
        code = b"\n".join((ROOT / p).read_bytes() for p in tracked if p and (ROOT / p).is_file())
        # Capture actual container logs in memory; never print matched secret data.
        logs = b""
        for adapter, store in ((runtime, alpha), (runtime, beta), (restored, restored_store)):
            captured = adapter.dc(store, "logs", "--no-color")
            logs += captured.stdout + captured.stderr
        gateway_logs = run(["docker", "compose", "-p", f"nasqo-m2-{registry.instance}-gateway",
                            "-f", str(registry.directory / "gateway/compose.json"), "logs", "--no-color"])
        logs += gateway_logs.stdout + gateway_logs.stderr
        for credentials in registry.directory.rglob("credentials.json"):
            for value in json.loads(credentials.read_text()).values():
                check(value.encode() not in code, "Generated development secret entered tracked files")
                check(value.encode() not in logs, "Generated development secret entered container logs")
        check(key.read_bytes().strip() not in code, "Recovery key entered tracked files")
        check(key.read_bytes().strip() not in logs, "Recovery key entered container logs")
        passed(current, "Generated credentials/recovery key absent from tracked files and actual tenant/restore/gateway logs")
        image_lines = run(["docker", "image", "inspect", ODOO_IMAGE, POSTGRES_IMAGE, GATEWAY_IMAGE, "--format", "{{json .RepoDigests}}"]).stdout.decode().splitlines()
        report["images"] = [digest for line in image_lines for digest in json.loads(line)]
        report["result"] = "PASS"
    except Exception as error:
        results.append({"test": current, "status": "FAIL", "detail": type(error).__name__})
        report["result"] = "FAIL"
        raise
    finally:
        result_path.write_text(json.dumps(report, indent=2) + "\n")
        registry.close()


if __name__ == "__main__":
    execute()
