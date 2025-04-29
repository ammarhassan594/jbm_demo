# -*- coding: utf-8 -*-
{
    'name': "CTS API",

    'summary': """CTS API""",

    'author': "M.Deeb",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'taqat_purchase_extended', 'jbm_minor_integration'],
    'data': [
        'data/cron.xml',
        'views/res_config_setting_view.xml',
        'views/purchase_order.xml',
        'views/account_move.xml',
    ],

}
