# -*- coding: utf-8 -*-
{
    'name': "employee_absence_notification",

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
    'depends': ['base', 'hr', 'jbm_group_access_right_extended', 'dynamic_ooredoo_integration', 'employee_ooredoo_integration'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/ir_crone.xml',
        'data/mail_template.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
