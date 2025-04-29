# -*- coding: utf-8 -*-
{
    'name': "EBS Fusion Purchase Module",

    'summary': """
        This module contains custom modifications for ebs fusion purchase
        """,

    'description': """
       This module contains custom modifications for ebs fusion purchase
    """,

    'author': "Mustafa Kantawala",
    'website': "http://www.ever-bs.com/",
    'category': 'CRM',
    'version': '15.0.0.0.1',
    'depends': [
        'purchase', 'ebs_fusion_account', 'base_automation', 'taqat_config_extended', 'ebs_jbm_budget_custom'
    ],
    'data': [
        'views/purchase_order_custom.xml',
    ],
    'pre_init_hook': 'pre_init_hook',
}
