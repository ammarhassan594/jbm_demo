from odoo import api, fields, models, _


class OvertimeCustom(models.Model):
    _inherit = 'hr.overtime'
    _description = "HR Overtime"

    attendance_sheet_ids = fields.Many2one('attendance.sheet', string='Attendance', ondelete="cascade")

