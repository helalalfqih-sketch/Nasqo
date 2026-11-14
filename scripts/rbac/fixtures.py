"""Odoo-shell fixture body. Host prepends private credentials through stdin.

Writes are allowed only in the explicitly named disposable RBAC database.
No real partner, product, login or external service identity is used.
"""
import json

assert env.cr.dbname == 'nasqo_rbac_test', 'Refusing a non-audit database'
assert not env['res.users'].search_count([('login', '=', 'rbac-merchant')]), 'Use a fresh database'
context = dict(no_reset_password=True, tracking_disable=True, mail_create_nosubscribe=True)
company = env.ref('base.main_company')
merchant_groups = ['base.group_user', 'sales_team.group_sale_manager',
                   'product.group_product_manager', 'base.group_partner_manager']
profiles = {
    'developer': merchant_groups + ['base.group_system', 'stock.group_stock_manager',
        'purchase.group_purchase_manager', 'account.group_account_manager', 'website.group_website_designer'],
    'merchant': merchant_groups,
    'merchant_union': merchant_groups + ['stock.group_stock_manager',
        'purchase.group_purchase_manager', 'website.group_website_restricted_editor'],
    'staff': ['base.group_user', 'sales_team.group_sale_salesman'],
    'portal': ['base.group_portal'],
    'support_candidate': ['base.group_user'],
    'delegated_users': merchant_groups + ['base.group_erp_manager'],
}
actors = {}
for role, refs in profiles.items():
    groups = [env.ref(ref).id for ref in refs]
    values = {'name': 'SYNTHETIC RBAC ' + role, 'login': 'rbac-' + role,
              'password': credentials[role], 'email': role + '@example.invalid',
              'group_ids': [(6, 0, groups)], 'company_id': company.id,
              'company_ids': [(6, 0, [company.id])], 'lang': 'en_US'}
    if role == 'developer':
        user = env.ref('base.user_admin')
        user.with_context(**context).write(values)
    else:
        user = env['res.users'].with_context(**context).create(values)
    actors[role] = {'id': user.id, 'login': values['login'], 'group_refs': refs,
                    'direct_group_ids': groups,
                    'system': user.has_group('base.group_system'),
                    'access_manager': user.has_group('base.group_erp_manager')}
assert all(not actors[role]['system'] and not actors[role]['access_manager']
           for role in ['merchant', 'merchant_union', 'staff', 'portal', 'support_candidate'])

partner = env['res.partner'].with_context(**context).create({
    'name': 'SYNTHETIC RBAC buyer', 'email': 'buyer@example.invalid',
    'company_id': company.id,
})
product = env['product.template'].with_context(**context).create({
    'name': 'SYNTHETIC RBAC product', 'list_price': 25, 'company_id': company.id,
})
order = env['sale.order'].with_context(**context).create({
    'partner_id': partner.id, 'user_id': actors['merchant']['id'],
    'company_id': company.id, 'client_order_ref': 'SYNTHETIC RBAC order',
    'order_line': [(0, 0, {'product_id': product.product_variant_id.id,
        'product_uom_qty': 1, 'price_unit': 25})],
})
private = env['ir.config_parameter'].create({
    'key': 'nasqo.rbac.admin_marker', 'value': 'SYNTHETIC_ADMIN_VALUE',
})
attachment = env['ir.attachment'].create({
    'name': 'synthetic-rbac-admin.txt', 'raw': b'SYNTHETIC_ADMIN_PRIVATE',
    'res_model': 'ir.config_parameter', 'res_id': private.id,
    'mimetype': 'text/plain', 'public': False,
})
partner_attachment = env['ir.attachment'].create({
    'name': 'synthetic-rbac-buyer.txt', 'raw': b'SYNTHETIC_BUYER_PRIVATE',
    'res_model': 'res.partner', 'res_id': partner.id,
    'mimetype': 'text/plain', 'public': False,
})
foreign_company = env['res.company'].with_context(**context).create({'name': 'SYNTHETIC other company'})
module_model = env['ir.module.module']
installed_probe = module_model.search([('name', '=', 'nasqo_rbac_state_probe')], limit=1)
uninstalled_probe = module_model.search([('name', '=', 'nasqo_rbac_install_probe')], limit=1)
assert installed_probe.state == 'installed' and uninstalled_probe.state == 'uninstalled'
menu_ids = {}
for ref in ['base.menu_administration', 'base.menu_apps', 'base.menu_management',
            'nasqo_whatsapp_center.menu_whatsapp_root']:
    record = env.ref(ref, raise_if_not_found=False)
    if record:
        menu_ids[ref] = record.id
assert 'base.menu_administration' in menu_ids and 'base.menu_apps' in menu_ids
result = {'database': env.cr.dbname, 'actors': actors, 'profiles': profiles,
    'company_id': company.id, 'foreign_company_id': foreign_company.id,
    'partner_id': partner.id, 'product_id': product.id,
    'product_variant_id': product.product_variant_id.id, 'order_id': order.id,
    'config_id': private.id, 'admin_attachment_id': attachment.id,
    'partner_attachment_id': partner_attachment.id,
    'installed_probe_id': installed_probe.id, 'uninstalled_probe_id': uninstalled_probe.id,
    'system_group_id': env.ref('base.group_system').id,
    'access_group_id': env.ref('base.group_erp_manager').id,
    'preview_session_id': env.ref('nasqo_waha_qr_preview.nasqo_demo_session').id,
    'menu_ids': menu_ids,
    'modules': sorted(module_model.search([('state', '=', 'installed')]).mapped('name')),
}
env.cr.commit()
print('NASQO_RBAC_FIXTURES:' + json.dumps(result, sort_keys=True))
