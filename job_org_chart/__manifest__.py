# -*- coding: utf-8 -*-
{
    'name': "job_org_chart",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'hr_org_chart', 'web'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/hr_job_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'assets': {
            'web._assets_primary_variables': [
                'job_org_chart/static/src/scss/variables.scss',
            ],
            'web.assets_backend': [
                'job_org_chart/static/src/scss/job_org_chart.scss',
                'job_org_chart/static/src/js/job_org_chart.js',
            ],
            'web.assets_qweb': [
                'job_org_chart/static/src/xml/**/*',
            ],
        },
}
