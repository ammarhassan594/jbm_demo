from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AttendanceApiLog(models.Model):
    _name = 'attendance.api.log'
    _description = "Attendance Api log"
    _rec_name = 'employee_id'

    employee_id = fields.Char(string="Employee Id")
    punch_type = fields.Char(string="Punch type")
    date = fields.Datetime(string="Date")
    punch_id = fields.Char(string="Punch id")
    attendance_id = fields.Many2one('hr.attendance', string="Attendance")
    error = fields.Text(string="Error")
    employee_record_id = fields.Many2one('hr.employee', string="Employee", related="attendance_id.employee_id")
