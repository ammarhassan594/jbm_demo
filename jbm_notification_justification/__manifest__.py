# -*- coding: utf-8 -*-
{
    'name': "JBM Notification Justification",
    'summary': """
    JBM Notification Justification add features to justification addons (ake_early_late_attandence)
    """,
    'description': """
    JBM Notification Justification add features to justification addons (ake_early_late_attandence)
    """,
    'author': "Intalio EverTeam",
    'website': "https://www.intalio.com/",
    'maintainer': 'Muhammed-Ashraf',
    'category': 'Human Resources/Attendances',
    'version': '16.0',
    'depends': ['ake_early_late_attandence', 'dynamic_ooredoo_integration'],
    'data': [

        # Data Files
        'data/ir_cron.xml',
        'data/mail_template.xml',

        # View Files
        'views/hr_attendance_view.xml',
        'views/res_config_settings.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}
