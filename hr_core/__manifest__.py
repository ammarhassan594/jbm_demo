# -*- coding: utf-8 -*-
{
    'name': "hr_core Fusion",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.3',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'web'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/hr_core_views.xml',
        'data/data_sequence.xml',
    ],
    # 'assets': {
    #     'web.assets_backend': [
    #         # 'hr_core/static/src/js/core_changes.js'
    #     ],
    #     'web.assets_qweb': [
    #         'views/templates-qweb.xml'
    #     ]
    #
    # },
    # only loaded in demonstration mode

}
