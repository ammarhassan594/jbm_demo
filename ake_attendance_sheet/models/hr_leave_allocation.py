from odoo import models, fields, api


class InheritHrLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    created_from_violation_hours = fields.Boolean()