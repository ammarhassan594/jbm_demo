# -*- coding: utf-8 -*-
{
    'name': "jbm_employee_custom",

    'summary': """
        Customize Employee Profile""",

    'description': """
        Customize Employee Profile
    """,

    'author': "Mervat Mosaad",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['hr', 'hr_holidays', 'ebs_fusion_hr_employee', 'hr_payroll', 'jbm_hr_sponsor', 'hr_employee_custom',
                'ebs_lb_payroll',
                'attendance_api', 'jbm_employee_dependants', 'hr_fleet', 'jbm_group_access_right_extended'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/actual_duty_schedule.xml',
        'views/hr_department.xml',
        'views/hr_employee_views.xml',
        'views/hr_leave_type.xml',
        'views/employee_config.xml',
        'views/res_partner_bank.xml',
        'wizard/import_wizard.xml',

    ],
    # only loaded in demonstration mode
    'demo': [

    ],
}
