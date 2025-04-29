# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, time
from dateutil.relativedelta import relativedelta
from odoo.addons.resource.models.resource import HOURS_PER_DAY


class HrLeaveAllocation(models.Model):
    _inherit = "hr.leave.allocation"

    date_button = fields.Selection(
        [
            ('start', 'Start Date'),
            ('joining', 'Joining Date')
        ], string="Date", default="start", required=True)
    start_date = fields.Date(
        string='Start Date')
    joining_date = fields.Date(
        string='Joining Date',
        related='employee_id.joining_date')

    year = fields.Integer(string="Year", default=fields.Date.today().year, required=True)

    @api.model
    def _update_accrual(self):
        """
            Method called by the cron task in order to increment the number_of_days when
            necessary.
        """
        # Get the current date to determine the start and end of the accrual period
        today = datetime.combine(fields.Date.today(), time(0, 0, 0))
        this_year_first_day = today + relativedelta(day=1, month=1)
        end_of_year_allocations = self.search(
        [('allocation_type', '=', 'accrual'), ('state', '=', 'validate'), ('accrual_plan_id', '!=', False), ('employee_id', '!=', False),
            '|', ('date_to', '=', False), ('date_to', '>', fields.Datetime.now()), ('lastcall', '<', this_year_first_day)])
        end_of_year_allocations._end_of_year_accrual()
        end_of_year_allocations.flush()
        allocations = self.search(
        [('allocation_type', '=', 'accrual'), ('state', '=', 'validate'), ('accrual_plan_id', '!=', False), ('employee_id', '!=', False),
            '|', ('date_to', '=', False), ('date_to', '>', fields.Datetime.now()),
            '|', ('nextcall', '=', False), ('nextcall', '<=', today)])
        allocations._process_accrual_plans()

    # @api.model
    # def _update_accrual(self):
    #     """
    #         Method called by the cron task in order to increment the number_of_days when
    #         necessary.
    #     """
    #     today = fields.Date.from_string(fields.Date.today())
    #     holidays = self.search(
    #         [('allocation_type', '=', 'accrual'), ('employee_id.active', '=', True), ('state', '=', 'validate'),
    #          ('holiday_type', '=', 'employee'),
    #          '|', ('date_to', '=', False), ('date_to', '>', fields.Datetime.now()),
    #          '|', ('nextcall', '=', False), ('nextcall', '<=', today)])
    #     for holiday in holidays:
    #         values = {}
    #         delta = relativedelta(days=0)
    #         if holiday.interval_unit == 'weeks':
    #             delta = relativedelta(weeks=holiday.interval_number)
    #         if holiday.interval_unit == 'months':
    #             delta = relativedelta(months=holiday.interval_number)
    #         if holiday.interval_unit == 'years':
    #             delta = relativedelta(years=holiday.interval_number)
    #         values['nextcall'] = (holiday.nextcall if holiday.nextcall else today) + delta
    #         # period_start = datetime.combine(today, time(0, 0, 0)) - delta
    #         period_end = datetime.combine(today, time(0, 0, 0))
    #         # We have to check when the employee has been created
    #         # in order to not allocate him/her too much leaves
    #         if holiday.date_button == 'start':
    #             start_date_holiday = holiday.start_date
    #             start_date = datetime.strptime(
    #                 str(start_date_holiday) + ' 00:00:00',
    #                 "%Y-%m-%d %H:%M:%S")
    #         elif holiday.date_button == 'joining':
    #             join_date = holiday.joining_date
    #             start_date = datetime.strptime(
    #                 str(join_date) + ' 00:00:00',
    #                 "%Y-%m-%d %H:%M:%S")
    #         else:
    #             start_date = holiday.employee_id._get_date_start_work()
    #         # If employee is created after the period, we cancel the computation
    #         if period_end <= start_date:
    #             holiday.write(values)
    #             continue
    #         # If employee created during the period, taking the date at which he has been created
    #         # if period_start <= start_date:
    #         # if start_date.day == date.today().day:
    #         period_start = start_date
    #         # worked = holiday.employee_id._get_work_days_data(period_start, period_end,
    #         #                                                  domain=[('holiday_id.holiday_status_id.unpaid', '=', True),
    #         #                                                          ('time_type', '=', 'leave')])['days']
    #         # left = holiday.employee_id._get_leave_days_data(period_start, period_end,
    #         #                                                 domain=[('holiday_id.holiday_status_id.unpaid', '=', True),
    #         #                                                         ('time_type', '=', 'leave')])['days']
    #         # prorata = worked / (left + worked) if worked else 0
    #         days_to_give = holiday.number_per_interval
    #         if holiday.unit_per_interval == 'hours':
    #             # As we encode everything in days in the database we need to convert
    #             # the number of hours into days for this we use the
    #             # mean number of hours set on the employee's calendar
    #             days_to_give = days_to_give / (holiday.employee_id.resource_calendar_id.hours_per_day or HOURS_PER_DAY)
    #         if holiday.interval_unit == 'months':
    #             if period_start.day <= 15 and period_end.day <= 15:
    #                 period = (period_end.year - period_start.year) * 12 + ((period_end.month - 1) - period_start.month)
    #             elif period_start.day > 15 and period_end.day <= 15:
    #                 period = (period_end.year - period_start.year) * 12 + (period_end.month - period_start.month)
    #             elif period_start.day <= 15 and period_end.day > 15:
    #                 period = (period_end.year - period_start.year) * 12 + ((period_end.month + 1) - period_start.month)
    #             else:
    #                 period = (period_end.year - period_start.year) * 12 + (
    #                             (period_end.month - 1) - (period_start.month - 1))
    #             period = period / holiday.interval_number
    #             # values['number_of_days'] = holiday.number_of_days + days_to_give + prorata
    #             values['number_of_days'] = (days_to_give * period)
    #         if holiday.accrual_limit > 0:
    #             values['number_of_days'] = min(values['number_of_days'], holiday.accrual_limit)
    #             print(values)
    #         holiday.write(values)
