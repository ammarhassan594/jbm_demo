# -*- coding: utf-8 -*-
{
    'name': "EBS Fusion Hr Employee Module",

    'summary': """
        This module contains custom modifications for ebs fusion Hr Employee
        """,

    'description': """
       This module contains custom modifications for ebs fusion Hr Employee
    """,

    'author': "Mustafa kantawala",
    'website': "http://www.ever-bs.com/",
    'category': 'CRM',
    'version': '15.0.0.0.0.1',
    'depends': [
        'hr',
        'base',
        'ebs_fusion_documents',
        'documents_hr',
        'hr_payroll',
        'hr_employee_custom',
        'hr_holidays',
        'ebs_fusion_services',
        'ebs_lb_payroll'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/sequence.xml',
        'data/ir_cron.xml',
        'report/noc_generic.xml',
        'report/noc_to_waive_notice_period_report.xml',
        'report/salary_certificate_cbq_report.xml',
        'report/salary_certificate_qnb_report.xml',
        'report/salary_certificate_generic_qid_holder.xml',
        # 'report/outsourced_employee_liquor_permit.xml',
        'wizards/pay_card_wizard_view.xml',
        'report/salary_certificate_visa_report.xml',
        'report/salary_certificate_visa_cbq_report.xml',
        'wizards/letter_print_wizard_view.xml',
        'wizards/update_outsourced_status_wizard_view.xml',
        'wizards/outsourced_employee_report_wizard_view.xml',
        'wizards/workmens_compensation_view.xml',
        'views/hr_employee_custom.xml',
        'views/res_partner_bank_custom.xml',
        'views/documents_document_custom.xml',
        'views/employee_penalty_views.xml',
        'views/ebs_emp_residence_view.xml',
        'views/outsourced_employee_report_config_view.xml',
        'views/res_config_setting_view.xml',

    ],

    'qweb': [
        "static/src/xml/*.xml",
    ],
}
