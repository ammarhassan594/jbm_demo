import logging
import pytz

from collections import namedtuple, defaultdict

from datetime import datetime, timedelta, time, date
from pytz import timezone, UTC
import math
from odoo import api, fields, models, tools
from odoo.addons.base.models.res_partner import _tz_get
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request
from odoo.tools import float_compare, format_date
from odoo.tools.float_utils import float_round
from odoo.tools.translate import _
from odoo.osv import expression

_logger = logging.getLogger(__name__)

# Used to agglomerate the attendances in order to find the hour_from and hour_to
# See _compute_date_from_to
DummyAttendance = namedtuple('DummyAttendance', 'hour_from, hour_to, dayofweek, day_period, week_type')

ATTENDANCE_SHEET_FIELDS = ['date', 'check_in', 'check_out', 'early_check_out', 'late_check_in',
                           'attendance_id']


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    attendance_sheet_ids = fields.One2many("hr.attendance.sheet", "employee_id",
                                           string="Attendances")
    allowed_violation_balance = fields.Float(string='Violations Balance', compute="_get_remaining_violation_balance")
    counter = fields.Integer()
    exceed_allowed_violation_balance = fields.Float()
    remaining_balance = fields.Float(default=0.0)

    def _get_remaining_violation_balance(self):
        print("hello from violation")
        for rec in self:
            print("hello")
            max_allowed_violation_hours = rec.env.company.max_allowed_hours
            if rec.attendance_sheet_ids:
                filtered_records = rec.attendance_sheet_ids.filtered(
                    lambda x: x.attendance_state not in ['attendance'] and x.date.month == date.today().month)
                if filtered_records:
                    late_check_ins = sum(filtered_records.filtered(lambda x: x.late_check_in).mapped('late_check_in'))
                    early_check_outs = sum(
                        filtered_records.filtered(lambda x: x.early_check_out).mapped('early_check_out'))
                    rec.allowed_violation_balance = max_allowed_violation_hours - (late_check_ins + early_check_outs)
                else:
                    rec.allowed_violation_balance = max_allowed_violation_hours
                if rec.allowed_violation_balance < 0:
                    rec.allowed_violation_balance = 0
            else:
                rec.allowed_violation_balance = max_allowed_violation_hours

    def updated_or_create_attendance_sheet(self, attendance_date='', **vals) -> int:
        """
         Update an existing attendance sheet record matching the specified parameters or creates a new one.

        :param attendance_date: The date of the attendance sheet in the format "%Y-%m-%d".
        :param vals: A dictionary containing the field names and values for the attendance sheet.
                     The available fields are:
                     - check_in (float): The check-in time in 24-hour format.
                     - check_out (float): The check-out time in 24-hour format.
                     - early_check_out (float): The time before which a check-out is considered early, in 24-hour format.
                     - late_check_in (float): The time after which a check-in is considered late, in 24-hour format.
                     - attendance_id (int): The ID of the attendance record.
        :return: The attendance sheet record that was found or created.
        :rtype: int
        """
        self.ensure_one()

        valid_fields = {key: vals.get(key) for key in vals if key in ATTENDANCE_SHEET_FIELDS}
        if not valid_fields or not attendance_date:
            raise ValidationError(_('Required fields of the attendance sheet were not provided.'))

        try:
            attendance_date = datetime.strptime(attendance_date, "%Y-%m-%d").date()
        except ValueError:
            _logger.error("Error parsing attendance date as formatted YYYY-MM-DD (2023-02-10)")
            raise UserError(_("Error parsing attendance date as formatted YYYY-MM-DD"))

        attend_sheet_record = self.attendance_sheet_ids.filtered(lambda x: x.date == attendance_date)
        if not attend_sheet_record:
            valid_fields["employee_id"] = self.id
            valid_fields["date"] = attendance_date
            attend_sheet_record = self.env['hr.attendance.sheet'].create(valid_fields)
            attend_sheet_record._set_attendance_state()
            return attend_sheet_record.id

        try:
            attend_sheet_record.write(valid_fields)
            attend_sheet_record._set_attendance_state()
        except Exception as e:
            _logger.error('Error on update attendance sheet record')
            raise Exception(_('Error on update attendance sheet record'))

        return attend_sheet_record.id

    def _daily_exceed_allowed_hours(self):
        max_allowed_violation_hours = self.env.company.max_allowed_hours
        employees = self.env['hr.employee'].search([('out_of_attendance', '!=', True)])
        data = []
        today = fields.Date.today()
        for employee in employees:
            if employee.attendance_sheet_ids:
                rec = employee.attendance_sheet_ids.filtered(
                    lambda x: x.attendance_state not in [
                        'attendance'] and x.date.month == date.today().month and x.date.year == date.today().year)
                if rec:
                    late_check_ins = sum(rec.filtered(lambda x: x.late_check_in).mapped('late_check_in'))
                    early_check_outs = sum(
                        rec.filtered(lambda x: x.early_check_out).mapped('early_check_out'))
                    breaks_hours = sum(
                        rec.filtered(lambda x: x.break_time > 0).mapped('break_time'))
                    employee.exceed_allowed_violation_balance = (
                                                                        late_check_ins + early_check_outs + breaks_hours) - max_allowed_violation_hours - (
                                                                        employee.counter * employee.resource_calendar_id.reference_violation) + employee.remaining_balance
                    # if employee.exceed_allowed_violation_balance >= employee.resource_calendar_id.reference_violation:
                    if employee.exceed_allowed_violation_balance >= employee.resource_calendar_id.reference_violation:
                        leave_type = rec.env['hr.leave.type'].search([('is_annual', '=', True)],
                                                                     limit=1)
                        annual_allocations = self.env['hr.leave.allocation'].search(
                            [('employee_id', '=', employee.id),
                             ('holiday_status_id.is_annual', '=', True),
                             ('state', '=', 'validate'), ('year', '=', date.today().year)])
                        if annual_allocations:
                            n_of_days = sum(annual_allocations.mapped('number_of_days_display'))
                            balance = sum(annual_allocations.mapped('max_leaves')) - sum(
                                annual_allocations.mapped('leaves_taken'))
                            if balance > 0:
                                # leave_date = self._find_next_valid_leave_date(employee, today)
                                # if leave_date:
                                try:
                                    # self.create_annual_leave(employee, leave_date)
                                    self.create_annual_allocation(employee)
                                    employee.counter += 1
                                except Exception:
                                    # _logger.debug("failed to create annual leave", exc_info=True)
                                    pass
                                else:
                                    pass
                    else:
                        pass
                # else:
                #     employee.counter = 0
                #     if employee.exceed_allowed_violation_balance >= employee.resource_calendar_id.reference_violation:
                #         employee.remaining_balance = employee.exceed_allowed_violation_balance - employee.resource_calendar_id.reference_violation
                #     else:
                #         employee.remaining_balance = employee.exceed_allowed_violation_balance

    def _monthly_remaining_hours(self):
        today = datetime.now().date()
        first_day_next_month = (today.replace(day=1) + timedelta(days=31)).replace(day=1)
        last_day_this_month = first_day_next_month - timedelta(days=1)

        if today == last_day_this_month:
            employees = self.env['hr.employee'].search([('out_of_attendance', '!=', True)])
            for employee in employees:
                # employee._daily_exceed_allowed_hours()
                if employee.exceed_allowed_violation_balance > 0:
                    employee.remaining_balance = employee.exceed_allowed_violation_balance
                employee.counter = 0

    def create_annual_allocation(self, employee):
        leave_type = self.env['hr.leave.type'].search([('is_annual', '=', True)],
                                                      limit=1)
        today = datetime.today()
        last_day_of_year = datetime(today.year, 12, 31)
        res = [
            {
                'name': "خصم من رصيد الإجازة الدورية بسبب استنفاذ رصيد ساعات الاستئذان الشهرية",
                'holiday_status_id': leave_type.id,
                'allocation_type': 'regular',
                'holiday_type': 'employee',
                'employee_id': employee.id,
                'number_of_days': -1,
                'year': date.today().year,
                'date_to': last_day_of_year,
                'state': 'validate',
                'created_from_violation_hours': True
            },
        ]
        allocations = self.env['hr.leave.allocation'].create(res)

    # def create_annual_leave(self, employee, leave_date):
    #     leave_type = self.env['hr.leave.type'].search([('is_annual', '=', True)],
    #                                                  limit=1)
    #     date_from, date_to = self.get_date_from_to(employee, leave_date)
    #     data = [{
    #         'employee_id': employee.id,
    #         'holiday_status_id': leave_type.id,
    #         'request_date_from': leave_date,
    #         'request_date_to': leave_date,
    #         'date_from': date_from,
    #         'date_to': date_to,
    #         'state': 'validate',
    #         'number_of_days': 1,
    #         'return_date': leave_date+timedelta(days=1),
    #         # 'approved_automatic': True,
    #         # 'payslip_id': payslip.id,
    #         'created_from_violation_hours': True,
    #         'name': "خصم من رصيد الإجازة الدورية بسبب استنفاذ رصيد ساعات الاستئذان الشهرية"
    #     }]
    #     leave = self.env['hr.leave'].sudo().with_context(leave_skip_state_check=True).create(data)

    def _find_next_valid_leave_date(self, employee, start_date):
        # Define weekends
        day_of_work = employee.contract_id.resource_calendar_id.attendance_ids.mapped('dayofweek')

        public_holiday = employee.contract_id.resource_calendar_id.global_leave_ids.filtered(
            lambda x: x.date_from.date() >= start_date).mapped('date_from') \
            if employee.contract_id else False
        public_holidays = [holiday.date() for holiday in public_holiday]

        existing_leaves = self.env['hr.leave'].search([
            ('employee_id', '=', employee.id),
            ('request_date_from', '>=', start_date),
            ('state', 'not in', ['refuse', 'cancel'])
        ]).mapped('request_date_from')

        current_date = start_date
        while True:
            if (str(current_date.weekday()) in day_of_work and
                    current_date not in public_holidays and
                    current_date not in existing_leaves):
                return current_date
            current_date += timedelta(days=1)

    def float_to_time(hours):
        """ Convert a number of hours into a time object. """
        if hours == 24.0:
            return time.max
        fractional, integral = math.modf(hours)
        return time(int(integral), int(float_round(60 * fractional, precision_digits=0)), 0)

    def get_date_from_to(self, employee, leave_date):

        resource_calendar_id = employee.resource_calendar_id or self.env.company.resource_calendar_id
        domain = [('calendar_id', '=', resource_calendar_id.id), ('display_type', '=', False)]
        attendances = self.env['resource.calendar.attendance'].read_group(domain,
                                                                          ['ids:array_agg(id)',
                                                                           'hour_from:min(hour_from)',
                                                                           'hour_to:max(hour_to)', 'week_type',
                                                                           'dayofweek',
                                                                           'day_period'],
                                                                          ['week_type', 'dayofweek', 'day_period'],
                                                                          lazy=False)

        # Must be sorted by dayofweek ASC and day_period DESC
        attendances = sorted(
            [DummyAttendance(group['hour_from'], group['hour_to'], group['dayofweek'], group['day_period'],
                             group['week_type']) for group in attendances],
            key=lambda att: (att.dayofweek, att.day_period != 'morning'))

        default_value = DummyAttendance(0, 0, 0, 'morning', False)

        attendance_from = next(
            (att for att in attendances if int(att.dayofweek) >= leave_date.weekday()),
            attendances[0] if attendances else default_value)
        attendance_to = next(
            (att for att in reversed(attendances) if int(att.dayofweek) <= leave_date.weekday()),
            attendances[-1] if attendances else default_value)

        compensated_request_date_from = leave_date
        compensated_request_date_to = leave_date

        hour_from = float_to_time(attendance_from.hour_from)
        hour_to = float_to_time(attendance_to.hour_to)

        date_from = timezone(employee.tz).localize(
            datetime.combine(compensated_request_date_from, hour_from)).astimezone(UTC).replace(tzinfo=None)
        date_to = timezone(employee.tz).localize(datetime.combine(compensated_request_date_to, hour_to)).astimezone(
            UTC).replace(tzinfo=None)

        return date_from, date_to
