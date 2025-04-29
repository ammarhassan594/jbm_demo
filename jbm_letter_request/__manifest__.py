# -*- coding: utf-8 -*-
{
    'name': "JBM Letter Request",
    'summary': """
    JBM Letter Request add features request for printing letter 
    """,
    'description': """
    JBM Letter Request add features request for printing letter 
    """,
    'author': 'Intalio EverTeam',
    'maintainer': 'Muhammed-Ashraf',
    'website': 'https://www.intalio.com/',
    'category': 'HR',
    'version': '15.0.0.0',
    'depends': ['ebs_capstone_hr', 'jbm_portal_self_service',
                'jbm_pension_configuration'],
    'data': [
        'data/ir_sequence_data.xml',
        'data/letter_type_data.xml',
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'views/res_partner_views.xml',
        'views/jbm_letter_request.xml',
        'views/letter_request_type.xml',
        'views/hr_employee_view.xml',
        'views/res_config_setting_view.xml',
        'report/salary_certificate_with_details.xml',
        'report/work_certificate_template.xml',
        'report/report_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'jbm_letter_request/static/src/js/letter_dashboard.js',
        ]
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
