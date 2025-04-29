from odoo import models, fields, api, _


class InheritHrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    employee_approver_days = fields.Float(string="Employee Approver's Due in (Days)")
    time_off_officer_days = fields.Float(string="Time Off Officer Due in (Days)")
