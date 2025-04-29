# -*- coding: utf-8 -*-
{
    'name': "EBS - Payroll",

    'summary': """
        EBS modification for payroll""",

    'description': """
    EBS modification for payroll
    """,
    'author': "jaafar khansa",
    'website': "http://www.ever-bs.com/",
    'version': '0.1',

    # any module necessary for this one to work correctly
    'category': 'Payroll Localization',
    'depends': ['hr_payroll', 'hr_contract_reports', 'hr', 'hr_holidays', 'hr_employee_custom', 'account', 'jbm_hr_payroll',
                'base_dynamic_approval', 'res_partner_extended', 'jbm_hr_sponsor'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence_allowance_request.xml',
        'data/payslip_mail_template.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/additional_elements_types_views.xml',
        'views/additional_elements_view.xml',
        'views/transportation_rule_view.xml',
        # 'views/hr_contract_view_custom.xml',
        'views/hr_payslip_view_custom.xml',
        'views/payslip_line_view.xml',
        'views/hr_employee_view_custom.xml',
        'views/hr_payroll_structure_custom.xml',
        'views/hr_job_custom_view.xml',
        'views/hr_leave_type_view_custom.xml',
        'views/allowance_request_type_view.xml',
        'views/allowance_request_view.xml',
        # 'views/account_move_view.xml',
        'views/ticket_allowance_request_view.xml',
        'views/ebs_hr_eos_other_entitlements_types_view.xml',
        'views/ebs_mod_end_of_service_payment_view.xml',
        'views/ebs_hr_eos_config.xml',
        'views/report_payslip_templates.xml',
        'views/salary_report_config_views.xml',
        'views/wps_config_views.xml',
        'views/res_users_view.xml',
        'wizard/salary_report_views.xml',
        'wizard/payroll_payment.xml',
        'wizard/wps_report_views.xml',
        'views/payroll_expense_tranfser_view.xml',
        'views/import_allowances_configuration_view.xml',
        'views/import_allowances_view.xml',
        'views/employee_transfer_config_view.xml',
        'views/menus.xml',
        'wizard/send_mail_template_wizard_view.xml',
        'wizard/generate_invoice_wizard.xml',
        'views/jbm_account.xml',

    ]
}
