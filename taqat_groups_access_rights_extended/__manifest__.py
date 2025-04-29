# -*- coding: utf-8 -*-
{
    'name': "Taqat Configuration Module",

    'summary': """
        This module contains custom modifications for Configuration
        """,

    'description': """
       This module contains custom modifications for Configuration
    """,

    'author': "TechUltra Solution",
    'website': "http://www.techultrasolution.com/",
    'category': 'Configuration',
    'version': '15.0.0.0.0.1',
    'depends': ['ebs_fusion_hr_employee','hr_contract_custom','hr_holidays','hr_appraisal','sales_team','hr_recruitment','hr_payroll','account','hr_attendance','base',],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
    ],
}
