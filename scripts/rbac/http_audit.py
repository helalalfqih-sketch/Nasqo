"""Actual HTTP/RPC audit, executed inside the isolated lab Odoo container.

The host prepends fixtures and credentials via stdin, not command arguments.
Only sanitized observations are printed. Policy gaps are reported separately
from execution failures; successful probe execution is not launch acceptance.
"""
import json
import time
from datetime import datetime, timezone
import requests

assert fixtures['database'] == 'nasqo_rbac_test'
BASE = 'http://127.0.0.1:8069'
checks, findings, observations = [], [], {}
DENIED = {'odoo.exceptions.AccessError', 'odoo.exceptions.AccessDenied',
          'odoo.http.SessionExpiredException'}


def record(name, condition, **details):
    checks.append({'name': name, 'status': 'PASS' if condition else 'FAIL', **details})


def error_kind(data):
    return data.get('error', {}).get('data', {}).get('name')


class Client:
    def __init__(self, role):
        self.role = role
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.headers['User-Agent'] = 'NASQO-synthetic-RBAC-audit/1.0'
        self.uid = None

    def rpc(self, model, method, args=None, kwargs=None, button=False, debug=False):
        path = '/web/dataset/' + ('call_button/' if button else 'call_kw/') + model + '/' + method
        if debug:
            path += '?debug=1'
        response = self.session.post(BASE + path, json={'jsonrpc': '2.0', 'id': 1, 'method': 'call',
            'params': {'model': model, 'method': method, 'args': args or [], 'kwargs': kwargs or {}}}, timeout=120)
        try:
            return response.json()
        except ValueError:
            return {'transport_status': response.status_code, 'non_json': True}

    def login(self):
        actor = fixtures['actors'][self.role]
        response = self.session.post(BASE + '/web/session/authenticate', json={
            'jsonrpc': '2.0', 'id': 1, 'method': 'call', 'params': {
                'db': fixtures['database'], 'login': actor['login'],
                'password': credentials[self.role]}}, timeout=90)
        data = response.json()
        self.uid = data.get('result', {}).get('uid')
        record(self.role + ': authenticate', self.uid == actor['id'])
        if not self.uid:
            raise RuntimeError('Synthetic authentication failed: ' + self.role)
        return self

    def get(self, path):
        return self.session.get(BASE + path, timeout=120, allow_redirects=False)


for attempt in range(45):
    try:
        if requests.get(BASE + '/web/login', timeout=4).status_code == 200:
            break
    except requests.RequestException:
        pass
    time.sleep(1)
else:
    raise RuntimeError('Audit runtime did not become ready')

clients = {role: Client(role).login() for role in fixtures['actors']}
admin = clients['developer']
record('developer is a regular authenticated user, not superuser ID 1', admin.uid != 1)


def allowed(name, response):
    record(name, 'result' in response and 'error' not in response,
           error_kind=error_kind(response))
    return response.get('result')


def denied(name, response):
    record(name, error_kind(response) in DENIED, error_kind=error_kind(response),
           unexpected_success='result' in response and 'error' not in response)


allowed('developer can read module metadata', admin.rpc('ir.module.module', 'read',
    [[fixtures['installed_probe_id']]], {'fields': ['name', 'state']}))
allowed('developer can write a synthetic technical setting', admin.rpc('ir.config_parameter', 'write',
    [[fixtures['config_id']], {'value': 'SYNTHETIC_ADMIN_UPDATED'}]))
record('developer downloads the synthetic private admin attachment',
       admin.get('/web/content/' + str(fixtures['admin_attachment_id']) + '?download=1').content == b'SYNTHETIC_ADMIN_PRIVATE')
allowed('developer can update a synthetic staff account', admin.rpc('res.users', 'write',
    [[fixtures['actors']['staff']['id']], {'name': 'SYNTHETIC STAFF updated by developer'}]))

methods = ['button_install', 'button_immediate_install', 'button_upgrade',
           'button_immediate_upgrade', 'button_uninstall', 'button_immediate_uninstall']
for role in ['merchant', 'merchant_union']:
    client = clients[role]
    allowed(role + ': edit product', client.rpc('product.template', 'write',
        [[fixtures['product_id']], {'description_sale': 'SYNTHETIC updated by ' + role}]))
    allowed(role + ': edit own-store order', client.rpc('sale.order', 'write',
        [[fixtures['order_id']], {'client_order_ref': 'SYNTHETIC ' + role}]))
    new_product = allowed(role + ': create product', client.rpc('product.template', 'create',
        [{'name': 'SYNTHETIC ' + role + ' created', 'list_price': 7}]))
    new_order = allowed(role + ': create quotation', client.rpc('sale.order', 'create',
        [{'partner_id': fixtures['partner_id'], 'user_id': client.uid,
          'order_line': [(0, 0, {'product_id': fixtures['product_variant_id'],
             'product_uom_qty': 1, 'price_unit': 25})]}]))
    product_readback = client.rpc('product.template', 'read', [[fixtures['product_id']]],
        {'fields': ['description_sale']}).get('result', [])
    order_readback = client.rpc('sale.order', 'read', [[fixtures['order_id']]],
        {'fields': ['client_order_ref']}).get('result', [])
    record(role + ': product update persisted', bool(product_readback) and
        product_readback[0]['description_sale'] == 'SYNTHETIC updated by ' + role)
    record(role + ': order update persisted', bool(order_readback) and
        order_readback[0]['client_order_ref'] == 'SYNTHETIC ' + role)
    for model, value in [('product.template', new_product), ('sale.order', new_order)]:
        ids = value if isinstance(value, list) else [value] if type(value) is int else []
        persisted = admin.rpc(model, 'read', [ids], {'fields': ['id']}).get('result', []) if ids else []
        record(role + ': created ' + model + ' persisted', bool(persisted) and
            sorted(x['id'] for x in persisted) == sorted(ids))
    for debug in [False, True]:
        mode = 'debug=1' if debug else 'normal'
        for method in methods:
            target = fixtures['uninstalled_probe_id'] if method.endswith('install') and not method.endswith('uninstall') else fixtures['installed_probe_id']
            denied(role + ': ' + method + ' ' + mode,
                   client.rpc('ir.module.module', method, [[target]], debug=debug))
        denied(role + ': technical config read ' + mode,
               client.rpc('ir.config_parameter', 'read', [[fixtures['config_id']]], {'fields': ['key', 'value']}, debug=debug))
        denied(role + ': technical config write ' + mode,
               client.rpc('ir.config_parameter', 'write', [[fixtures['config_id']], {'value': 'FORBIDDEN'}], debug=debug))
        denied(role + ': self administrative group injection ' + mode,
               client.rpc('res.users', 'write', [[client.uid], {'group_ids': [(4, fixtures['system_group_id'])]}], debug=debug))
        denied(role + ': change another user ' + mode,
               client.rpc('res.users', 'write', [[fixtures['actors']['staff']['id']], {'name': 'FORBIDDEN'}], debug=debug))
    denied(role + ': module batch operation', client.rpc('ir.module.module', 'button_install',
        [[fixtures['uninstalled_probe_id'], fixtures['installed_probe_id']]]))
    denied(role + ': call_button install', client.rpc('ir.module.module', 'button_immediate_install',
        [[fixtures['uninstalled_probe_id']]], button=True, debug=True))
    denied(role + ': direct module state mutation', client.rpc('ir.module.module', 'write',
        [[fixtures['uninstalled_probe_id']], {'state': 'to install'}]))
    denied(role + ': group inheritance injection', client.rpc('res.groups', 'write',
        [[fixtures['actors']['merchant']['direct_group_ids'][0]], {'implied_ids': [(4, fixtures['system_group_id'])]}]))
    denied(role + ': context spoofing cannot write configuration', client.rpc('ir.config_parameter', 'write',
        [[fixtures['config_id']], {'value': 'FORBIDDEN'}],
        {'context': {'uid': 1, 'sudo': True, 'allowed_company_ids': [fixtures['foreign_company_id']]}}))
    denied(role + ': arbitrary admin-user creation', client.rpc('res.users', 'create',
        [{'name': 'SYNTHETIC forbidden admin', 'login': role + '-forbidden-admin',
          'group_ids': [(6, 0, [fixtures['system_group_id']])]}]))
    invitation = client.rpc('res.users', 'create', [{'name': 'SYNTHETIC allowed-role employee',
        'login': role + '-allowed-staff', 'email': role + '-staff@example.invalid',
        'group_ids': [(6, 0, fixtures['actors']['staff']['direct_group_ids'])]}])
    observations[role + '_allowed_role_employee_creation'] = {
        'denied': error_kind(invitation) in DENIED, 'error_kind': error_kind(invitation)}
    record(role + ': cannot create any user through unrestricted res.users', error_kind(invitation) in DENIED)
    denied(role + ': synthetic admin attachment RPC read', client.rpc('ir.attachment', 'read',
        [[fixtures['admin_attachment_id']]], {'fields': ['raw']}))
    file_response = client.get('/web/content/' + str(fixtures['admin_attachment_id']) + '?download=1')
    record(role + ': guessed private admin attachment download denied',
        file_response.status_code in [403, 404] and b'SYNTHETIC_ADMIN_PRIVATE' not in file_response.content,
        http_status=file_response.status_code)
    for path in ['/nasqo/whatsapp/live', '/nasqo/whatsapp/qr']:
        response = client.get(path + '?debug=1')
        record(role + ': ' + path + ' denied', response.status_code == 403, http_status=response.status_code)
    response = client.rpc('nasqo.waha.preview.session', 'action_reset_mock', [[fixtures['preview_session_id']]])
    record(role + ': public preview method denied', error_kind(response) in DENIED | {'odoo.exceptions.UserError'},
        error_kind=error_kind(response))
    menu = client.get('/web/webclient/load_menus')
    menus = menu.json() if menu.status_code == 200 else {}
    observed = {key: str(mid) in menus for key, mid in fixtures['menu_ids'].items()}
    observations[role + '_technical_menus'] = observed
    for key, visible in observed.items():
        record(role + ': menu hidden ' + key, not visible)
    for path in ['/odoo/apps', '/odoo/settings', '/odoo/apps?debug=1']:
        response = client.get(path)
        observations[role + '_' + path] = {'http_status': response.status_code,
            'note': 'HTML shell status is not proof of authorized action or data access'}
    denied(role + ': app metadata behind a direct link', client.rpc('ir.module.module', 'read',
        [[fixtures['installed_probe_id']]], {'fields': ['name', 'state']}))

for role in ['portal', 'staff']:
    client = clients[role]
    denied(role + ': technical config denied', client.rpc('ir.config_parameter', 'read',
        [[fixtures['config_id']]], {'fields': ['key']}))
    denied(role + ': admin self-escalation denied', client.rpc('res.users', 'write',
        [[client.uid], {'group_ids': [(4, fixtures['system_group_id'])]}]))

support = clients['support_candidate']
support_read = support.rpc('res.partner', 'read', [[fixtures['partner_id']]], {'fields': ['name']})
support_file = support.get('/web/content/' + str(fixtures['partner_attachment_id']) + '?download=1')
observations['plain_internal_support_candidate'] = {
    'reads_synthetic_partner_without_grant': 'result' in support_read and 'error' not in support_read,
    'downloads_partner_attachment_without_grant': support_file.status_code == 200 and support_file.content == b'SYNTHETIC_BUYER_PRIVATE',
}
findings.append({'id': 'RBAC-04', 'status': 'BLOCKED',
    'reason': 'No dedicated support/grant/audit implementation exists. A plain internal-user profile must not be used as a restricted support role.',
    'evidence': observations['plain_internal_support_candidate']})

# Deliberate unsafe configuration control, not a claim of a Community vulnerability.
delegated = clients['delegated_users']
escalation = delegated.rpc('res.users', 'write', [[delegated.uid], {'group_ids': [(4, fixtures['system_group_id'])]}])
observations['access_management_role_self_elevation'] = {
    'allowed': 'result' in escalation and 'error' not in escalation,
    'error_kind': error_kind(escalation),
}
allowed('developer restores unsafe delegation candidate', admin.rpc('res.users', 'write',
    [[delegated.uid], {'group_ids': [(6, 0, fixtures['actors']['delegated_users']['direct_group_ids'])]}]))
findings.append({'id': 'RBAC-03', 'status': 'FAIL',
    'reason': 'A safe merchant profile cannot invite an allowed-role employee through res.users. Granting general access-management rights is not a safe substitute for a constrained invitation flow.',
    'evidence': observations['access_management_role_self_elevation']})

staff = clients['staff']
staff_file_path = '/web/content/' + str(fixtures['partner_attachment_id']) + '?download=1'
record('active staff can download its synthetic partner attachment',
       staff.get(staff_file_path).content == b'SYNTHETIC_BUYER_PRIVATE')
allowed('developer disables synthetic staff', admin.rpc('res.users', 'write', [[staff.uid], {'active': False}]))
after_disabled = staff.rpc('res.partner', 'read', [[fixtures['partner_id']]], {'fields': ['name']})
denied('disabled staff old session is rejected on next request', after_disabled)
expired_file = staff.get(staff_file_path)
record('disabled staff old file link discloses no bytes',
       expired_file.status_code in [302, 303, 401, 403, 404] and
       b'SYNTHETIC_BUYER_PRIVATE' not in expired_file.content,
       http_status=expired_file.status_code)

state = allowed('developer verifies module states after forbidden calls', admin.rpc('ir.module.module', 'read',
    [[fixtures['installed_probe_id'], fixtures['uninstalled_probe_id']]], {'fields': ['name', 'state']}))
record('forbidden module operations left states unchanged', isinstance(state, list) and
    {row['name']: row['state'] for row in state} == {
        'nasqo_rbac_state_probe': 'installed', 'nasqo_rbac_install_probe': 'uninstalled'})
setting = allowed('developer verifies technical setting after forbidden writes', admin.rpc('ir.config_parameter', 'read',
    [[fixtures['config_id']]], {'fields': ['value']}))
record('technical setting retained developer value', bool(setting) and setting[0]['value'] == 'SYNTHETIC_ADMIN_UPDATED')

for role in ['merchant', 'merchant_union']:
    groups = admin.rpc('res.users', 'read', [[clients[role].uid]], {'fields': ['all_group_ids']}).get('result', [])
    record(role + ': forbidden attempts left administrative groups absent', bool(groups) and
        not {fixtures['system_group_id'], fixtures['access_group_id']}.intersection(groups[0]['all_group_ids']))

# Positive controls use only the empty audit addon, never a business module.
for method, expected in [('button_immediate_install', 'installed'),
                         ('button_immediate_upgrade', 'installed'),
                         ('button_immediate_uninstall', 'uninstalled')]:
    allowed('developer: empty-addon ' + method,
        admin.rpc('ir.module.module', method, [[fixtures['uninstalled_probe_id']]], button=True))
    state = admin.rpc('ir.module.module', 'read', [[fixtures['uninstalled_probe_id']]],
                     {'fields': ['state']}).get('result', [])
    record('developer: empty-addon state after ' + method, bool(state) and state[0]['state'] == expected)

result = {'captured_at_utc': datetime.now(timezone.utc).isoformat(),
    'checks': checks, 'findings': findings, 'observations': observations,
    'summary': {'pass': sum(x['status'] == 'PASS' for x in checks),
                'fail': sum(x['status'] == 'FAIL' for x in checks)},
    'limits': ['Synthetic isolated database only; no live user permissions changed.',
        'Menu payload and direct HTTP/RPC tested; no authenticated visual browser walkthrough.',
        'No new cross-tenant DB/filestore, support grant, backup or financial acceptance tests.',
        'No outbound network, WhatsApp gateway secrets, real email, payments or customer data.']}
print('NASQO_RBAC_RESULT:' + json.dumps(result, sort_keys=True))
