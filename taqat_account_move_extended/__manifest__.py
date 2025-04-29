# -*- coding: utf-8 -*-
{
    'name': "Taqat Accounting Module",

    'summary': """
        This module contains custom modifications for Accounting
        """,

    'description': """
       This module contains custom modifications for Accounting
    """,

    'author': "TechUltra Solution",
    'website': "http://www.techultrasolution.com/",
    'category': 'Accounting',
    'version': '15.0.0.0.0.1',
    'depends': [
        'base','account','ebs_fusion_account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_company_extended_view.xml',
        # 'views/account_move_extended_view.xml',
        'wizards/approval_account_journal_entries_view.xml',
    ],
}
