# -*- coding: utf-8 -*-


{
    'name': "AKE Attendance Sheet",
    'summary': """
        AKE Attendance Sheet Addons manage attendance information
        """,
    'description': """
        AKE Attendance Sheet Addons manage attendance information
    """,
    'author': 'Intalio EverTeam',
    'maintainer': 'Muhammed-Ashraf',
    'website': 'https://www.intalio.com/',
    'category': 'Human Resources/Attendance Sheet',
    'version': '16.0',
    'depends': ['hr', 'hr_attendance', 'hr_holidays', 'hr_employee_custom'],
    'data': [
        'data/ir_cron.xml',
        'security/ir.model.access.csv',
        'views/resource_calendar.xml',
        'views/hr_employee.xml',
        'views/hr_attendance_sheet_views.xml',
        'views/violation_balance.xml',
        'views/inherit_hr_leave_allocation_form_view.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
