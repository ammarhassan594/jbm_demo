# -*- coding: utf-8 -*-
{
    'name': "jbm_hr_attendance",

    'summary': """
        This module is to manage the attendance of the employee during time interval""",

    'description': """
        This module is to manage the attendance of the employee during time interval
    """,

    'author': "Moqbel Elseaedy",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['hr', 'hr_holidays', 'jbm_payscale_configuration', 'jbm_employee_custom', 'taqat_payroll',
                'sla_activity', 'hr_payroll'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/hr_salary_rule.xml',
        'views/hr_leave_type.xml',
        'views/attendance_batch.xml',
        'views/hr_attendance_sheet.xml',
        'views/attendance_sheet_lines.xml',
        'views/hr_payslip.xml',
        # 'views/hr_employee.xml',
    ],
}
