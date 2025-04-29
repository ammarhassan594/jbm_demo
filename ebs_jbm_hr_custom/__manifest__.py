# -*- coding: utf-8 -*-
{
    'name': "Ebs JBM Hr custom",
    'summary': """
        Customization in salary scale configuration""",
    'description': """
    Customization in salary scale configuration
    """,
    'author': "TechUltra Solution",
    'website': "http://www.techultrasolution.com/",
    'version': '15.0.0.0.0.1',
    'category': 'HR',
    'depends': ['hr', 'hr_recruitment', 'hr_contract', 'internal_regulations_api'],
    'data': [
        'security/ir.model.access.csv',
        'data/demo.xml',
        'views/hr_salary_allowance.xml',
        'views/hr_salary_scale_configuration.xml',
        'views/hr_contract_view.xml',
        'views/hr_employee_view.xml',
        'views/employee_activity.xml'
    ]
}
