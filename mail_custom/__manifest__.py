# -*- coding: utf-8 -*-
{
    'name': "Mail Custom",
    'summary': """Add Customization to Chatter Buttons""",
    'description': """Add Customization to Chatter Buttons""",
    'author': "M.Deeb",
    'website': "",
    'category': 'Productivity/Discuss',
    'version': '0.1',
    'depends': ['mail', 'base'],
    'data': [
        'data/mail_template.xml',
        'views/mail_activity_views.xml',
    ],
    'demo': [],

    'assets': {
        'mail.assets_discuss_public': [
            'mail_custom/static/src/js/*.js',
        ],
        'web.assets_backend': [
            'mail_custom/static/src/js/chatter_custom.js',
        ],
    },
}
