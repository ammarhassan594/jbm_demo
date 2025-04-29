# -*- coding: utf-8 -*-
{
    'name': "account_reporting",
    'summary': """""",
    'description': """""",
    'author': "EBS",
    'website': "",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'jbm_minor_integration'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/pdc_checks.xml',
        'wizard/bank_receon.xml',
        'wizard/bank_statement.xml',
        'views/account_type.xml',
        'views/res_partner_bank_view.xml',
        # 'views/account.xml',
    ],
    'demo': [],
}
