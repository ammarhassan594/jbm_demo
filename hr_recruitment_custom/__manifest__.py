# -*- coding: utf-8 -*-
{
    'name': "hr_recruitment Fusion",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'hr_contract', 'hr_recruitment', 'hr_recruitment_survey', 'hr_core', 'website_hr_recruitment', 'mail'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/mail_template.xml',
        'views/views.xml',
        'data/config_data.xml',
        'views/templates.xml',
        'views/job_custom.xml',
        'views/position_default_signatures.xml',
        'report/applicant_photo.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'hr_recruitment_custom/static/src/js/website_apply_form.js',

        ],
        'web.assets_backend': [
            'hr_recruitment_custom/static/src/css/recruitment.css',
        ]

    },
}
