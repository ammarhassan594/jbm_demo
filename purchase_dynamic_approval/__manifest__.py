# -*- coding: utf-8 -*-
{
    'name': 'Purchase Dynamic Approval',
    'summary': 'Allow to request approval based on approval matrix',
    'version': '15.0.0.0.0',
    'category': 'Purchase',
    'license': 'OPL-1',
    'depends': [
        'purchase',
        'purchase_requisition',
        'base_dynamic_approval',
    ],
    'data': [
        'views/purchase_order_inherit.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
