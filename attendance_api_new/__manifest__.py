# -*- coding: utf-8 -*-
{
    'name': "Attendance Api Fetching Module",

    'summary': """
        This module contains of create attendance from api
        """,

    'description': """
       This module contains of create attendance from api
    """,

    'author': "TechUltra Solution",
    'website': "http://www.techultrasolution.com/",
    'category': 'hr',
    'version': '15.0.0.0.0.3',

    'depends': ['hr_attendance', 'ebs_fusion_hr_employee', 'ake_early_late_attandence', 'jbm_portal_self_service',
                'jbm_group_access_right_extended'],

    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/ir_sequence_data.xml',
        'data/ir_cron.xml',
        'data/server_actions.xml',
        'views/res_config_setting_view.xml',
        'views/hr_attendance_view.xml',
        'views/hr_employee.xml',
        'views/machine_attendance_record.xml',
        'views/machine_attendance_issues.xml',
        'wizard/manual_attendance.xml',

    ],
}
