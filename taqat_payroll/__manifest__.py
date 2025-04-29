# -*- coding: utf-8 -*-
{
    'name': "Hr Payroll Extended Module",

    'summary': """
        This module contains custom modifications for Hr Payroll
        """,

    'description': """
       This module contains custom modifications for  Hr Payroll
    """,

    'author': "TechUltra Solution",
    'website': "http://www.techultrasolution.com/",
    'category': 'HR',
    'version': '15.0.0.0.0.1',
    'depends': [
        'hr',
        'hr_payroll',
        'mail',
        'ebs_lb_payroll',
        'taqat_groups_access_rights_extended',
    ],
    'data': [
        'views/hr_payslip.xml',
    ],


}
