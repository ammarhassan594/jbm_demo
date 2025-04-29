# -*- coding: utf-8 -*-
{
    'name': "EBS JBM HR Holiday Custom ",
    'summary': """
        Ebs JBM HR Holiday Custom """,
    'description': """
        Ebs JBM HR Holiday Custom 
    """,
    'author': "TechUltra Solution",
    'website': "http://www.techultrasolution.com/",
    'category': 'Uncategorized',
    'version': '15.0.0.0.1',
    'depends': ['ebs_lb_payroll', 'ebs_fusion_services', 'ebs_fusion_hr_employee', 'jbm_employee_custom',
                'jbm_payscale_configuration', 'jbm_portal_self_service'],
    'data': [
        'report/jbm_custom_leave_report.xml',
        'report/leave_work_resumption_report.xml',
        'report/jbm_leave_request_report.xml',
        'report/leave_request_resuming_work_report.xml',
        'report/casual_leave.xml',
        'views/hr_leave.xml',
        'report/leave_request.xml',
        'report/leave_return_confirmation_report.xml',
        'views/res_config_settings.xml',
    ],
}
