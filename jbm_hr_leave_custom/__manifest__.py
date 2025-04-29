# -*- coding: utf-8 -*-
{
    'name': "jbm_hr_leave_custom",
    'summary': """JBM Holiday Custom""",
    'description': """JBM Holiday Custom""",
    'author': "EBS",
    'website': "",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'hr_holidays', 'jbm_hr_attendance','jbm_group_access_right_extended'],
    'data': [
        'data/mail_activity.xml',
        'data/mail_template.xml',
        'data/server_action.xml',
        'views/leave_type.xml',
        'views/hr_leave_views.xml',
    ],
    'demo': [],
}
