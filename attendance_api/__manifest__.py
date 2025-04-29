# -*- coding: utf-8 -*-
{
    'name': "Attendance Api",

    'summary': """
        This module contains of create attendance from api
        """,

    'description': """
       This module contains of create attendance from api
    """,

    'author': "TechUltra Solution",
    'website': "http://www.techultrasolution.com/",
    'category': 'hr',
    'version': '15.0.0.0.0.1',
    'depends': ['hr_attendance'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_attendance_view.xml',
        # 'views/hr_employee_view.xml',
        'views/res_config_setting_view.xml',
        'views/attendance_api_log_view.xml'
    ],
}
