# -*- coding: utf-8 -*-
{
    'name': "jbm_custom_account",

    'summary': """
    Customization of Account and Payment modules
       """,

    'description': """
    Customization of Account and Payment modules
    """,

    'author': "Mervat Mosaad",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.15',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'ebs_fusion_account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/groups.xml',
        'security/rules.xml',
        'views/account_move_view.xml',
        'views/account_payment_view.xml',
        'views/account_payment_register.xml',
    ],
}
