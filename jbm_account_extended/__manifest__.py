# -*- coding: utf-8 -*-
{
    'name': "jbm_account_extended",

    'summary': """
        Customization Of Account""",

    'description': """
        Customization Of Account
    """,

    'author': "Mervat Mosaad",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'base_dynamic_approval', 'jbm_group_access_right_extended'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/server_actions.xml',
        'data/mail_activity.xml',
        'views/account_account_views.xml',
        'views/account_move_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
