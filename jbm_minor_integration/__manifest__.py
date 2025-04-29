# -*- coding: utf-8 -*-
{
    'name': "JBM Minor Integration",
    'summary': """
       JBM Minor Integration addons now include API support for both POST and GET requests.
        """,
    'description': """
        JBM Minor Integration addons now include API support for both POST and GET requests.
    """,
    'author': "Intalio EverTeam",
    'website': "https://www.intalio.com/",
    'maintainer': 'Muhammed-Ashraf',
    'category': '',
    'version': '15.0.0.1',
    'depends': ['account', 'ebs_fusion_contacts', 'account_payment_custom'],
    'data': [
        'views/account_payment.xml',
        'views/payment_method.xml',
        'views/res_partner.xml',
        'views/purchase_order.xml',
        'views/product.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
