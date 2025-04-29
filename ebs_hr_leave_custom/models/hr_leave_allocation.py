from odoo import models, fields, api, _


class Allocation(models.Model):
    _inherit = 'hr.leave.allocation'
    _description = 'Leave Allocation'

    _sql_constraints = [
        ('duration_check', "CHECK ( number_of_days != None )", "The number of days must not equal to None."),
    ]

    employee_number = fields.Char(related="employee_id.registration_number", string="Employee Number")
    allocated_yearly = fields.Boolean()

    @api.onchange('holiday_status_id')
    def _get_default_number_of_days(self):
        if self.holiday_status_id and self.holiday_status_id.default_days:
            self.number_of_days_display = self.holiday_status_id.default_days
        else:
            self.number_of_days_display = 1
