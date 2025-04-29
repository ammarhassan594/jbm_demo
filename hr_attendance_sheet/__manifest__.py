# -*- coding: utf-8 -*-
{
    'name': "HR Attendance Sheet And Policies",

    'summary': """Managing  Attendance Sheets for Employees
        """,

    'description': """
        
    """,


    'category': 'hr',
    'version': '13.0.1.0.0',
    'images': ['static/description/bannar.jpg'],

    # any module necessary for this one to work correctly
    'depends': ['hr_attendance', 'hr_holidays', 'project', 'hr_payroll', 'ohrms_overtime', 'matco_loan_management', 'ebs_waseef_leave_advance', 
                'ebs_lb_payroll'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/hr_attendance_sheet_view.xml',
        'views/hr_attendance_sheet_view_custom.xml',
        'views/hr_attendance.xml',
        'views/overtime_request_custom.xml',
        'views/resource_calendar_views.xml',
        'data/ebs_hr_attendendce_sheet.xml',
        'data/leave_advance_site_rule.xml',
        'data/salary_rule_advance_food.xml',
        # 'data/input_rules_advance_salary.xml',
        # 'data/salary_rules_advance_salary.xml',
    ],

    'license': 'OPL-1',
}
