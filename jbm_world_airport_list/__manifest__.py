# -*- coding: utf-8 -*-
{
    'name': "jbm_world_airport_list",

    'summary': """
        World Airport List""",

    'description': """
        World Airport List
    """,

    'author': "Moqbel Elseaedy",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '16.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'hr_contract'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/world_airport_views.xml',
        'views/hr_contract.xml',
    ],
}
