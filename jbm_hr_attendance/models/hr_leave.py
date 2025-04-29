from odoo import api, fields, models, _
from pytz import UTC
from dateutil.relativedelta import relativedelta
from odoo.addons.resource.models.resource import HOURS_PER_DAY


class Leave(models.Model):
    _inherit = 'hr.leave'

    attendance_sheet_id = fields.Many2one('attendance.sheet', string='Attendance', ondelete="cascade")
    approved_automatic = fields.Boolean(string="Approved Automatic")

    @api.depends('date_from', 'date_to', 'employee_id')
    def _compute_number_of_days(self):
        for holiday in self:
            if holiday.date_from and holiday.date_to and \
                     holiday.holiday_status_id.days_based_on != 'calendar_days':
                holiday.number_of_days = \
                    holiday._get_number_of_days(holiday.date_from,
                                                holiday.date_to,
                                                holiday.employee_id.id)['days']
            elif holiday.date_from and holiday.date_to and \
                    holiday.holiday_status_id.days_based_on == 'calendar_days':
                if not holiday.request_unit_half and not holiday.request_unit_hours:
                    holiday.number_of_days = (holiday.date_to.date() -
                                              holiday.date_from.date()).days + 1
                else:
                    holiday.number_of_days = 0

                # elif holiday.request_unit_hours:
                #     if all((holiday.request_hour_to, holiday.request_hour_from)):
                #         holiday.number_of_hours_display = float(holiday.request_hour_to) - float(
                #             holiday.request_hour_from)
                #         holiday.number_of_days_display = holiday.number_of_hours_display
                #         # # holiday.number_of_days = holiday.number_of_hours_display
                #         # print('holiday.number_of_days', holiday.number_of_days)
                #         # print('holiday.number_of_days_display', holiday.number_of_days_display)
            else:
                holiday.number_of_days = 0

    @api.depends('number_of_days')
    def _compute_number_of_hours_display(self):
        for holiday in self:
            calendar = holiday._get_calendar()
            if holiday.date_from and holiday.date_to and \
                    holiday.holiday_status_id.days_based_on != 'calendar_days':
                # Take attendances into account, in case the leave validated
                # Otherwise, this will result into number_of_hours = 0
                # and number_of_hours_display = 0 or (#day * calendar.hours_per_day),
                # which could be wrong if the employee doesn't work the same number
                # hours each day
                if holiday.state == 'validate':
                    start_dt = holiday.date_from
                    end_dt = holiday.date_to
                    if not start_dt.tzinfo:
                        start_dt = start_dt.replace(tzinfo=UTC)
                    if not end_dt.tzinfo:
                        end_dt = end_dt.replace(tzinfo=UTC)
                    resource = holiday.employee_id.resource_id
                    intervals = calendar._attendance_intervals_batch(start_dt, end_dt, resource)[resource.id] \
                                - calendar._leave_intervals_batch(start_dt, end_dt, None)[
                                    False]  # Substract Global Leaves
                    number_of_hours = sum((stop - start).total_seconds() / 3600 for start, stop, dummy in intervals)
                else:
                    number_of_hours = \
                        holiday._get_number_of_days(holiday.date_from,
                                                    holiday.date_to,
                                                    holiday.employee_id.id)['hours']
                holiday.number_of_hours_display = number_of_hours or (
                        holiday.number_of_days * (calendar.hours_per_day or HOURS_PER_DAY))
            elif holiday.date_from and holiday.date_to and \
                    holiday.holiday_status_id.days_based_on == 'calendar_days':
                holiday.number_of_hours_display = 0
                if holiday.request_unit_hours:
                    if all((holiday.request_hour_to, holiday.request_hour_from)):
                        holiday.number_of_hours_display = \
                            (float(holiday.request_hour_to) - float(
                                holiday.request_hour_from)) or (
                                    holiday.number_of_days * (
                                    calendar.hours_per_day or HOURS_PER_DAY))
                else:
                    number_of_hours = \
                        holiday._get_number_of_days(holiday.date_from, holiday.date_to, holiday.employee_id.id)['hours']
                    holiday.number_of_hours_display = number_of_hours or (
                            holiday.number_of_days * (calendar.hours_per_day or HOURS_PER_DAY))

            else:
                holiday.number_of_hours_display = 0

    def activity_update(self):
        to_clean, to_do = self.env['hr.leave'].sudo(), self.env['hr.leave'].sudo()
        for holiday in self:
            holiday = holiday.sudo()
            note = _(
                'New %(leave_type)s Request created by %(user)s',
                leave_type=holiday.holiday_status_id.name,
                user=holiday.create_uid.name,
            )
            deadline_after = holiday.holiday_status_id.employee_approver_days
            date_deadline = (fields.Date.today())
            user =  holiday.sudo()._get_responsible_for_approval() or self.env.user
            employee = self.env['hr.employee'].sudo().search([
                ('user_id', '=', user.id) if user else False
            ])
            if employee:
                contract = employee.active_contract if employee.active_contract else False
                if contract:
                    for day in range(int(deadline_after)):
                        date = date_deadline + relativedelta(days=1)
                        weekend = str(date.weekday()) not in set(
                            contract.resource_calendar_id.attendance_ids.mapped('dayofweek'))

                        public_holiday = contract.resource_calendar_id.global_leave_ids.filtered(
                            lambda x: x.date_from.date() <= date <= x.date_to.date())

                        while weekend or public_holiday:
                            date = date + relativedelta(days=1)
                            weekend = str(date.weekday()) not in set(
                                contract.resource_calendar_id.attendance_ids.mapped('dayofweek'))
                            public_holiday = contract.resource_calendar_id.global_leave_ids.filtered(
                                lambda x: x.date_from.date() <= date <= x.date_to.date())

                        if not weekend and not public_holiday:
                            date_deadline = date

            if holiday.state == 'draft':
                to_clean |= holiday
            elif holiday.state == 'confirm':
                # deadline_after = holiday.holiday_status_id.employee_approver_days
                # date_deadline = (fields.Date.today() + relativedelta(days=deadline_after))
                holiday.activity_schedule(
                    'hr_holidays.mail_act_leave_approval',
                    date_deadline=date_deadline,
                    note=note,
                    user_id=user.id)
            elif holiday.state == 'validate1':
                # deadline_after = holiday.holiday_status_id.time_off_officer_days
                # date_deadline = (fields.Date.today() + relativedelta(days=deadline_after))
                holiday.activity_feedback(['hr_holidays.mail_act_leave_approval'])
                holiday.activity_schedule(
                    'hr_holidays.mail_act_leave_second_approval',
                    date_deadline=date_deadline,
                    note=note,
                    user_id=user.id)
            elif holiday.state == 'validate':
                to_do |= holiday
            elif holiday.state == 'refuse':
                to_clean |= holiday
        if to_clean:
            to_clean.activity_unlink(
                ['hr_holidays.mail_act_leave_approval', 'hr_holidays.mail_act_leave_second_approval'])
        if to_do:
            to_do.activity_feedback(
                ['hr_holidays.mail_act_leave_approval', 'hr_holidays.mail_act_leave_second_approval'])
