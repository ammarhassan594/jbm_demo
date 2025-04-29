# -*- coding: utf-8 -*-
{
    'name': "EBS Fusion Account Module",

    'summary': """
        This module contains custom modifications for ebs fusion Account
        """,

    'description': """
       This module contains custom modifications for ebs fusion Account
    """,

    'author': "Mustafa kantawala",
    'website': "http://www.ever-bs.com/",
    'category': 'CRM',
    'version': '15.0.0.0.1',
    'depends': [
        'base',
        'account',
        'account_budget',
        'ebs_fusion_contacts',
        'account_accountant',
        'ebs_fusion_services',
        'base_dynamic_approval'
    ],
    'data': [
        'data/sequence.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/product_template.xml',
        'report/proforma_invoice_report.xml',
        'data/mail_template.xml',
        'views/crossovered_budget_custom.xml',
        'views/ebs_budget_transfer.xml',
        'views/res_config_setting_custom.xml',
        'views/res_partner_custom.xml',
        # 'views/account_move_custom.xml',
        'views/crossovered_budget_lines_view_form_custom.xml',
        'views/ebs_crm_proposal_inherit.xml',
        'views/ebs_turnover.xml',
        'views/payment_receipt_template.xml',
        'views/partner_ledger_header_change_view.xml',
        'views/menu.xml',

    ]

}
