from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date


class HRLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    actual_days_calculated = fields.Boolean('Is calculated in actual days?')
    max_allowed_days = fields.Integer('Max Allowed Days')

    @api.onchange('actual_days_calculated')
    def _onchange_max_allowed_days(self):
        if not self.actual_days_calculated:
            self.max_allowed_days = 0
