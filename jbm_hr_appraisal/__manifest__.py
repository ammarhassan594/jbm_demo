# -*- coding: utf-8 -*-
{
    'name': "JBM HR Appraisal",
    'summary': """
        JBM HR Appraisal add features to appraisal 
        """,
    'description': """
JBM HR Appraisal add features to appraisal
     """,
    'author': 'Intalio EverTeam',
    'maintainer': 'Muhammed-Ashraf',
    'website': 'https://www.intalio.com/',
    'category': 'Human Resources/Appraisals',
    'version': '15.0.0.0',
    'depends': ['hr', 'hr_appraisal', 'approvals', 'jbm_group_access_right_extended',
                'jbm_group_access_right_extended', 'employee_training_courses'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/skills_objective_types.xml',
        'views/skills_objectives.xml',
        'views/appraisal_batch_view.xml',
        'views/hr_job.xml',
        'views/hr_employee.xml',
        'views/hr_appraisal_view.xml',
        'views/res_config_settings_view.xml',
        'report/report_template.xml',
        'report/hr_appraisal_report.xml',
        # 'report/delivery_note.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
