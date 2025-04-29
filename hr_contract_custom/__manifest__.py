# -*- coding: utf-8 -*-
{
    'name': "hr_contract Fusion",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.2',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_contract', 'hr_recruitment_custom', 'hr_core', 'survey', 'resource', 'hr_appraisal'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'report/job_offer_report.xml',
        'report/probation_assessment_report.xml',
        'report/probation_confirmation_letter_report.xml',
        'report/probation_extension_letter_report.xml',
        'report/resignation_report.xml',
        'report/salary_certificate_report.xml',
        'report/employment_contract_report.xml',
        'report/employment_offer_report.xml',
        'report/jbm_special_contract_report_template.xml',
        'report/jbm_custom_hr_contract_report.xml',
        'data/mail_template.xml',
        'data/data_sequence.xml',
        'wizard/job_offer_send_views.xml',
        'wizard/salary_certificate_wizard_view.xml',
        'wizard/employment_contract_wizard.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/contract_custom.xml',
        'views/contract_compensation.xml',
        'views/job_position_custom.xml',
        'views/contact_signatures.xml',
    ],
    # only loaded in demonstration mode

}
