# -*- coding: utf-8 -*-
{
    'name': "jbm_account_payment",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['account', 'ebs_account_postchecks', 'ebs_jbm_account_custom', 'jbm_export_payment',
                'jbm_group_access_right_extended', 'jbm_minor_integration'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/account_payment.xml',
        'data/schedule_action.xml',
    ],
}
