# -*- coding: utf-8 -*-
{
    'name': "EBS Fusion CRM Module",

    'summary': """
        This module contains custom modifications for ebs fusion crm
        """,

    'description': """
       This module contains custom modifications for ebs fusion crm
    """,

    'author': "Mustafa kantawala",
    'website': "http://www.ever-bs.com/",
    'category': 'CRM',
    'version': '15.0.0.0.0.1',
    'depends': [
        'contacts',
        'crm',
        'account',
        'hr',
        'documents',
        'ebs_fusion_contacts',
        'ebs_fusion_documents',
        'base',
        'calendar',
        'sale_crm',


    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/lead_mail_template.xml',
        'report/proposal_report_template.xml',
        'views/res_config_settings_view.xml',
        'views/ebs_fusion_tender.xml',
        'views/crm_lead_custom.xml',
        'views/res_partner_custom.xml',
        'views/res_partner_industry.xml',
        'views/crm_stage_custom.xml',
        'views/crm_sales_dashboard.xml',
        'views/crm_res_users_custom.xml',
        'views/ebs_calendar_meeting_room.xml',

    ]
}
