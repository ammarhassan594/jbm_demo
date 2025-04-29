# -*- coding: utf-8 -*-
{
    'name': "JBM Group Access right Extended",
    'summary': """
      JBM Group Access right Extended
        """,
    'description': """
     JBM Group Access right Extended
    """,
    'author': "TechUltra Solution",
    'website': "http://www.techultrasolution.com/",
    'category': 'Configuration',
    'version': '15.0.0.0.0.1',
    'depends': ['base_user_role', 'sale_stock', 'hr_approvals', 'sales_team', 'sale_stock', 'hr_attendance',
                'im_livechat', 'purchase_requisition', 'account',
                'documents', 'fleet', 'hr_appraisal', 'planning', 'hr_holidays', 'ebs_fusion_hr_employee', 'project',
                'base_dynamic_approval', 'hr_payroll', 'hide_menu_user', 'event', 'ebs_jbm_budget_custom',
                'ebs_fusion_account'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/res_user_role_views.xml',
        'views/hr_leave_view.xml',
        'views/views.xml',
        'views/hr_payslip_run_views.xml',
        'views/purchase.xml'
    ],
}
