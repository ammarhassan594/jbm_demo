# -*- coding: utf-8 -*-
{
    'name': "dynamic_ooredoo_integration",

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
    'depends': ['base', 'hr'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/email_templates.xml',
        'templates/dynamic_integration_templates.xml',
        'views/res_config_setting_view.xml',
        'views/dynamic_integration_configuration_views.xml',
        # 'views/hr_employee_views.xml',

    ],
    # only loaded in demonstration mode
    'demo': [

    ],
}
