# -*- coding: utf-8 -*-
{
    'name': "Account Payment Customisation",

    'summary': """
         Custom Payment reports""",

    'description': """
     Custom Payment reports
    """,

    'author': "TUS",
    'website': "https://www.techultrasolutions.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '15.0.0',

    # any module necessary for this one to work correctly
    'depends': ['account', 'account_budget', 'ebs_fusion_services', 'partner_bank', 'ebs_jbm_account_custom'],

    # always loaded
    'data': [
        'data/server_action.xml',
        'views/account_payment_views.xml',
        'views/account_budget_post_views.xml',
        'report/payment_test.xml',
        'report/payment_transfer_report.xml',
        'report/payment_method_report.xml',
        'report/payment_cash_receipt_report.xml',
        'report/report.xml',
        # 'report/payment_check.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
