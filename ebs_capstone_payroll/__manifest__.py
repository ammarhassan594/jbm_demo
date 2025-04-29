# -*- coding: utf-8 -*-
{
    'name': "ebs_capstone_payroll",

    'summary': """
        Capstone Payroll Modification""",

    'description': """
    Capstone Payroll Modification
    """,

    'author': "jaafar khansa",
    'website': "http://www.ever-bs.com/",
    'version': '0.1',

    # any module necessary for this one to work correctly
    'category': 'Uncategorized',
    'depends': ['hr_payroll','hr','account'],

    # always loaded
    'data': [
        #'security/ir.model.access.csv',
        'views/views.xml',
    ]
}
