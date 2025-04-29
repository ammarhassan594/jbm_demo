# -*- coding: utf-8 -*-
from datetime import datetime, date, time

from odoo import models, fields, api, _

import pytz

from odoo.addons.resource.models.resource import float_to_time


class AttendanceSheet(models.Model):
    _inherit = 'hr.attendance.sheet'

    break_time = fields.Float("Break Time")
    attendance_state = fields.Selection(
        selection_add=[
            ('break', 'Break'),
            ('check_in_break', 'Late In / Break'),
            ('break_check_out', 'Break / Early Out'),
            ('in_out_break', 'Late In / Break / Early Out'),
        ],
        ondelete={
            "break": "cascade",
            "check_in_break": "cascade",
            "break_check_out": "cascade",
            "in_out_break": "cascade",
        })

    _sql_constraints = [
        ('unique_employee_attendance', 'check(1=1)',
         _("Employee attendance already exists"))
    ]

    def _set_attendance_state(self):
        res = super(AttendanceSheet, self)._set_attendance_state()
        for attend_sheet in self.filtered(lambda sheet: sheet.break_time > 0.0):
            late_check_in = attend_sheet.late_check_in or 0.0
            early_check_out = attend_sheet.early_check_out or 0.0
            if late_check_in > 0.0 and early_check_out > 0.0:
                attend_sheet.attendance_state = 'in_out_break'
            elif late_check_in > 0.0:
                attend_sheet.attendance_state = 'check_in_break'
            elif early_check_out > 0.0:
                attend_sheet.attendance_state = 'break_check_out'
            else:
                attend_sheet.attendance_state = 'break'
        return res

    def get_day_leaves(self, employees, days):
        return self.env['hr.leave'].search(
            [('employee_id', 'in', employees.ids), ('request_date_from', '<=', days[0]),
             ('request_date_from', '>=', days[-1]),
             ('state', '=', 'validate'), ('holiday_status_id.request_unit', '!=', 'day')])

    def get_existing_justification(self, employees, days):
        return self.search(
            [('employee_id', 'in', employees.ids), ('date', '>=', days[0]),
             ('date', '<=', days[-1])])

    def get_employees_attendance(self, employees, days):
        first_date_time = datetime.combine(days[0], time(0, 0, 0))
        last_date_time = datetime.combine(days[-1], time(23, 59, 59))
        return self.env['hr.attendance'].search(
            [('employee_id', 'in', employees.ids), ('check_in', '>=', first_date_time),
             ('check_out', '<=', last_date_time)], order='check_in asc')

    def _set_breaks(self, employees, sorted_days):
        vals_list = []

        employees_attendance = self.get_employees_attendance(employees, sorted_days)
        employee_days_leaves = self.get_day_leaves(employees, sorted_days)
        existing_employees_justification = self.get_existing_justification(employees, sorted_days)

        for employee in employees:
            if not employee.out_of_attendance:
                for day in sorted_days:

                    evening_data = employee.resource_calendar_id.attendance_ids.filtered(
                        lambda x: dict(x._fields['dayofweek'].selection).get(
                            x.dayofweek) == day.strftime(
                            '%A') and x.day_period == 'afternoon')
                    if len(evening_data) > 1:
                        evening_data = evening_data[-1]
                    calender_time_zone = pytz.timezone(employee.resource_calendar_id.tz)
                    last_log_time = float_to_time(evening_data.hour_to)
                    last_date_time_log_in = datetime.combine(day, last_log_time).astimezone(calender_time_zone)
                    last_date_time_log_in_utc = last_date_time_log_in.astimezone(pytz.timezone('UTC')).replace(
                        tzinfo=None)

                    day_employee_attendance_records = employees_attendance.filtered(
                        lambda attendance_rec: attendance_rec.check_in.date() == day and \
                                               attendance_rec.check_in < last_date_time_log_in_utc and \
                                               attendance_rec.employee_id == employee)

                    existing_justification_record = existing_employees_justification.filtered(
                        lambda
                            justification_rec: justification_rec.employee_id == employee and justification_rec.date == day)

                    employee_day_leaves = employee_days_leaves.filtered(
                        lambda leave_rec: leave_rec.employee_id == employee and leave_rec.request_date_from == day)

                    day_employee_attendance_records.sorted('check_in')
                    break_times = range(len(day_employee_attendance_records) - 1)
                    total_break = 0

                    for break_time in break_times:

                        check_out = day_employee_attendance_records[break_time].check_out
                        check_in = day_employee_attendance_records[break_time + 1].check_in
                        break_period = (check_in - check_out).total_seconds()
                        for leave in employee_day_leaves:

                            # Leave Out of break Duration
                            if leave.date_from >= check_in or check_out >= leave.date_to:
                                continue
                            # Leave inside break duration
                            elif leave.date_from >= check_out and check_in >= leave.date_to:
                                break_period = ((leave.date_from - check_out).total_seconds() + (
                                        check_in - leave.date_to).total_seconds())

                            # Below Conditions will not occure
                            # leave at beginning
                            elif leave.date_from <= check_out < leave.date_to:
                                break_period = (check_in - leave.date_to).total_seconds()

                                # leave at ending
                            elif leave.date_from <= check_in < leave.date_to:
                                break_period = (leave.date_from - check_out).total_seconds()

                        total_break += break_period

                    if not existing_justification_record and total_break > 0:
                        vals_list.append({
                            'employee_id': employee.id,
                            'date': day,
                            'attendance_state': 'break',
                            'attendance_id': day_employee_attendance_records[0].id,
                            'break_time': round(total_break / 3600, 2),
                            'check_out': 0.0,
                            'check_in': 0.0,
                        })

                    elif existing_justification_record:
                        if total_break < 0:
                            total_break = 0
                        existing_justification_record.write({'break_time': round(total_break / 3600, 2)})
                        existing_justification_record._set_attendance_state()

        created_breaks = self.create(vals_list)
        created_breaks._set_attendance_state()
