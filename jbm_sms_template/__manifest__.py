{
    'name': "JBM SMS TEMPLATE",
    'summary': """""",
    'description': """CONSOLIDATED STATE""",
    'author': "My Company",
    'website': "",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base' ,'hr_payroll', 'hr_contract_reports', 'hr', 'hr_holidays', 'hr_employee_custom', 'account',],
    'data': [
        'wizard/schedule_wizard_view.xml',
        'wizard/test_wizard_view.xml',
        'views/jbm_sms_template_view.xml',
        'views/menus.xml',
    ],
    'demo': [],
}
