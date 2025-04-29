# -*- coding: utf-8 -*-
{
    'name': "attendance_analysis_report",

    'summary': """
        This Module is to print a daily report""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_attendance', 'resource', 'report_xlsx', 'ake_attendance_sheet'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'report/report.xml',
        'wizard/attendance_analysis.xml',
    ],

}
