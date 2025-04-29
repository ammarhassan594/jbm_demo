# -*- coding: utf-8 -*-
{
    'name': "hr_employee_custom Fusion",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.6',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_core', 'hr_contract_custom', 'hr_recruitment_custom', 'hr_skills', 'ebs_fusion_contacts',
                'mail', 'hr_payroll', 'hr_holidays'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/contact_relation_type_view.xml',
        'wizards/link_user_wizard.xml',
        'views/employee_custom.xml',
        'views/views.xml',
        'data/sequence.xml',
        'data/emp_cus_scheduled.xml',
        'views/event_type.xml',
        'views/employee_event.xml',
        'views/employee_color_combo.xml',
        'wizards/log_note_wizard_view.xml',
        'wizards/link_partner_wizrd_view.xml',
        'report/employee_applicant_photo.xml',
        'report/non_disclosure_agreement_report.xml',
        'report/terms_conditions_for_using_mobile_phone.xml',
        'data/cron_jobs.xml',
        'views/housing_settings_view.xml',
        'views/approve_employee_wiz.xml',
        'views/hr_applicant_custom.xml',
        'views/hr_payroll_custom.xml',
        'views/hr_department_views.xml',
        'views/hr_attendance.xml',
        # 'views/probation_wizard_custom.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hr_employee_custom/static/src/js/employee.js',

        ]
    },

}
