# -*- coding: utf-8 -*-
{
    'name': "EBS Fusion Services",

    'summary': """
        This module contains ebs fusion services, proposals, pricelists
        """,

    'description': """
       This module contains ebs fusion services, proposals, pricelists
    """,

    'author': "Mustafa kantawala",
    'website': "http://www.ever-bs.com/",
    'category': 'CRM',
    'version': '150.0.0.1.1',
    'depends': [
        'account',
        'ebs_fusion_crm',
        'ebs_fusion_theme',
        'ebs_fusion_documents',
        'website_bootstrap_select',
        'helpdesk',
        'purchase',
        'ebs_fusion_contacts',
        'hr_employee_custom',
        'web',
        'hr',
        'mail',

    ],
    'data': [
        'data/contract_mail_template.xml',
        'wizard/transfer_document_views.xml',
        'wizard/advance_payment_invoice_views.xml',
        'wizard/advance_payment_contract_invoice_views.xml',
        'wizard/return_to_previous_views.xml',
        'wizard/document_validation_view.xml',
        'wizard/update_lq_lines_wizard_view.xml',
        'wizard/warning_wizard_view.xml',
        'wizard/mail_compose_message_view.xml',
        'wizard/assign_workflows_wizard_view.xml',
        'wizard/workflow_change_status_wizard_view.xml',
        'security/security.xml',
        'security/ir.model.access.csv',

        'views/ebs_crm_services.xml',
        'views/hr_employee_custom_views.xml',
        'views/ebs_crm_proposal.xml',
        'views/ebs_crm_service_stage.xml',
        'views/ebs_crm_service_activity.xml',
        'views/ebs_crm_service_authority.xml',
        'views/ebs_crm_pricelist.xml',
        'views/ebs_crm_pricelist_category.xml',
        'views/crm_lead_custom.xml',
        'views/ebs_crm_service_templates.xml',
        'views/documents_document_custom.xml',
        'views/ebs_crm_service_process.xml',
        'views/ebs_contract_proposal_fees_view.xml',
        'views/ebs_crm_pricelist_line_views.xml',
        'views/proposal_process_dashboard.xml',
        'views/res_partner_custom.xml',
        'views/workflow_dashboard_views.xml',
        'views/service_order_portal_templates_custom.xml',
        'views/ebs_crm_contract_fees_views.xml',
        'views/ebs_crm_contract_details_views.xml',

        'views/ebs_crm_service_groups_line.xml',
        'views/ebs_fusion_fees.xml',
        'views/ebs_batch_service_order_views.xml',
        'data/service_data.xml',
        'data/contract_details_data.xml',
        'data/client_contact_relation_tags.xml',
        'views/ebs_labor_quota.xml',
        'views/ebs_service_user_groups_view.xml',
        'views/menu.xml',
        'report/service_order_invoice.xml',
        'views/ebs_service_rules.xml',
        # 'views/account_move_view.xml',
        'views/ebs_service_option_view.xml',
        'views/ebs_accounts_credit_cards_view.xml',
        'views/ebs_crm_service_fine_view.xml',

    ],
    'assets': {
        'web.assets_frontend': [
            'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.1.6/Chart.js',
            'ebs_fusion_services/static/src/css/request_services.css',
            'ebs_fusion_services/static/src/js/custom.js',
            'ebs_fusion_services/static/src/js/service_order_chart.js'

        ]
    },
}
