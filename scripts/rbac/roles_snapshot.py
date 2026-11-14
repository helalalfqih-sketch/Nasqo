"""Read-only Odoo-shell role inventory; no usernames or business records exported."""
import json
from collections import Counter
from pathlib import Path
from odoo.modules.module import get_module_path
refs=['base.group_user','base.group_system','base.group_erp_manager','base.group_portal','sales_team.group_sale_salesman','sales_team.group_sale_salesman_all_leads','sales_team.group_sale_manager','website.group_website_designer','stock.group_stock_user','stock.group_stock_manager','purchase.group_purchase_user','purchase.group_purchase_manager','account.group_account_invoice','account.group_account_manager']
group_map={ref:env.ref(ref,raise_if_not_found=False) for ref in refs}
users=env['res.users'].search([('active','=',True),('share','=',False)])
counts=Counter()
for u in users:
    key=tuple(sorted(ref for ref,g in group_map.items() if g and g in u.all_group_ids))
    counts[key]+=1
data={'active_internal_profiles':[{'groups':list(k),'count':v} for k,v in counts.items()],'nasqo_group_xmlids':env['ir.model.data'].search([('model','=','res.groups'),('module','=like','nasqo_%')]).mapped('complete_name'),'observed_group_definitions':[],'current_registered_users_fields':[x for x in ['group_ids','all_group_ids','share','active'] if x in env['res.users']._fields]}
for ref,g in group_map.items():
    if not g:continue
    data['observed_group_definitions'].append({'xmlid':ref,'implied_group_ids':g.implied_ids.get_external_id()})
p=get_module_path('nasqo_indexesstore_link',display_warning=False)
if p:
 mf=Path(p)/'__manifest__.py'
 data['indexesstore_link_manifest']=mf.read_text() if mf.exists() else None
env.cr.rollback()
print('NASQO_RBAC_LIVE_ROLES:'+json.dumps(data,ensure_ascii=False))
