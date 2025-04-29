# -*- coding: utf-8 -*-
{
    'name': "ebs fusion asset",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "ebs",
    'website': "http://www.ever-bs.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'contacts', 'purchase', 'account', 'account_budget', 'account_asset', 'hr', 'ebs_fusion_services'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizards/create_asset_from_po_view.xml',
        'wizards/message_wiz_view.xml',
        'wizards/transfer_asset_view.xml',
        'views/views.xml',
        'views/asset_view_custom.xml',
        'views/asset_transfer_log.xml',
        'views/menu.xml',

    ],
}
