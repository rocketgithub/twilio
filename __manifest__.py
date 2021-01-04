# -*- coding: utf-8 -*-

{
    'name': 'Twilio',
    'category': 'Sales/CRM',
    'summary': 'Twilio integration',
    'version': '1.0',
    'description': """Twilio integration""",
    'author': 'aquíH',
    'website': 'http://aquih.com/',
    'depends': ['sms'],
    'data': [
        'views/phone_alias_views.xml',
        'security/ir.model.access.csv',
        #'data/twilio_data.xml',
    ],
    'installable': True,
}
