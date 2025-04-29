from odoo import api, fields, models, _

class ebsServiceUserGroups(models.Model):
    _name = 'ebs.services.user.group'
    _description = 'EBS Service User Group'
    _rec_name = 'name'

    name = fields.Char('Name')
    manager_id = fields.Many2one('hr.employee','Manager',domain=[('employee_type','=','fusion_employee')])
    manager_user_id = fields.Many2one(comodel_name='res.users', string='Manager', required=1,
                                      domain="[('share','=',False)]")
    user_ids = fields.One2many('ebs.services.user.group.lines','user_group_id','User Group Lines')


class ebsServiceUserGroupsLines(models.Model):
    _name = 'ebs.services.user.group.lines'
    _description = 'EBS Service User Group Lines'

    user_group_id = fields.Many2one('ebs.services.user.group','User Group')
    employee_id = fields.Many2one('hr.employee','Employee',domain=[('employee_type','=','fusion_employee')])
    employee_user_id = fields.Many2one(comodel_name='res.users', string='Employee', required=1,
                                       domain="[('share','=',False)]")
