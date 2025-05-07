{
    'name': 'Base Advanced Approval Role',
    'summary': 'Allow to set Generic Role for level',
    'author': 'Ever Business Solutions',
    'maintainer': 'Abdalla Mohamed',
    'website': 'https://www.everbsgroup.com/',
    'version': '15.0.1.0.0',
    'category': 'Hidden/Tools',
    'license': 'OPL-1',
    'depends': [
        'base_dynamic_approval', 'project'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/dynamic_approval.xml',
        'views/dynamic_approval_role.xml',
        'views/role_distribution.xml',
        'views/project_project.xml',
        'template/role_distribution_template.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
