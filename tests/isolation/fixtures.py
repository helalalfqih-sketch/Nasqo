"""Executed only in a fresh synthetic M2 tenant through the Odoo shell."""
# The operator prepends slug, tenant_id and a fresh portal_password via stdin.
import json

marker = 'M2-' + slug.upper() + '-' + tenant_id[:12]
partner = env['res.partner'].create({'name': marker + '-BUYER', 'email': slug + '@example.invalid'})
product = env['product.template'].create({'name': marker + '-PRODUCT', 'list_price': 12.5, 'is_published': True})
order = env['sale.order'].create({
    'name': marker + '-ORDER', 'partner_id': partner.id,
    'order_line': [(0, 0, {'product_id': product.product_variant_id.id, 'product_uom_qty': 1, 'price_unit': 12.5})],
})
payload = (marker + '-PRIVATE-ATTACHMENT').encode()
attachment = env['ir.attachment'].create({
    'name': marker + '.txt', 'raw': payload, 'mimetype': 'text/plain',
    'res_model': 'sale.order', 'res_id': order.id, 'public': False,
})
env['res.users'].with_context(no_reset_password=True).create({
    'name': marker + '-PORTAL', 'login': 'portal-' + slug, 'password': portal_password,
    'partner_id': partner.id, 'group_ids': [(6, 0, [env.ref('base.group_portal').id])],
})
env.cr.commit()
print('NASQO_FIXTURE=' + json.dumps({
    'marker': marker, 'product_id': product.id, 'order_id': order.id,
    'attachment_id': attachment.id, 'store_fname': attachment.store_fname,
    'payload': payload.decode(),
}))
