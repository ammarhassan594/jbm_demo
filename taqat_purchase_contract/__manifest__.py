# -*- coding: utf-8 -*-


{
    'name': "Purchase Contract",

    'summary': """
        This module contains Purchase Contract
        """,

    'description': """
       This module contains Purchase Contract
    """,

    'author': "TechUltra Solution",
    'website': "http://www.techultrasolution.com/",
    'category': 'Purchase',
    'version': '15.0.0.0.0.1',
    'depends': [
        'purchase', 'mail','purchase_stock'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/purchase_contract_sequence.xml',
        'views/purchase_contract_view.xml',
    ],

}
