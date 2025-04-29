from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class HrDepartment(models.Model):
    _inherit = 'hr.department'

    policy_ids = fields.One2many('hr.policy.procedure','department_id','Policies')
    type_of_department = fields.Selection(
        [('hr', 'HR'), ('marketing', 'Marketing'), ('sales', 'Sales'), ('social', 'Social Media'),
         ('legal', 'Legal'), ('account', 'Account'), ('it', 'Information Technology'), ('procurement', 'Procurement')],
        string='Reporting Type')


class PolicyProcedure(models.Model):
    _name = 'hr.policy.procedure'
    _description = 'HR Policy Procedure'

    name = fields.Char('Name', required=1)
    effected_date = fields.Date('Effected Date')
    attachment_ids = fields.Many2many('ir.attachment','Attachments')
    department_id = fields.Many2one('hr.department')