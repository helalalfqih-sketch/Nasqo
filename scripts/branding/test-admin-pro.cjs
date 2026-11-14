// Runtime contract tests against the installed Odoo title and patch implementations.
const fs = require("node:fs");
const vm = require("node:vm");
const assert = require("node:assert/strict");
const { execFileSync } = require("node:child_process");
const container = process.env.NASQO_TEST_CONTAINER || "nasqo-rtl-pilot-odoo-1";
const source = (path) => execFileSync("docker", ["exec", container, "cat",
    "/usr/lib/python3/dist-packages/odoo/addons/web/static/src/" + path], {encoding: "utf8"});
const strip = (code) => code.replace(/import\s[\s\S]*?from\s["'][^"']+["'];/g, "")
    .replace(/export (const|function|class) /g, "$1 ");
const registry = {
    values: new Map(),
    category(key) {
        if (!this.values.has(key)) this.values.set(key, new Map());
        const values = this.values.get(key);
        return { add(k,v) { values.set(k,v); return this; }, remove(k) { values.delete(k); }, get(k) {return values.get(k);} };
    },
};
for (const key of ["support","odoo_account","preferences","log_out"]) {
    registry.category("user_menuitems").add(key, () => key);
}
const stubs = `
class Dialog { static defaultProps = {title: "Odoo", size: "lg"}; }
class ErrorDialog { static title = "Odoo Error"; }
class ClientErrorDialog extends ErrorDialog {}
class NetworkErrorDialog extends ErrorDialog {}
class RPCErrorDialog extends ErrorDialog {
    inferTitle() { this.title = odooExceptionTitleMap.get(this.props.exceptionName) || "Odoo Server Error"; }
}
class WarningDialog { inferTitle() {return this.props.title || "Odoo Warning";} }
class RedirectWarningDialog {setup() {this.title = this.props.subType || "Odoo Warning";} }
const odooExceptionTitleMap = new Map([["odoo.exceptions.AccessDenied", "Access Denied"]]);
`;
const tests = `
const service = titleService.start();
assert.equal(service.current, "نسقو برو | NASQO PRO");
service.setParts({action: "Applications"});
assert.ok(service.current.includes("Applications") && service.current.includes("NASQO PRO"));
service.setCounters({inbox: 3});
assert.ok(service.current.startsWith("(3) "));
service.setParts({action: false, nasqo_brand: false});
assert.equal(service.current, "(3) نسقو برو | NASQO PRO");
service.setCounters({inbox: 0});
assert.equal(service.current, "نسقو برو | NASQO PRO");
assert.ok(registry.category("user_menuitems").get("preferences"));
assert.ok(registry.category("user_menuitems").get("log_out"));
assert.equal(registry.category("user_menuitems").get("odoo_account"), undefined);
assert.equal(Dialog.defaultProps.size, "lg");
assert.equal(Dialog.defaultProps.title, "نسقو برو | NASQO PRO");
const denied = new RPCErrorDialog();
denied.props = {exceptionName: "odoo.exceptions.AccessDenied", type: "server"};
denied.inferTitle();
assert.equal(denied.title, "Access Denied");
const network = new RPCErrorDialog();
network.props = {type: "network"};
network.inferTitle();
assert.equal(network.title, "تعذر الاتصال بنسقو برو");
print("PASS runtime contracts: action titles, counters, fallback, account actions, dialog defaults, error meanings");
`;
const branding = fs.readFileSync(__dirname + "/../../addons/nasqo_backend_branding/static/src/js/branding.js", "utf8");
vm.runInNewContext(strip(source("core/utils/patch.js")) + "\n" +
    strip(source("core/browser/title_service.js")) + "\n" + stubs + "\n" +
    strip(branding) + "\n" + tests, {registry, document: {title: ""}, assert, print: console.log});
