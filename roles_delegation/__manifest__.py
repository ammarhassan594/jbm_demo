{
    'name': "Roles Delegation",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'hr', 'hr_holidays', 'base_user_role'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/roles_delegate.xml',
        'data/cron_job.xml',
        'data/mail_activity_type.xml',
        'views/server_action.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
