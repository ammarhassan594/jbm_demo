# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.addons.ake_attendance_sheet.tools.custom_dateutil import convert_to_timezone, time_to_float
from odoo.exceptions import ValidationError

from datetime import datetime, date, time
import pytz


class AkeAttendanceSheet(models.Model):
    _name = 'hr.attendance.sheet'
    _description = 'AKE Attendance Sheet'
    _order = 'date desc, id desc'

    employee_id = fields.Many2one("hr.employee", ondelete='cascade')
    date = fields.Date()
    check_in = fields.Float("Actual Check IN")
    check_out = fields.Float("Actual Check Out")
    early_check_out = fields.Float("Early Check Out")
    late_check_in = fields.Float("Late Check In")
    attendance_state = fields.Selection([
        ('attendance', 'Attendance'),
        ('late', 'Late In'),
        ('early', 'Early Out'),
        ('both', 'Late In / Early Out'),
    ])
    attendance_id = fields.Many2one('hr.attendance', ondelete='cascade')

    _sql_constraints = [
        ('unique_employee_attendance', 'unique(employee_id,attendance_id)',
         _("Employee attendance already exists"))
    ]

    def _set_attendance_state(self):
        for attend_sheet in self:
            early_check_out = attend_sheet.early_check_out or 0.0
            late_check_in = attend_sheet.late_check_in or 0.0

            if early_check_out > 0.0 and late_check_in > 0.0:
                attend_sheet.attendance_state = 'both'
            elif early_check_out > 0.0:
                attend_sheet.attendance_state = 'early'
            elif late_check_in > 0.0:
                attend_sheet.attendance_state = 'late'
            else:
                attend_sheet.attendance_state = 'attendance'

    def _update_check_out(self):
        if self.attendance_id and self.attendance_id.check_out:
            from_zone = 'UTC'
            to_zone = self._context.get('tz')
            attendance_checkout_central = convert_to_timezone(from_zone, to_zone,
                                                              str(self.attendance_id.check_out))
            self.check_out = time_to_float(attendance_checkout_central)

    def _update_check_in(self):
        if self.attendance_id and self.attendance_id.check_in:
            from_zone = 'UTC'
            to_zone = self._context.get('tz')
            attendance_checkin_central = convert_to_timezone(from_zone, to_zone,
                                                             str(self.attendance_id.check_in))
            self.check_in = time_to_float(attendance_checkin_central)

    def remove_late_check_in(self):
        self.ensure_one()
        self.late_check_in = 0.0
        self._update_check_in()
        self._set_attendance_state()

    def remove_early_check_out(self):
        self.ensure_one()
        self.early_check_out = 0.0
        self._update_check_out()
        self._set_attendance_state()

    def return_attendance_to_confirm(self):
        """Return the associated attendances to manager_confirm_state"""
        attendance_sheets = self.filtered(lambda x: x.attendance_id and x.attendance_state in ['late', 'early', 'both'])
        for attendance_sheet in attendance_sheets:
            if attendance_sheet.attendance_id.check_in:
                attendance_sheet.write({'attendance_state': 'attendance'})
                attendance_sheet.attendance_id.write({'attendance_status': 'department_manager_approve'})
                attendance_sheet.attendance_id.get_late_checkin_attendance()
            if attendance_sheet.attendance_id.check_out:
                attendance_sheet.write({'attendance_state': 'attendance'})
                attendance_sheet.attendance_id.write({'attendance_status_early': 'department_manager_approve'})
                attendance_sheet.attendance_id.get_early_check_out_attendance()
        return True
