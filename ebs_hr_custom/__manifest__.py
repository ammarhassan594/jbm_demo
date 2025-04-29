# -*- coding: utf-8 -*-
{
    'name': "EBS-HR ",

    'summary': """
        EBS modification for HR""",

    'description': """
    EBS modification for HR
    """,

    'author': "Maria L Soliman, Moqbel Elsaidy",
    'website': "https://www.everbsgroup.com/",
    'version': '0.1',

    # any module necessary for this one to work correctly
    'category': 'Human Resources',
    'depends': ['hr', 'project', 'uom', 'analytic', 'timesheet_grid', 'hr_timesheet', 'hr_payroll', 'ebs_capstone_hr',
                'web_domain_field', 'hr_org_chart', 'report_xlsx', 'hr_vacation_mngmt'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/rule.xml',
        'security/ir.model.access.csv',
        'views/employee_event_view.xml',
        'views/emergency_contact.xml',
        'views/hr_employee_custom.xml',
        'views/hr_contract_custom.xml',
        'views/hr_job_custom.xml',
        'views/hr_template.xml',
        'views/hr_department.xml',
        'views/employee_payroll_group.xml',
        'views/permanent_employees_pay_scale.xml',
        'views/menu.xml',
        'views/res_partner_bank.xml',
        'views/res_users_view.xml',
        'views/res_country.xml',
        'views/settings.xml',
        'wizard/custom_report_view.xml',
        'wizard/employee_departure.xml',
        'views/settings.xml',
        'views/resource_calender_view.xml',
        'data/cron_job.xml',
        'data/mail_template.xml',
        # 'data/cron_job_for_masterlist.xml',
        'data/mail_users_template.xml',
        'views/profession_view.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ]
}
