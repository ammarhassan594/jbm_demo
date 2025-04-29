# -*- coding: utf-8 -*-
{
    'name': "Base DMS Integration",
    'summary': """
        Base DMS Integration
        """,
    'description': """
    Base DMS Integration
    """,
    'author': "Intalio EverTeam",
    'website': "https://www.intalio.com/",
    'maintainer': 'Muhammed-Ashraf',
    'category': 'Tools / API',
    'version': '15.0.0.1',
    'depends': ['base', 'mail', 'report_xlsx'],
    'data': [
        'security/ir.model.access.csv',
        'data/server_action.xml',
        'views/dms_integration.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
