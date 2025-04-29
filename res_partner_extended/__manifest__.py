# -*- coding: utf-8 -*-
{
    'name': "Res Partner Extended",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['ebs_fusion_contacts', 'ebs_fusion_documents'],

    # always loaded
    'data': [
        'views/res_partner_views.xml',
    ],
}
