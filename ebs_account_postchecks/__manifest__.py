# -*- coding: utf-8 -*-
{
    'name': "Accounting Post Checks",

    'summary': """
         Module to modify check functionality and add post checks""",

    'description': """
       Module to modify check functionality and add post checks
    """,

    'author': "Jaafar Khansa",
    'website': "http://www.ever-bs.com/",
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/check_template_view.xml',
        'views/account_move_custom.xml',
        'views/payments_view_custom.xml',
        'views/menu.xml',

        'report/check_template.xml',
        'report/bank_transfer_report.xml',
        'report/report.xml',
        # 'views/templates.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
