from odoo import models, fields, api, _

class InheritHrEmployee(models.Model):
    _inherit = 'hr.employee'

    role_delegation_ids = fields.Many2many('roles.delegation', string="Roles Delegation")