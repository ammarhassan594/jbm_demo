# -*- coding: utf-8 -*-
{
    'name': "Dynamic Email Send",

    'summary': """
       Send Email Dynamically.""",

    'description': """
        Send Email Dynamically.
    """,

    'author': "Intalio",
    'website': "",

    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/dynamic_integration_configuration_views.xml',

    ],
    # only loaded in demonstration mode
    'demo': [

    ],
}
