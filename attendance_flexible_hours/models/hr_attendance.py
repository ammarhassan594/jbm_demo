import logging
from odoo import models, fields, api, _
from datetime import datetime, time
from dateutil import tz
from odoo.addons.ake_attendance_sheet.tools.custom_dateutil import convert_to_timezone, time_to_float

_logger = logging.getLogger(__name__)

class InheritHrAttendance(models.Model):
    _inherit = 'hr.attendance'


    def get_late_checkin_attendance(self):
        """Check if attendance is late form expected based on employee calendar"""
        self.ensure_one()
        employee_attendance = self
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz('Asia/Qatar' or self._context.get('tz'))
        attendance_checkin_utc = datetime.strptime(str(employee_attendance.check_in), '%Y-%m-%d %H:%M:%S')
        attendance_checkin_utc = attendance_checkin_utc.replace(tzinfo=from_zone)
        attendance_checkin_central = attendance_checkin_utc.astimezone(to_zone)

        attend_time_minutes = attendance_checkin_central.time().hour + (
                attendance_checkin_central.time().minute / 60)
        # get morning
        calendar_attend = employee_attendance.employee_id.resource_calendar_id.attendance_ids.filtered(
            lambda x: dict(x._fields['dayofweek'].selection).get(
                x.dayofweek) == attendance_checkin_central.strftime('%A')
                      and x.day_period == 'morning'
        )

        if len(calendar_attend) > 1:
            calendar_attend = calendar_attend[0]
        if calendar_attend and attend_time_minutes > calendar_attend.hour_from:
            if employee_attendance.employee_id.resource_calendar_id.allow_flexible_hours:
                if employee_attendance.employee_id.resource_calendar_id.max_check_in_hour == 0.00:
                    employee_attendance._disable_late_check_in()
                    if employee_attendance.attendance_sheet_id:
                        employee_attendance.attendance_sheet_id.remove_late_check_in()
                elif employee_attendance.employee_id.resource_calendar_id.max_check_in_hour > 0.00:
                    max_hour = calendar_attend.hour_from + employee_attendance.employee_id.resource_calendar_id.max_check_in_hour
                    if max_hour:
                        if attend_time_minutes <= max_hour:
                            employee_attendance._disable_late_check_in()
                        else:
                            late_hours = attend_time_minutes - max_hour
                            leaves = self.env['hr.leave'].sudo().search(
                                [('employee_id', '=', employee_attendance[0].employee_id.id),
                                 ('request_date_from', '<=', attendance_checkin_utc.date()),
                                 ('request_date_to', '>=', attendance_checkin_utc.date()),
                                 ('state', '=', 'validate')
                                 ])
                            if leaves:
                                for leave in leaves:
                                    hour_from = time_to_float(leave.date_from.astimezone(to_zone).time())
                                    if hour_from == calendar_attend.hour_from or hour_from == max_hour:
                                        if late_hours > leave.number_of_hours_display:
                                            employee_attendance.leave_id = leave.id
                                            remaining_diff_after_leave = late_hours - leave.number_of_hours_display
                                            employee_attendance._enable_late_check_in(remaining_diff_after_leave)
                                        else:
                                            employee_attendance._disable_late_check_in()
                                    else:
                                        employee_attendance._enable_late_check_in(late_hours)
                            else:
                                employee_attendance._enable_late_check_in(late_hours)
            else:
                diff = attend_time_minutes - calendar_attend.hour_from
                justification = self.env['justification.type'].search([
                    ('daily_grace_period', '=', True), ('to_time', '!=', False)
                ])
                is_allowed_late = justification.is_checked_in_justification(attend_time_minutes,
                                                                            calendar_attend.hour_from)
                if not is_allowed_late:
                    diff = diff - justification.to_time if diff > justification.to_time else diff
                    employee_attendance.justification_type_id = False
                    today_date_time = attendance_checkin_central.replace(hour=0, minute=0, second=0)
                    leaves = self.env['hr.leave'].sudo().search(
                        [('employee_id', '=', employee_attendance[0].employee_id.id),
                         ('request_date_from', '<=', attendance_checkin_utc.date()),
                         ('request_date_to', '>=', attendance_checkin_utc.date()),
                         ('state', '=', 'validate')
                         ])
                    if leaves:
                        for leave in leaves:
                            hour_from = time_to_float(leave.date_from.astimezone(to_zone).time())
                            if hour_from == calendar_attend.hour_from:
                                if diff > leave.number_of_hours_display:
                                    employee_attendance.leave_id = leave.id
                                    remaining_diff_after_leave = diff - leave.number_of_hours_display
                                    employee_attendance._enable_late_check_in(remaining_diff_after_leave)
                                else:
                                    employee_attendance._disable_late_check_in()
                            else:
                                employee_attendance._enable_late_check_in(diff)
                    else:
                        employee_attendance._enable_late_check_in(diff)
                else:
                    employee_attendance.justification_type_id = justification.id
                    employee_attendance._disable_late_check_in()
        else:
            employee_attendance._disable_late_check_in()
            # check if existing attendance sheet record
            if employee_attendance.attendance_sheet_id:
                employee_attendance.attendance_sheet_id.remove_late_check_in()



    def get_early_check_out_attendance(self):
        """Check if attendance is earlier than expected based on employee calendar"""
        self.ensure_one()
        employee_attendance = self
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz('Asia/Qatar' or self._context.get('tz'))
        attendance_checkout_utc = datetime.strptime(str(employee_attendance.check_out), '%Y-%m-%d %H:%M:%S')
        attendance_checkout_utc = attendance_checkout_utc.replace(tzinfo=from_zone)
        attendance_checkout_central = attendance_checkout_utc.astimezone(to_zone)

        allow_flexible_hours = employee_attendance.employee_id.resource_calendar_id.allow_flexible_hours
        # get afternoon calendar
        evening_data = employee_attendance.employee_id.resource_calendar_id.attendance_ids.filtered(
            lambda x: dict(x._fields['dayofweek'].selection).get(x.dayofweek) == attendance_checkout_central.strftime(
                '%A') and x.day_period == 'afternoon')
        if len(evening_data) > 1:
            evening_data = evening_data[0]
        time_in_minutes = employee_attendance.check_out and \
                          attendance_checkout_central.time().hour + \
                          (attendance_checkout_central.time().minute / 60)

        if allow_flexible_hours and employee_attendance.employee_id.resource_calendar_id.max_check_in_hour > 0.00:
            max_hour_to = evening_data.hour_to + employee_attendance.employee_id.resource_calendar_id.max_check_in_hour

            attendance_checkin_utc = datetime.strptime(str(employee_attendance.check_in), '%Y-%m-%d %H:%M:%S')
            attendance_checkin_utc = attendance_checkin_utc.replace(tzinfo=from_zone)
            attendance_checkin_central = attendance_checkin_utc.astimezone(to_zone)

            attend_in_time_minutes = attendance_checkin_central.time().hour + (
                    attendance_checkin_central.time().minute / 60)

            calendar_attend = employee_attendance.employee_id.resource_calendar_id.attendance_ids.filtered(
                lambda x: dict(x._fields['dayofweek'].selection).get(
                    x.dayofweek) == attendance_checkin_central.strftime('%A')
                          and x.day_period == 'morning'
            )

            if len(calendar_attend) > 1:
                calendar_attend = calendar_attend[0]

            attend_check_in = calendar_attend.hour_from
            max_attend_check_in = calendar_attend.hour_from + employee_attendance.employee_id.resource_calendar_id.max_check_in_hour


            if attend_in_time_minutes == attend_check_in:
                if time_in_minutes < evening_data.hour_to:
                    diff = evening_data.hour_to - time_in_minutes

                    leaves = self.env['hr.leave'].sudo().search(
                        [('employee_id', '=', employee_attendance[-1].employee_id.id),
                         ('request_date_from', '<=', attendance_checkout_utc.date()),
                         ('request_date_to', '>=', attendance_checkout_utc.date()),
                         ('state', '=', 'validate')])
                    if leaves:
                        for leave in leaves:
                            hour_to = time_to_float(leave.date_to.astimezone(to_zone).time())
                            if hour_to >= evening_data.hour_to:
                                employee_attendance.leave_id = leave.id
                                if diff > leave.number_of_hours_display:
                                    employee_attendance.leave_id = leave.id
                                    remaining_diff_after_leave = diff - leave.number_of_hours_display
                                    employee_attendance._enable_early_check_out(remaining_diff_after_leave)
                                else:
                                    employee_attendance._disable_early_check_out()
                            else:
                                employee_attendance._enable_early_check_out(diff)

                    else:
                        employee_attendance._enable_early_check_out(diff)
                else:
                    employee_attendance._disable_early_check_out()
                    # check if existing attendance sheet record
                    if employee_attendance.attendance_sheet_id:
                        employee_attendance.attendance_sheet_id.remove_early_check_out()
            elif (attend_in_time_minutes > attend_check_in and attend_check_in <= max_attend_check_in) or attend_in_time_minutes > max_attend_check_in:
                if time_in_minutes < max_hour_to:
                    diff = max_hour_to - time_in_minutes

                    leaves = self.env['hr.leave'].sudo().search(
                        [('employee_id', '=', employee_attendance[-1].employee_id.id),
                         ('request_date_from', '<=', attendance_checkout_utc.date()),
                         ('request_date_to', '>=', attendance_checkout_utc.date()),
                         ('state', '=', 'validate')])
                    if leaves:
                        for leave in leaves:
                            hour_to = time_to_float(leave.date_to.astimezone(to_zone).time())
                            if hour_to >= max_hour_to:
                                employee_attendance.leave_id = leave.id
                                if diff > leave.number_of_hours_display:
                                    employee_attendance.leave_id = leave.id
                                    remaining_diff_after_leave = diff - leave.number_of_hours_display
                                    employee_attendance._enable_early_check_out(remaining_diff_after_leave)
                                else:
                                    employee_attendance._disable_early_check_out()
                            else:
                                employee_attendance._enable_early_check_out(diff)

                    else:
                        employee_attendance._enable_early_check_out(diff)

                else:
                    employee_attendance._disable_early_check_out()
                    # check if existing attendance sheet record
                    if employee_attendance.attendance_sheet_id:
                        employee_attendance.attendance_sheet_id.remove_early_check_out()

        else:
            if time_in_minutes < evening_data.hour_to:
                diff = evening_data.hour_to - time_in_minutes
                today_date_time = attendance_checkout_central.replace(hour=int(evening_data.hour_to), minute=59,
                                                                      second=59)
                leaves = self.env['hr.leave'].sudo().search(
                    [('employee_id', '=', employee_attendance[-1].employee_id.id),
                     ('request_date_from', '<=', attendance_checkout_utc.date()),
                     ('request_date_to', '>=', attendance_checkout_utc.date()),
                     ('state', '=', 'validate')])
                if leaves:
                    for leave in leaves:
                        hour_to = time_to_float(leave.date_to.astimezone(to_zone).time())
                        if hour_to >= evening_data.hour_to:
                            employee_attendance.leave_id = leave.id
                            if diff > leave.number_of_hours_display:
                                employee_attendance.leave_id = leave.id
                                remaining_diff_after_leave = diff - leave.number_of_hours_display
                                employee_attendance._enable_early_check_out(remaining_diff_after_leave)
                            else:
                                employee_attendance._disable_early_check_out()
                        else:
                            employee_attendance._enable_early_check_out(diff)

                else:
                    employee_attendance._enable_early_check_out(diff)
            else:
                employee_attendance._disable_early_check_out()
                # check if existing attendance sheet record
                if employee_attendance.attendance_sheet_id:
                    employee_attendance.attendance_sheet_id.remove_early_check_out()
