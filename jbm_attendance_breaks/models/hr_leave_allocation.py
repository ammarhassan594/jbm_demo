from odoo import models, fields, api, _


class Allocation(models.Model):
    _inherit = 'hr.leave.allocation'

    due_violation = fields.Boolean(string='Due Violation')