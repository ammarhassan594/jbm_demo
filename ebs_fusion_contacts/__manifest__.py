# -*- coding: utf-8 -*-


{
    'name': "EBS Fusion Contacts Module",

    'summary': """
        This module contains custom modifications for ebs fusion Contacts
        """,

    'description': """
       This module contains custom modifications for ebs fusion Contacts
    """,

    'author': "Mustafa kantawala",
    'website': "http://www.ever-bs.com/",
    'category': 'Contacts',
    'version': '15.0.0.2.2.1',
    'depends': [
        'base',
        'contacts',
        'documents',
        'purchase',
        'ebs_fusion_documents',
        'ebs_fusion_product',
        'base_geolocalize',
        'account_asset',
        'fleet',
        'sale',
        'ebs_fusion_legal',
        'hr_attendance',

    ],
    'data': [
        'security/ir.model.access.csv',
        'data/client_relation_update.xml',
        # 'views/ebs_fusion_share_holder.xml',
        'views/ebs_client_contact.xml',
        'views/ebs_fusion_contacts.xml',
        'views/ebs_fusion_client_review.xml',

        'views/ebs_fusion_national_address.xml',
        'views/documents_document_custom.xml',
        'views/ebs_document_type.xml',
        'views/ebs_fusion_res_partner_state.xml',
        'views/res_partner_bank_view.xml',
        'views/mail_template.xml',
        'wizard/ebs_document_active_confirm.xml',
    ],
    'post_init_hook': 'post_init',
}
