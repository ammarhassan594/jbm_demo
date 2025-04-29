# -*- coding: utf-8 -*-
{
    'name': "EBS JBM Account Custom ",
    'summary': """
        Ebs JBM Account Account Custom """,
    'description': """
        Ebs JBM Account Account Custom 
    """,
    'author': "TechUltra Solution",
    'website': "http://www.techultrasolution.com/",
    'category': 'Uncategorized',
    'version': '15.0.0.0.1',
    'depends': ['account', 'analytic', 'base_dynamic_approval'],
    'data': [
        'views/account_analytic_account_custom_view.xml',
        'views/account_payment_custom_view.xml',
        'views/account_move.xml',
        'views/account_move_line.xml',
        'views/res_partner.xml',
    ],
}
