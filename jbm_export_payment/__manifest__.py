# -*- coding: utf-8 -*-

{
    'name': 'JBM Export Payment',
    'version': '15.0.0.0.0',
    'summary': """export payment details base on account number.""",
    'description': 'export payment details base on account number.',
    'category': 'Accounting',
    'author': "TechUltra Solution",
    'website': "http://www.techultrasolution.com/",
    'depends': ['account_reports'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/export_payment.xml',
        'views/account_payment_view_inherit.xml',
    ],
    'demo': [],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
