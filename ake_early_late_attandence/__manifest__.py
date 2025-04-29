# -*- coding: utf-8 -*-


{
    'name': "AKE Attendance Module",
    'summary': """
        This module contains custom modifications for Attendance Late Checkin Early Checkout
        """,
    'description': """
       This module contains custom modifications for Attendance Late Checkin Early Checkout
    """,
    'author': "Intalio EverTeam",
    'website': "https://www.intalio.com/",
    'maintainer': 'Muhammed-Ashraf',
    'category': 'Human Resources/Attendances',
    'version': '16.0',
    'depends': ['hr_payroll', 'hr', 'hr_attendance', 'jbm_salary_rules',
                'ebs_fusion_hr_employee', 'hr_holidays','taqat_payroll',
                'jbm_group_access_right_extended', 'ake_attendance_sheet', 'jbm_hr_payroll',
                'jbm_employee_custom', 'hr_employee_custom'],
    'data': [
        'security/ir.model.access.csv',
        'security/rule.xml',
        'data/ir_cron.xml',
        'data/ir_mail_activity.xml',
        'data/salary_structure_rules.xml',
        'wizard/justification_attendance_wizard_view.xml',
        'wizard/approve_wizard.xml',
        'views/hr_payslip.xml',
        # 'views/resource_calendar.xml',
        'views/hr_leave.xml',
        'views/hr_leave_type_view.xml',
        'views/allocations.xml',
        'views/hr_employee_view.xml',
        'views/justification_late_early_view.xml',
        'views/justification_type_view.xml',
        'views/employee_shortage_hour.xml',
        'views/res_config_setting_view.xml',
        'views/menu_item.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
