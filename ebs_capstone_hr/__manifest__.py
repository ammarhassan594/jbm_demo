# -*- coding: utf-8 -*-
{
    'name': "ebs_capstone_hr",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'hr_holidays', 'hr_payroll', 'ebs_lb_payroll', 'web'],

    # always loaded
    'data': [
        'security/ebs_hr_security.xml',
        'security/ir.model.access.csv',
        'views/hr_leave_allocation_custom.xml',
        # 'views/views.xml',
        # 'views/templates.xml',

        'views/hr_document_type_view.xml',
        # 'cron-job/contract_cron_job_view.xml',
        'cron-job/probation_contract_cron_job_view.xml',
        'cron-job/document_type_cron_job_view.xml',
        # 'cron-job/birthday_cron_job_view.xml',
        # 'cron-job/birthday_event_cron_job_view.xml',
        # 'cron-job/birthday_event_reminder_cron_job_view.xml',
        # 'cron-job/performance_appraisal_cron_job.xml',
        # 'cron-job/vacation_cron_job_view.xml',

        'data/other_document_template.xml',
        'data/residence_permit_template.xml',
        'data/work_permit_template.xml',
        'data/health_card_template.xml',
        'data/hr_documents_data.xml',

        # 'data/hr_contract_reminder_cron.xml',
        'data/hr_contract_trial_end_reminder_email_template.xml',
        'data/contract_template.xml',

        'data/birthday_email_template.xml',
        'data/birthday_event_email_template.xml',
        'data/birthday_event_reminder_email_template.xml',

        'data/probation_email_template.xml',

        'data/performance_appraisal_email_template.xml',
        'data/vacation_email_template.xml',

        'data/ir_sequence_data.xml',
        'data/letter_request_email_template.xml',
        # 'views/ebs_hr_letter_request_view.xml',
        'views/hr_document_view.xml',
        'views/hr_department_views.xml',
        # 'views/hr_employee_custom.xml',
        'views/hr_employee.xml',
        # 'views/hr_contract_view_custom.xml',
        'report/report_actions.xml',
        'views/menu.xml',

        'views/hr_holidays_custom.xml',
        'views/hr_payslip_custom.xml',
        # 'report/hr_holidays_templates.xml',
        # 'report/report.xml',
        # 'report/noc_for_family_template.xml',
        # 'report/salary_transfer_template.xml',
        # 'report/experience_certificate_template.xml',
        # 'report/salary_certificate_template.xml',
        # 'report/gross_salary_template.xml',

        'views/ir_sequence.xml',
        # 'views/hr_employee_sponsor.xml',

    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    #     # 'views/hr_employee_custom.xml'
    # ],
}
