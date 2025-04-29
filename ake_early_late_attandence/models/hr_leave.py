from odoo import models, fields, api

class InheritHrLeave(models.Model):

    _inherit = 'hr.leave'

    payslip_id = fields.Many2one('hr.payslip')
    created_from_violation_hours = fields.Boolean()