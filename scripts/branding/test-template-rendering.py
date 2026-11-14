from types import SimpleNamespace
from markupsafe import Markup
from lxml import html
qweb=env['ir.qweb'].with_context(lang='ar_001')
company=SimpleNamespace(name='Synthetic Test Company',phone=False,email=False,website=False,email_secondary_color='#123b42',email_primary_color='#ffffff',uses_default_logo=True,id=0)
message=SimpleNamespace(body=Markup('<p>NASQO-SYNTHETIC-CONTENT</p>'),preview='',record_name='Synthetic Document')
values=dict(lang='ar_001',company=company,message=message,subtype=False,email_notification_force_header=False,email_notification_allow_header=False,email_notification_force_footer=True,email_notification_allow_footer=True,has_button_access=False,author_user=env.user,subtitles=[],is_discussion=True,record_name='Synthetic Document',tracking_values=[],email_add_signature=False,signature=False,show_unfollow=True,model_description='Synthetic')
for name in ['mail.mail_notification_layout','mail.mail_notification_light']:
    rendered=str(qweb._render(name,dict(values)))
    assert 'نسقو برو' in rendered
    assert 'odoo.com' not in rendered
    assert '/mail/unfollow' in rendered
    assert 'NASQO-SYNTHETIC-CONTENT' in rendered
    print('PASS rendered email identity / content / unfollow: '+name)
for name in ['web.report_layout','web.report_preview_layout']:
    wrapper=env['ir.ui.view'].create({'name':'NASQO PRO synthetic report wrapper','type':'qweb','arch_db':'<t t-call="'+name+'"><p>NASQO-SYNTHETIC-REPORT</p></t>'})
    rendered=str(qweb._render(wrapper.id,{'lang':'ar_001','title':False,'web_base_url':'http://127.0.0.1:8069','preview_css':''}))
    document=html.fromstring(rendered)
    assert document.findtext('.//title')=='تقرير نسقو برو'
    assert 'NASQO-SYNTHETIC-REPORT' in rendered
    print('PASS rendered report title / content: '+name)
view=env.ref('nasqo_backend_branding.settings_identity')
assert 'NASQO PRO' in view.arch_db
assert env['ir.config_parameter'].get_param('web.web_app_name')=='نسقو برو'
assert env.ref('base.partner_root').name in {'مساعد نسقو برو', 'نسقو برو'}
print('PASS app setting / system assistant identity')
env.cr.rollback()
