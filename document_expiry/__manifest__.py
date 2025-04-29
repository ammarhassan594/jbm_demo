# -*- coding: utf-8 -*-
{
    'name': "document_expiry",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Mervat Mosaad",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'documents', 'ebs_fusion_documents'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/ebs_document_type.xml',
        'data/ir_cron.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
