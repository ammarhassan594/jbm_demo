from odoo import models, fields, api, _
from odoo.exceptions import UserError



class HrAttendanceCustom(models.Model):
    _inherit = 'hr.attendance'

    check_in_punch_id = fields.Char(string="Check In Punch ID")
    check_out_punch_id = fields.Char(string="Check Out Punch ID")
