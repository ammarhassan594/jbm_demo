# -*- coding: utf-8 -*-
{
    'name': "Ebs JBM Contact custom",
    'summary': """
        Ebs JBM Contact custom""",
    'description': """
    Ebs JBM Contact custom
    """,
    'author': "TechUltra Solution",
    'website': "http://www.techultrasolution.com/",
    'version': '15.0.0.0.0.1',
    'category': 'Uncategorized',
    'depends': ['contacts'],
    'data': [
        'security/ir.model.access.csv',
        'views/contact_classification_view.xml',
        'views/contact_custom_view.xml',
    ]
}
