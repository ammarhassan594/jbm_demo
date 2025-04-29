# -*- coding: utf-8 -*-
{
    'name': "JBM  Loan  Custom",
    'summary': """JBM  Loan  Custom""",
    'description': """JBM  Loan  Custom """,
    'author': "EBS",
    'website': "",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['matco_loan_management', 'payslip_reports', 'web_domain_field'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/restart_loan.xml',
        'views/hr_loan.xml',
    ],
    'demo': [],
}
