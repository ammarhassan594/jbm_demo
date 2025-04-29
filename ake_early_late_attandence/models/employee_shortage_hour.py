    # -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class EmployeeShortageHour(models.Model):
    _name = 'employee.shortage.hour'
    _description = 'Employee Shortage Hour'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string="Employee")
    date_from = fields.Date(string="From date")
    date_to = fields.Date(string="To date")
    violation_hours = fields.Float(string="Employee Violation hour")
    attendance_ids = fields.Many2many('hr.attendance', string="Attendance")
    casual_leave_justification_types = fields.Many2many('justification.type', string="Casual leave justification type")
    casual_leave_allocation_id = fields.Many2one('hr.leave.allocation', string="Casual leave allocation")
    status = fields.Selection([('draft', 'Draft'), ('approved', 'Approved'), ('refused', 'Refused')], string="Status",
                              default="draft")
    is_manager = fields.Boolean(string="Is manager", compute="compute_is_manager")

    def compute_is_manager(self):
        for record in self:
            if record.employee_id.parent_id and record.employee_id.parent_id.user_id == self.env.user:
                record.is_manager = True
            else:
                record.is_manager = False

    def approve_employee_shortage_hour(self):
        current_leave_balance = self.casual_leave_allocation_id.number_of_hours_display - self.violation_hours
        if self.employee_id.resource_calendar_id and self.employee_id.resource_calendar_id.hours_per_day > 0:
            number_of_days = current_leave_balance / self.employee_id.resource_calendar_id.hours_per_day
        else:
            number_of_days = current_leave_balance / 8
        self.casual_leave_allocation_id.sudo().write(
            {'number_of_days': number_of_days})
        self.employee_id.sudo().write({'violation_hours': 0.0, 'justification_type_ids': False})
        self.status = 'approved'

    def refuse_employee_shortage_hour(self):
        if self.employee_id.resource_calendar_id and self.employee_id.resource_calendar_id.hours_per_day > 0:
            violation_in_days = self.violation_hours / self.employee_id.resource_calendar_id.hours_per_day
        else:
            violation_in_days = self.violation_hours / 8
        number_of_days = self.casual_leave_allocation_id.number_of_days + violation_in_days
        self.casual_leave_allocation_id.sudo().write({'number_of_days': number_of_days})
        self.status = 'refused'

    def action_set_to_draft(self):
        self.status = 'draft'
