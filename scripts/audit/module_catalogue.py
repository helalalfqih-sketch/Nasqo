# Run as stdin to an authenticated Odoo shell --no-http in the intended environment.
# Read-only module metadata; do not put shell logs or credentials in Git.
import json,ast,hashlib
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
from odoo.modules.module import get_module_path
model=env['ir.module.module'].with_context(lang='ar_001')
apps=model.search([('application','=',True)],order='name')
technical_names=['account','account_payment','account_accountant','account_reports','accountant','sale_management','sale','sale_stock','website','website_sale','delivery','purchase','purchase_stock','stock','stock_account','analytic','payment','payment_custom','payment_demo','mail','sms','spreadsheet','hr','hr_contract','hr_payroll','web_studio','website_livechat','im_livechat','sale_subscription','sale_renting','documents','sign','whatsapp','nasqo_store','nasqo_finance','nasqo_partner_credit','nasqo_fx','nasqo_reports','nasqo_notifications']
technical=model.search([('name','in',technical_names)])|model.search([('name','=like','nasqo_%')])
metadata={m.name:m for m in model.search([])}
cache={}
def inspect_manifest(name):
    if name in cache:return cache[name]
    try:directory=get_module_path(name)
    except Exception:directory=None
    path=Path(directory)/'__manifest__.py' if directory else None
    if not path or not path.is_file():
        result={'present':False}
    else:
        raw=path.read_bytes()
        try:
            m=ast.literal_eval(raw.decode())
            result={'present':True,'manifest_sha256':hashlib.sha256(raw).hexdigest(),'license':m.get('license','LGPL-3'),'license_declared':'license' in m,'version':m.get('version'),'installable':m.get('installable',True),'depends':m.get('depends',[]),'external_dependencies':m.get('external_dependencies',{}),'auto_install':m.get('auto_install',False)}
        except Exception as ex:result={'present':True,'parse_error':type(ex).__name__}
    cache[name]=result
    return result
def describe(m):
    manifest=inspect_manifest(m.name)
    dependencies=manifest.get('depends',m.dependencies_id.mapped('name'))
    missing_source=[];noninstalled=set();visited=set()
    def visit(name):
        if name in visited:return
        visited.add(name)
        child=metadata.get(name)
        child_manifest=inspect_manifest(name)
        if not child_manifest.get('present'):missing_source.append(name)
        if not child or child.state!='installed':noninstalled.add(name)
        for dep in child_manifest.get('depends',[]):visit(dep)
    for name in dependencies:visit(name)
    return {'id':m.id,'name':m.name,'title_ar':m.shortdesc,'category':m.category_id.display_name,'state':m.state,'db_license':m.license,'installed_version':m.latest_version,'source':manifest,'direct_dependencies':dependencies,'noninstalled_dependency_closure':sorted(noninstalled),'missing_source_dependency_closure':sorted(missing_source)}
action=env.ref('base.open_module_tree',raise_if_not_found=False)
data={'captured_at_utc':datetime.now(timezone.utc).isoformat(),'runtime_version':__import__('odoo').release.version,'catalogue_domain':[['application','=',True]],'catalogue_action':{'id':action.id,'domain':action.domain,'context':action.context} if action else None,'counts':{'applications':len(apps),'application_states':dict(Counter(apps.mapped('state'))),'all_module_states':dict(Counter(model.search([]).mapped('state')))},'applications':[describe(m) for m in apps],'technical_modules':[describe(m) for m in technical],'absent_technical_module_records':sorted(set(technical_names)-set(technical.mapped('name')))}
env.cr.rollback()
print('NASQO_CATALOGUE_JSON:'+json.dumps(data,ensure_ascii=False,separators=(',',':')))
