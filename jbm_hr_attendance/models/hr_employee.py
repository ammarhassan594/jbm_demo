from odoo import models, fields, api, _


class EmployeeCustom(models.Model):
    _inherit = 'hr.employee'

    out_of_attendance = fields.Boolean(string="Out Of Attendance")
