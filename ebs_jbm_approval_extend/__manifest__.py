# -*- coding: utf-8 -*-
{
    'name': "EBS JBM Approval Extend",
    'summary': """
        EBS JBM Approval Extend""",
    'description': """
        EBS JBM Approval Extend
    """,
    'author': "TechUltra Solution",
    'website': "http://www.techultrasolution.com/",
    'category': 'Uncategorized',
    'version': '15.0.0.0.1',
    'depends': ['account', 'approvals', 'approvals_purchase', 'jbm_portal_self_service', 'stock', 'base_portal_user'],
    'data': [
        'security/ir.model.access.csv',
        'data/server_action.xml',
        'views/approval_request_view.xml',
        'views/approval_product_line_view.xml',
        'views/stock_location.xml',
        'views/stock_picking.xml',
        'views/hr_employee.xml',
        'views/purchase_order_view.xml',
        'report/approval_need_request.xml',
        'report/material_request_receipt.xml',
    ],
}
