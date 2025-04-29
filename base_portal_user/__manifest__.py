# -*- coding: utf-8 -*-
{
    'name': "Base Portal User Access",

    'summary': """This Module Give Access To Backend Access group Users to back end""",
    'description': """This Module Give Access To Backend Access group Users to back end""",
    'author': "M.Deeb",
    'website': "",
    'category': 'Product',
    'version': '1.0.0.0.0.1',
    'license': 'LGPL-3',
    'depends': ['auth_signup', 'portal', 'calendar', 'base', 'mail', 'rating', 'resource',
                'appointment', 'hr', 'base_user_role'],
    'data': [
        # Security Files
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/record_rules.xml',

        # Data Files
        'data/security_role.xml',

        # View Files
        'views/menu.xml',
    ],
}
