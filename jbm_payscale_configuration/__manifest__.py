# -*- coding: utf-8 -*-
{
    'name': "jbm_payscale_configuration",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Moqbel Elseaedy",
    'website': "http://www.yourcompany.com",

    'category': 'HR',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'hr_contract', 'web_domain_field', 'jbm_employee_custom', 'hr_holidays'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/employee_payscale.xml',
        'views/hr_contract.xml',
        'views/hr_job_custom.xml',
    ],
}
