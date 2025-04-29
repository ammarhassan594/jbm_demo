# -*- coding: utf-8 -*-
{
    'name': "Taqat Appraisal Module",

    'summary': """
        This module contains custom modifications for Appraisal
        """,

    'description': """
       This module contains custom modifications for Appraisal
    """,

    'author': "TechUltra Solution",
    'website': "http://www.techultrasolution.com/",
    'category': 'HR',
    'version': '15.0.0.0.0.1',
    'depends': ['hr_appraisal', 'hr_contract_custom'],
    'data': [
        'security/ir.model.access.csv',
        'report/jbm_hr_appraisal_report.xml',
        'report/appraisal_appraisal_a_report.xml',
        'report/appraisal_appraisal_b_report.xml',
        'views/hr_appraisal_view.xml',
        'views/hr_employee_view.xml',
    ],
}
