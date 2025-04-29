import datetime
from datetime import datetime, timedelta
from odoo import models, fields, tools, api, exceptions, _
import babel
import pytz


class AttendanceSheetLine(models.Model):
    _name = 'attendance.sheet.line'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('done', 'Approved')], default='draft', readonly=True, )
    date = fields.Date("Date")
    day = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], 'Day of Week', required=True, index=True, )
    att_sheet_id = fields.Many2one(comodel_name='attendance.sheet', string='Attendance Sheet', readonly=True,
                                   ondelete="cascade")
    worked_hours = fields.Float("Worked Hours", readonly=True)
    ac_sign_in = fields.Float("Actual sign in", readonly=True)
    ac_sign_out = fields.Float("Actual sign out", readonly=True)
    late_in = fields.Float("Late In", readonly=True)
    early_out = fields.Float("Early Out", readonly=True)
    total_over_break = fields.Float("Break", readonly=True)
    note = fields.Text("Note", readonly=True)
    status = fields.Selection(string="Day Status",
                              selection=[('ab', 'Absence'), ('weekend', 'Week End'), ('ph', 'Public Holiday'),
                                         ('leave', 'Leave'), ('illegal', 'Absence'),
                                         ('unpaid_leave', 'Unpaid Leave'),
                                         ('terminated', 'End Contract'),
                                         ],
                              required=False, readonly=True)
    # leave_ids = fields.Many2many(comodel_name='hr.leave', relation="leave_attendance_rel",
    #                                           column1="leave", culomn2="attendance", string='Leaves')
    sick_leave_type = fields.Char(string="Sick Leave Percentage", readonly=True, )
    display_attendance = fields.Boolean(default=False)
    status_char = fields.Char(string="Status")
    leave_type_id = fields.Many2one(comodel_name='hr.leave.type', string='Leave', readonly=True)


    def get_attendance_records(self):
        try:
            tree_view_id = self.env.ref("hr_attendance.view_attendance_tree").id
        except Exception as e:
            tree_view_id = False
        employee = self.att_sheet_id.employee_id
        user = self.env['res.users'].sudo().browse(self.env.user.id)
        timezone = pytz.timezone(user.tz or "UTC")
        # date_utc = self.date.replace(tzinfo=pytz.UTC).astimezone(timezone)
        day_before = self.date + timedelta(days=-1)
        date_from = datetime(day_before.year, day_before.month, day_before.day, 22, 0, 0)
        date_to = datetime(self.date.year, self.date.month, self.date.day, 22, 0, 0)
        attendances = self.env['hr.attendance'].search(
            [('employee_id', '=', employee.id), ]).filtered(lambda x: date_from <= x.check_in <= date_to)
        # print(date_from, date_to)
        # ids = []
        # for a in attendances:
        #     if date_from <= a.check_in <= date_to:
        #         ids.append(a.id)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Attendance',
            'view_type': 'form',
            'view_mode': 'tree,pivot,form',
            'res_model': 'hr.attendance',
            'views': [(tree_view_id, 'tree')],
            'target': 'current',
            'domain': [('id', 'in', attendances.ids)]
        }