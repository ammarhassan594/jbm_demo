# -*- coding: utf-8 -*-
{
    'name': "Ebs JBM Budget Custom",

    'summary': """
       Ebs JBM Budget Custom
        """,

    'description': """
       Ebs JBM Budget Custom
    """,

    'author': "TechUltra Solution",
    'website': "http://www.techultrasolution.com/",
    'category': 'accounting',
    'version': '15.0.0.0.0.1',
    'depends': ['account_budget', 'hr', 'base_dynamic_approval', 'ebs_capstone_hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/budget_preparation_view.xml'
    ],
}
