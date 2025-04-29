# -*- coding: utf-8 -*-
{
    'name': "JBM DMS Integration",
    'summary': """
        JBM DMS Integration adds dms integration feature to odoo addons 
        """,
    'description': """
        JBM DMS Integration adds dms integration feature to odoo addons :
          1- Budget
          2- Accounting
          3- Payments()
          4- Delivery Note ( ok)	 
          5-Employee Files(ok)
          6- Purchase agreement(ok)
          7- Procurement Order
          8- Leaves (ok)	
          9- Appraisal(ok)
          10 - Payroll Batch(ok)
          11- Payslip(ok)
          12- Vendor(ok)
          13- Inventory Report(ok) (stock.picking)
    """,
    'author': 'Intalio EverTeam',
    'maintainer': 'Muhammed-Ashraf',
    'website': 'https://www.intalio.com/',
    'category': 'Tools / API',
    'version': '15.0.1',
    'depends': ['stock', 'account', 'account_budget', 'documents',
                'hr', 'hr_holidays', 'purchase_requisition', 'hr_appraisal',
                'hr_payroll', 'base_dms_integration'],
    'data': [
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
