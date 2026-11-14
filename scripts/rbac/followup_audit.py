"""Targeted follow-up: verify effective delegation, revocation and install wizard.

Only synthetic records are touched. The dangerous candidate role is restored
in finally; no invitation, email or external service request is sent.
"""
import json
from datetime import datetime, timezone
import requests

assert fixtures['database'] == 'nasqo_rbac_test'
BASE = 'http://127.0.0.1:8069'
checks, observations = [], {}
DENIED = {'odoo.exceptions.AccessError', 'odoo.exceptions.AccessDenied',
          'odoo.http.SessionExpiredException'}


def record(name, condition):
    checks.append({'name': name, 'status': 'PASS' if condition else 'FAIL'})


def rpc(session, model, method, args, kwargs=None):
    return session.post(BASE + '/web/dataset/call_kw/' + model + '/' + method,
        json={'jsonrpc': '2.0', 'method': 'call', 'id': 1, 'params': {
            'model': model, 'method': method, 'args': args, 'kwargs': kwargs or {}}}, timeout=60).json()


def forbidden(result):
    return result.get('error', {}).get('data', {}).get('name') in DENIED


clients = {}
for role in ['developer', 'delegated_users', 'merchant', 'merchant_union']:
    session = requests.Session()
    session.trust_env = False
    response = session.post(BASE + '/web/session/authenticate', json={
        'jsonrpc': '2.0', 'method': 'call', 'id': 1, 'params': {
            'db': fixtures['database'], 'login': fixtures['actors'][role]['login'],
            'password': credentials[role]}}, timeout=60).json()
    assert response.get('result', {}).get('uid') == fixtures['actors'][role]['id'], 'Synthetic login failed'
    clients[role] = session

admin, candidate = clients['developer'], clients['delegated_users']
uid = fixtures['actors']['delegated_users']['id']
record('candidate cannot read technical configuration before elevation', forbidden(
    rpc(candidate, 'ir.config_parameter', 'read', [[fixtures['config_id']]], {'fields': ['key']})))
try:
    elevated = rpc(candidate, 'res.users', 'write', [[uid], {'group_ids': [(4, fixtures['system_group_id'])]}])
    groups = rpc(admin, 'res.users', 'read', [[uid]], {'fields': ['all_group_ids']}).get('result', [])
    read = rpc(candidate, 'ir.config_parameter', 'read', [[fixtures['config_id']]], {'fields': ['key']})
    observations['unsafe_access_manager_candidate'] = {
        'self_write_accepted': elevated.get('result') is True,
        'effective_system_group_confirmed': bool(groups) and fixtures['system_group_id'] in groups[0]['all_group_ids'],
        'technical_read_after_elevation': bool(read.get('result')),
    }
    record('unsafe configuration demonstrably grants effective administration',
           all(observations['unsafe_access_manager_candidate'].values()))
finally:
    restored = rpc(admin, 'res.users', 'write', [[uid], {
        'group_ids': [(6, 0, fixtures['actors']['delegated_users']['direct_group_ids'])]}])
    record('candidate direct groups restored', restored.get('result') is True)
record('old session cannot read technical configuration after role revocation', forbidden(
    rpc(candidate, 'ir.config_parameter', 'read', [[fixtures['config_id']]], {'fields': ['key']})))

review = rpc(admin, 'base.module.install.review', 'create', [
    {'module_id': fixtures['uninstalled_probe_id']}]).get('result')
review_id = review[0] if isinstance(review, list) else review
assert type(review_id) is int, 'Synthetic review wizard was not created'
for role in ['merchant', 'merchant_union']:
    client = clients[role]
    record(role + ': cannot create administrative installation review', forbidden(
        rpc(client, 'base.module.install.review', 'create', [{'module_id': fixtures['uninstalled_probe_id']}])))
    record(role + ': guessed review public install method denied', forbidden(
        rpc(client, 'base.module.install.review', 'action_install_module', [[review_id]])))
state = rpc(admin, 'ir.module.module', 'read', [[fixtures['uninstalled_probe_id']]],
            {'fields': ['state']}).get('result', [])
record('wizard attacks leave empty probe uninstalled', bool(state) and state[0]['state'] == 'uninstalled')
result = {'captured_at_utc': datetime.now(timezone.utc).isoformat(), 'checks': checks,
    'observations': observations,
    'summary': {'pass': sum(x['status'] == 'PASS' for x in checks),
                'fail': sum(x['status'] == 'FAIL' for x in checks)},
    'limit': 'Positive reproduction of an intentionally privileged configuration is evidence of a role-design gap, not a secure-role acceptance.'}
print('NASQO_RBAC_FOLLOWUP:' + json.dumps(result, sort_keys=True))
