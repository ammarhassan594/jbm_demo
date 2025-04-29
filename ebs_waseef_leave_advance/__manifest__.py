# -*- coding: utf-8 -*-
{
    'name': "ebs_waseef_leave_advance",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Moqbel Elsaidy",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_holidays', 'ebs_hr_leave_custom'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/leave_form_inherit_view.xml',
        'views/return_from_leave.xml',
        'wizard/early_return_from_leave_wizard.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
