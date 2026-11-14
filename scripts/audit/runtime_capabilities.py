# Run as stdin to an authenticated Odoo shell --no-http in the intended environment.
# Schema and currency metadata only; not functional acceptance tests.
import ast, hashlib, json
from pathlib import Path
from datetime import datetime, timezone
from odoo.modules.module import get_module_path
module_names = [
 "hr_timesheet","barcodes","barcodes_gs1_nomenclature","resource","event","web","portal","auth_signup","uom","base_import","l10n_ye","report_xlsx","account_accountant","account_reports","documents","hr_contract","hr_payroll","nasqo_finance","nasqo_fx","nasqo_notifications","nasqo_partner_credit","nasqo_reports","sale_renting","whatsapp"
]
modules = []
for name in module_names:
    rec = env["ir.module.module"].search([("name","=",name)],limit=1)
    path = get_module_path(name, display_warning=False)
    mf = Path(path)/"__manifest__.py" if path else None
    data = ast.literal_eval(mf.read_text()) if mf and mf.is_file() else {}
    modules.append({"name":name,"state":rec.state if rec else "no_record","source_present":bool(data),"license":data.get("license") if data else None,"depends":data.get("depends",[])})
specs = {
 "account.move":(["state","move_type","line_ids","currency_id","reversed_entry_id"],["action_post","_reverse_moves","_check_balanced"]),
 "account.move.line":(["debit","credit","balance","currency_id","amount_currency","account_id"],[]),
 "account.payment":(["state","move_id","journal_id","payment_type","amount","currency_id"],["action_post"]),
 "account.journal":(["type","currency_id"],[]),
 "account.account":(["code","account_type","reconcile"],[]),
 "account.bank.statement":(["line_ids","balance_start","balance_end_real"],[]),
 "account.bank.statement.line":(["statement_id","move_id","amount"],[]),
 "account.analytic.line":(["account_id","unit_amount","amount","employee_id","task_id"],[]),
 "res.partner":(["credit_limit","credit","debit","use_partner_credit_limit"],[]),
 "res.company":(["account_opening_move_id","account_opening_date","currency_id"],[]),
 "res.currency":(["rounding","decimal_places"],["_convert"]),
 "res.currency.rate":(["name","rate","company_id","currency_id"],[]),
 "purchase.order":(["order_line","state","invoice_ids"],["button_confirm"]),
 "stock.picking":(["move_ids","state","location_id","location_dest_id"],["button_validate"]),
 "stock.move":(["product_uom_qty","quantity","value","product_id","location_id","location_dest_id"],["_action_done"]),
 "stock.move.line":(["quantity","product_id","location_id","location_dest_id"],[]),
 "stock.quant":(["quantity","reserved_quantity","value"],[]),
 "stock.warehouse":(["lot_stock_id","view_location_id"],[]),
 "stock.location":(["usage","location_id"],[]),
 "stock.valuation.layer":(["value","quantity"],[]),
 "ir.actions.report":(["report_type","report_name"],["_render_qweb_pdf"]),
 "base_import.import":(["file","res_model"],["execute_import"]),
 "sale.order":(["partner_credit_warning","order_line","state"],["action_confirm"])
}
models=[]
for name,(fields,methods) in specs.items():
    exists=name in env.registry
    model=env[name] if exists else None
    models.append({"name":name,"registered":exists,
      "fields":{key:({"type":model._fields[key].type,"required":bool(model._fields[key].required)} if exists and key in model._fields else None) for key in fields},
      "methods":{key:bool(exists and callable(getattr(model,key,None))) for key in methods}})
yer=env["res.currency"].with_context(active_test=False).search([("name","=","YER")],limit=1)
result={"captured_at_utc":datetime.now(timezone.utc).isoformat(),"modules":modules,"models":models,
 "yer_metadata":{"exists":bool(yer),"active":bool(yer.active) if yer else None,"rounding":yer.rounding if yer else None,"decimal_places":yer.decimal_places if yer else None},
 "limits":["Schema/source metadata only; no accounting, stock or permissions acceptance tests.","No customer or transaction records queried; no commits; rollback at end."]}
env.cr.rollback()
print("NASQO_CAPABILITIES_JSON:"+json.dumps(result,ensure_ascii=False,sort_keys=True))
