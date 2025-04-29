# -*- coding: utf-8 -*-
{
    'name': "jbm_pension_configuration",

    'summary': """
        This module is to handle the Employee / Employer pension""",

    'description': """
        This module is to handle the Employee / Employer pension"
    """,

    'author': "Moqbel Elseaedy",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['hr', 'hr_payroll', 'hr_work_entry_contract_enterprise', 'jbm_salary_rules'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/pension_salary_rule.xml',
        'views/pension_configuration.xml',
        'views/hr_employee_views.xml',
    ],
}
