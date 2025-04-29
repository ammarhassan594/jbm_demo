from odoo import models, fields, api, _


class InheritHrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    replacement_employee = fields.Boolean(string="Replacement Employee")