# -*- coding: utf-8 -*-
{
    'name': "EBS HR Leave",

    'summary': """
        EBS modification for HR Leave""",

    'description': """
    EBS modification for HR Leave
    """,

    'author': "Maria L Soliman, Moqbel Elsaidy, Mohammed Ashraf",
    'website': "https://www.everbsgroup.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list

    'version': '0.1',

    # any module necessary for this one to work correctly
    'category': 'Human Resources',
    'depends': ['base', 'web_domain_field', 'hr_holidays',
                ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/cron_job.xml',
        'data/mail_activity.xml',
        'views/hr_leave_custom.xml',
        'views/leave_planning_view.xml',
        'views/res_config_settings.xml',
        'data/leave_menu.xml',
        'data/mail_template.xml'
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
    'assets': {
        'web.assets_qweb': [
            'ebs_hr_leave_custom/static/src/xml/*.xml',
        ],
    }
}
