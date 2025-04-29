# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from dateutil import tz
from odoo.addons.ake_attendance_sheet.tools.custom_dateutil import convert_to_timezone, time_to_float
import pytz


class ApproveAttendanceWizard(models.TransientModel):
    _name = 'approve.late_early_attendance.wizard'

    approve_options = fields.Selection([
        ('add_late_check_in', 'Add Late Check In'),
        ('add_early_check_out', 'Add Early Check Out'),
        ('add_both', 'Add Both'),
    ])

    def approve_late_early_check(self):
        if self._context.get('active_id') and self._context.get('active_model') == 'hr.attendance':
            attendance = self.env['hr.attendance'].browse(self._context.get('active_id'))
            if attendance.employee_id.parent_id.user_id != self.env.user:
                raise ValidationError(_('You not have permission for approved'))

            all_day_attendance = self.env['hr.attendance']
            attendance_day_start = attendance.check_in.replace(hour=0, minute=0, second=0).astimezone(
                pytz.UTC).replace(tzinfo=None).strftime('%Y-%m-%d %H:%M:%S')
            attendance_day_end = attendance.check_in.replace(hour=23, minute=59, second=59).astimezone(
                pytz.UTC).replace(tzinfo=None).strftime('%Y-%m-%d %H:%M:%S')
            query = """SELECT id FROM hr_attendance WHERE employee_id = %s AND check_in BETWEEN %s AND %s """
            self._cr.execute(query, (attendance.employee_id.id, attendance_day_start, attendance_day_end))
            existing_record_ids = self._cr.fetchall()
            if existing_record_ids:
                existing_record_ids = [rec_id[0] for rec_id in list(existing_record_ids)]
                all_day_attendance = self.env['hr.attendance'].browse(existing_record_ids).sorted('check_in')

            from_zone = tz.gettz('UTC')
            to_zone = tz.gettz('Asia/Qatar' or self._context.get('tz'))
            attendance_checkin_utc = attendance.check_in and \
                                     datetime.strptime(str(attendance.check_in), '%Y-%m-%d %H:%M:%S').replace(
                                         tzinfo=from_zone)
            attendance_checkout_utc = attendance.check_out and \
                                      datetime.strptime(str(attendance.check_out), '%Y-%m-%d %H:%M:%S').replace(
                                          tzinfo=from_zone)
            attendance_checkin_central = attendance_checkin_utc and \
                                         attendance_checkin_utc.astimezone(to_zone)
            attendance_checkout_central = attendance_checkout_utc and \
                                          attendance_checkout_utc.astimezone(to_zone)
            # activity = self.env.ref('ake_early_late_attandence.mail_activity_approve_attendance').id
            # attendance.sudo()._get_user_approval_activities(user=self.env.user, activity_type_id=activity).action_feedback()
            attendance_date = attendance_checkin_utc.date().strftime("%Y-%m-%d")
            if all_day_attendance:
                qatar_tz = pytz.timezone('Asia/Qatar')
                check_in = all_day_attendance[0].check_in.astimezone(qatar_tz).replace(tzinfo=None)
                check_out = all_day_attendance[-1].check_out.astimezone(qatar_tz).replace(tzinfo=None)
            else:
                check_in = attendance_checkin_central
                check_out = attendance_checkout_central
            vals = {
                "check_in": time_to_float(check_in),
                "check_out": time_to_float(check_out),
                "attendance_id": attendance.id
            }
            if self.approve_options == 'add_late_check_in' and \
                    attendance.is_late_check_in and \
                    attendance.late_check_in_hour > 0.0:
                if attendance.attendance_sheet_id:
                    attendance.attendance_sheet_id.remove_late_check_in()
                else:
                    # create an attendance line as history
                    vals.update({
                        "late_check_in": 0.0,
                    })
                    attendance.attendance_sheet_id = attendance.employee_id.updated_or_create_attendance_sheet(
                        attendance_date=attendance_date,
                        **vals)
                attendance._disable_late_check_in()
                attendance.attendance_status = 'approved'
            elif self.approve_options == 'add_early_check_out' and \
                    attendance.is_early_check_out and \
                    attendance.early_check_out_hour > 0.0:
                if attendance.attendance_sheet_id:
                    attendance.attendance_sheet_id.remove_early_check_out()
                else:
                    # create an attendance line as history
                    vals.update({
                        "early_check_out": 0.0,
                    })
                    attendance.attendance_sheet_id = attendance.employee_id.updated_or_create_attendance_sheet(
                        attendance_date=attendance_date,
                        **vals)
                attendance._disable_early_check_out()
                attendance.attendance_status_early = 'approved'
            elif self.approve_options == 'add_both' and attendance.is_late_check_in and \
                    attendance.late_check_in_hour > 0.0 and attendance.is_early_check_out and \
                    attendance.early_check_out_hour > 0.0:
                if attendance.attendance_sheet_id:
                    attendance.attendance_sheet_id.remove_late_check_in()
                    attendance.attendance_sheet_id.remove_early_check_out()
                else:
                    # create an attendance line as history
                    vals.update({
                        "early_check_out": 0.0,
                        "late_check_in": 0.0,
                    })
                    attendance.attendance_sheet_id = attendance.employee_id.updated_or_create_attendance_sheet(
                        attendance_date=attendance_date,
                        **vals)
                attendance._disable_late_check_in()
                attendance._disable_early_check_out()
                attendance.attendance_status_early = 'approved'
                attendance.attendance_status = 'approved'
            else:
                raise UserError(_('Please select a valid option based on late check only or'
                                  ' early check out or Both'))
            # attendance.attendance_status = 'approved'
        return True
