# -*- coding: utf-8 -*-
{
    'name': "Ebs Fusion Theme",

    'summary': """
        Ebs Fusion Website Customisations""",

    'description': """
        Ebs Fusion Website Customisations
    """,

    'author': "ebs",
    'website': "http://www.ever-bs.com/",
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['website', 'website_crm', 'portal', 'hr_holidays', 'social', 'account', 'ebs_fusion_contacts'],

    # always loaded
    'data': [
        'views/landing_page_snippets.xml',
        'views/templates.xml',
        'views/dashboard_template.xml',
        'views/registration_templates.xml',
        'views/website_login.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.1.6/Chart.js',
            'ebs_fusion_theme/static/src/js/jquery.validate.min.js',
            'ebs_fusion_theme/static/src/js/contact_form.js',
            'ebs_fusion_theme/static/src/js/dashboard.js',
            'ebs_fusion_theme/static/src/js/jquery.steps.js',
            'ebs_fusion_theme/static/src/js/invoice_chart.js',
            'ebs_fusion_theme/static/src/js/payments_chart.js',
            'ebs_fusion_theme/static/src/js/main.js',
            'ebs_fusion_theme/static/src/css/homepage.css',
            'ebs_fusion_theme/static/src/css/dashboard.css',
            'ebs_fusion_theme/static/src/css/invoice.css',
            'ebs_fusion_theme/static/src/css/employee.css',
            'ebs_fusion_theme/static/src/css/website_login.css',
            'ebs_fusion_theme/static/src/css/opensans-font.css',
            'ebs_fusion_theme/static/src/css/style.css',

        ]
    },
}
