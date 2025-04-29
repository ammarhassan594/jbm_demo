# -*- coding: utf-8 -*-
{
    'name': "SLA Activity Type",

    'summary': """
        Add new feature to SLA Activity Type module
        """,

    'description': """
        Add new feature to SLA Activity Type module
    """,
    'author': "Intalio EverTeam",
    'website': "https://www.intalio.com/",
    'maintainer': 'Mervet,Muhammed-Ashraf',
    'category': 'Tools',
    'version': '15.0',
    'depends': ['base', 'mail', 'base_dynamic_approval',
                'approvals', 'hr_approvals'],
    'data': [
        'security/ir.model.access.csv',
        'views/sla_activity_type_view.xml',
        'views/mail_activity_type_view.xml',
        'views/dynamic_approval_view.xml',
        'views/approval_category_approver.xml',
        'views/approval_request.xml',
        'views/ir_model.xml',
        'wizard/activity_type_wizard.xml',
    ],

    'assets': {
        'web.assets_qweb': [
            'sla_activity_type/static/src/components/chatter_topbar/chatter_top_bar.xml',
        ],
        'web.assets_backend': [
            'sla_activity_type/static/src/js/new_chatter.js',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
