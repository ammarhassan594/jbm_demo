# -*- coding: utf-8 -*-
{
    'name': "EBS JBM Scheduled Entries",
    'summary': """
        Ebs JBM Generate entries periodically """,
    'description': """
        Ebs JBM Generate entries periodically
    """,
    'author': "TechUltra Solution",
    'website': "http://www.techultrasolution.com/",
    'category': 'Uncategorized',
    'version': '15.0.0.0.1',
    'depends': ['account', 'analytic'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'views/scheduled_entries_configuration_view.xml',
    ],
}
