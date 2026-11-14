"""Read-only Odoo-shell explanation of observed lab ACLs and app menus."""
import hashlib
import json
from pathlib import Path
from odoo.modules.module import get_module_path

assert env.cr.dbname == 'nasqo_rbac_test'
model = env['ir.model']._get('ir.module.module')
rules = env['ir.model.access'].search([('model_id', '=', model.id), ('active', '=', True)])
result = {'module_acls': [], 'app_menus': [], 'source_hashes': {}}
for acl in rules:
    result['module_acls'].append({
        'xmlid': acl.get_external_id().get(acl.id),
        'group': acl.group_id.get_external_id().get(acl.group_id.id),
        'read': acl.perm_read, 'write': acl.perm_write,
        'create': acl.perm_create, 'unlink': acl.perm_unlink,
    })
for ref in ['base.menu_management', 'base.menu_apps', 'base.menu_administration']:
    menu = env.ref(ref)
    result['app_menus'].append({'xmlid': ref, 'name': menu.with_context(lang='en_US').name,
        'groups': list(menu.group_ids.get_external_id().values())})
path = Path(get_module_path('base_install_request'))
for relative in ['__manifest__.py', 'security/ir.model.access.csv',
                 'views/ir_module_module_views.xml']:
    result['source_hashes']['base_install_request/' + relative] = hashlib.sha256(
        (path / relative).read_bytes()).hexdigest()
env.cr.rollback()
print('NASQO_RBAC_ACL_EXPLANATION:' + json.dumps(result, sort_keys=True))
