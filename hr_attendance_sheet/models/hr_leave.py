from odoo import api, fields, models, _


class Leave(models.Model):
    _inherit = 'hr.leave'

    attendance_sheet_id = fields.Many2one('attendance.sheet', string='Attendance', ondelete="cascade")
