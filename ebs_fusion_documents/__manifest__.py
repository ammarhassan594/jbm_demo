# -*- coding: utf-8 -*-
{
    'name': "EBS Fusion Documents",

    'summary': """
        This module contains custom modifications for ebs fusion documents
        """,

    'description': """
       This module contains custom modifications for ebs fusion documents
    """,

    'author': "Mustafa Kantawala",
    'website': "http://www.ever-bs.com/",
    'category': 'CRM',
    'version': '15.0.0.2.1',
    'depends': [
        'documents', 'base', 'account'
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/update_document.xml',
        'data/document_mail_template.xml',

        'views/document_folder_custom.xml',
        'views/documents_document_custom.xml',
        'views/ebs_document_category_view.xml',
        'views/ebs_document_type.xml',
        'views/scheduler.xml',
        'views/document_portal_templates.xml',
        'views/workspce_rename_field_models.xml',
        'wizard/send_mail_template_document_wizard_view.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'ebs_fusion_documents/static/src/css/document.css',
            'ebs_fusion_documents/static/src/js/portal.js',
        ],
        'web.assets_backend': [
            'ebs_fusion_documents/static/src/js/document_custom.js',
            'ebs_fusion_documents/static/src/css/document.css',
        ]
    },

}
