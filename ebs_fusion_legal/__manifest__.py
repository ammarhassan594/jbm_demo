# -*- coding: utf-8 -*-
{
    'name': "EBS Fusion Legal",

    'summary': """
        This module contains ebs fusion legal cases
        """,

    'description': """
       This module contains ebs fusion legal cases
    """,

    'author': "Mustafa Kantawala",
    'website': "http://www.ever-bs.com/",
    'category': '',
    'version': '15.0.0.0.1',
    'depends': ['hr', 'ebs_fusion_documents'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/documents_data.xml',
        'views/ebs_legal_case_views.xml',
        'views/ebs_legal_law_firm_views.xml',
        'views/documents_document_custom.xml',
        'views/ebs_legal_activity_type_views.xml',
        'views/ebs_legal_case_type_views.xml',
        'views/ebs_legal_litigation_degree_view.xml',
        'views/ebs_legal_case_class_view.xml',
        'views/ebs_legal_court_views.xml',
    ],

}
