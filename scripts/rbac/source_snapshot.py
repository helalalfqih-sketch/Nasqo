"""Read-only Odoo-shell installed module and public source hash inventory."""
import json,hashlib,importlib
from odoo.modules.module import get_module_path
from pathlib import Path
from datetime import datetime,timezone
rows=env['ir.module.module'].search([('state','=','installed')])
data={'captured_at_utc':datetime.now(timezone.utc).isoformat(),'modules':sorted(rows.mapped('name')),'core':{},'nasqo_source_hashes':{}}
for name in ['base','sale','product','website']:
 p=Path(get_module_path(name))
 for rel in {'base':['models/res_users.py','models/ir_module.py','security/ir.model.access.csv'],'sale':['security/ir.model.access.csv'],'product':['security/ir.model.access.csv'],'website':['security/website_security.xml']}.get(name,[]):
  data['core'][name+'/'+rel]=hashlib.sha256((p/rel).read_bytes()).hexdigest()
for name in rows.filtered(lambda m:m.name.startswith('nasqo_')).mapped('name'):
 p=Path(get_module_path(name))
 data['nasqo_source_hashes'][name]={str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest() for f in p.rglob('*') if f.is_file() and '__pycache__' not in str(f) and f.suffix!='.pyc'}
env.cr.rollback()
print('NASQO_RBAC_PROVENANCE:'+json.dumps(data))
