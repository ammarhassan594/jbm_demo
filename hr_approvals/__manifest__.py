# -*- coding: utf-8 -*-
{
    'name': "hr_approvals Fusion",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1.11',

    # any module necessary for this one to work correctly
    'depends': ['base', 'approvals', 'hr_core', 'hr_contract_custom', 'hr_employee_custom', 'mail',
                'ebs_fusion_account', 'dynamic_ooredoo_integration'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/approval_security.xml',
        'security/approval_request.xml',
        'data/approval_category.xml',
        'data/approver_email.xml',
        'report/approvals_report.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/resignation_reasons.xml',
        'views/create_transfer_event_wiz.xml',
        'views/employee_event_type_custom.xml',
        'views/account_budget.xml',
        'views/request_type.xml',
    ],
    # only loaded in demonstration mode

}
