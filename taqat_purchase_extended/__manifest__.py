# -*- coding: utf-8 -*-
{
    'name': "Taqat Purchase Module",

    'summary': """
        This module contains custom modifications for Purchase
        """,

    'description': """
       This module contains custom modifications for Purchase
    """,

    'author': "TechUltra Solution",
    'website': "http://www.techultrasolution.com/",
    'category': 'Purchase',
    'version': '15.0.0.0.0.1',
    'depends': ['purchase', 'purchase_stock', 'ebs_fusion_purchase', 'jbm_group_access_right_extended', 'purchase_requisition'],
    'data': [
        'data/ir_sequence.xml',
        'data/mail_template_data.xml',
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        'report/purchase_order_report_inherit.xml',
        'report/purchase_order_approval_report.xml',
        'report/request_for_quotation.xml',
        'views/purchase_order_views.xml',
        'views/res_config_settings.xml',
        'views/rfq_terms.xml',
        'views/account_move_views.xml',
    ],
}
