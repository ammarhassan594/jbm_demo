import time
from datetime import datetime, timedelta, date, time as time_fun
import pytz

import babel
from dateutil.relativedelta import relativedelta
from odoo import models, fields, tools, api, exceptions, _
from odoo.exceptions import ValidationError
import pytz

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TIME_FORMAT = "%H:%M:%S"


def float_to_time(float_type):
    str_off_time = str(float_type)
    official_hour = str_off_time.split('.')[0]
    official_minute = ("%2d" % int(str(float("0." + str_off_time.split('.')[1]) * 60).split('.')[0])).replace(' ', '0')
    str_off_time = official_hour + ":" + official_minute
    str_off_time = datetime.strptime(str_off_time, "%H:%M").time()
    return str_off_time


def _get_float_from_time(time):
    time_type = datetime.strftime(time + timedelta(hours=2), "%H:%M")
    signOnP = [int(n) for n in time_type.split(":")]
    signOnH = signOnP[0] + signOnP[1] / 60.0
    return signOnH


def get_diff_btw_2_dates(date_from, date_to):
    return (date_to - date_from).days


def remove_duplicates(lst):
    lst_without_dup = []
    for day in lst:
        if day not in lst_without_dup:
            lst_without_dup.append(day.date())
    return lst_without_dup


class attendance_sheet(models.Model):
    _name = 'attendance.sheet'

    name = fields.Char("name", translate=True)

    def action_attsheet_confirm(self):
        self.write({'state': 'confirm'})
        return True

    def action_attsheet_approve(self):
        # self.calculate_att_data()
        self.write({'state': 'done'})
        for line in self.att_sheet_line_ids:
            line.write({'state': 'done'})
        return True

    def action_attsheet_draft(self):
        self.write({'state': 'draft'})
        for line in self.att_sheet_line_ids:
            line.write({'state': 'draft'})
        return True

    # overtime_request_ids = fields.One2many(comodel_name="hr.overtime", inverse_name="attendance_sheet_ids",
    #                                        string="Overtime",
    #                                        domain="[('employee_id', '=', 'employee_id')]")
    contract_id = fields.Many2one('hr.contract', compute='_get_employee_contract', store=True, string="Contract")
    contract_ids = fields.Many2many('hr.contract', string="Contracts")

    basic_allowance = fields.Float(string="Basic Allowance")
    housing_allowance = fields.Float(string="Housing Allowance")
    social_allowance = fields.Monetary(string="Social Allowance")
    transportation_allowance = fields.Float(string="Transportation Allowance")
    mobile_allowance = fields.Float(string="Mobile Allowance")
    other_allowance = fields.Float(string="Other Allowance")
    car_allowance = fields.Float(string="Car Allowance")
    supervision_allowance = fields.Float(string="Supervision Allowance")
    earning_allowance = fields.Float(string="Earning Settlement")
    eobs_allowance = fields.Float(string="EOBS Allowance")
    monthly_incentive_allowance = fields.Float(string="Monthly Incentive Allowance")
    representative_monthly_allowance = fields.Float(string="Representative Allowance")
    work_condition_allowance = fields.Float(string="Work Condition Allowance")

    basic_deduction = fields.Float(string="Basic Deduction")
    other_deduction = fields.Float(string="Other Deduction")
    transportation_deduction = fields.Float(string="Transportation Deduction")
    housing_deduction = fields.Float(string="Housing Deduction")
    mobile_deduction = fields.Float(string="Mobile Deduction")
    social_deduction = fields.Float(string="Social Deduction")
    car_deduction = fields.Float(string="Car Deduction")
    supervision_deduction = fields.Float(string="Supervision Deduction")
    deduction_settlement = fields.Float(string="Deduction Settlement")
    eobs_deduction = fields.Float(string="EOBS Deduction")
    monthly_deduction = fields.Float(string="Monthly Incentive Deduction")
    representative_deduction = fields.Float(string="Representative Deduction")
    work_condition_deduction = fields.Float(string="Work Condition Deduction")

    basic_allowance_second = fields.Float(string="Basic Allowance Second")
    housing_allowance_second = fields.Float(string="Housing Allowance Second")
    social_allowance_second = fields.Monetary(string="Social Allowance Second")
    transportation_allowance_second = fields.Float(string="Transportation Allowance Second")
    mobile_allowance_second = fields.Float(string="Mobile Allowance Second")
    other_allowance_second = fields.Float(string="Other Allowance Second")
    car_allowance_second = fields.Float(string="Car Allowance Second")
    supervision_allowance_second = fields.Float(string="Supervision Allowance Second")
    eobs_allowance_second = fields.Float(string="EOBS Allowance Second")
    monthly_incentive_allowance_second = fields.Float(string="Monthly Incentive Allowance Second")
    representative_monthly_allowance_second = fields.Float(string="Representative Allowance Second")
    work_condition_allowance_second = fields.Float(string="Work Condition Allowance Second")

    basic_deduction_second = fields.Float(string="Basic Deduction Second")
    other_deduction_second = fields.Float(string="Other Deduction Second")
    transportation_deduction_second = fields.Float(string="Transportation Deduction Second")
    housing_deduction_second = fields.Float(string="Housing Deduction Second")
    mobile_deduction_second = fields.Float(string="Mobile Deduction Second")
    social_deduction_second = fields.Float(string="Social Deduction Second")
    car_deduction_second = fields.Float(string="Car Deduction Second")
    supervision_deduction_second = fields.Float(string="Supervision Deduction Second")
    eobs_deduction_second = fields.Float(string="EOBS Deduction Second")
    monthly_deduction_second = fields.Float(string="Monthly Incentive Deduction Second")
    representative_deduction_second = fields.Float(string="Representative Deduction Second")
    work_condition_deduction_second = fields.Float(string="Work Condition Deduction Second")

    basic_allowance_tot = fields.Float(string="Basic Allowance Tot")
    housing_allowance_tot = fields.Float(string="Housing Allowance Tot")
    social_allowance_tot = fields.Monetary(string="Social Allowance Tot")
    transportation_allowance_tot = fields.Float(string="Transportation Allowance Tot")
    mobile_allowance_tot = fields.Float(string="Mobile Allowance Tot")
    other_allowance_tot = fields.Float(string="Other Allowance Tot")
    car_allowance_tot = fields.Float(string="Car Allowance Tot")
    supervision_allowance_tot = fields.Float(string="Supervision Allowance Tot")
    eobs_allowance_tot = fields.Float(string="EOBS Allowance Tot")
    monthly_incentive_allowance_tot = fields.Float(string="Monthly Incentive Allowance Tot")
    representative_monthly_allowance_tot = fields.Float(string="Representative Allowance Tot")
    work_condition_allowance_tot = fields.Float(string="Work Condition Allowance Tot")

    basic_deduction_tot = fields.Float(string="Basic Deduction Tot")
    other_deduction_tot = fields.Float(string="Other Deduction Tot")
    transportation_deduction_tot = fields.Float(string="Transportation Deduction Tot")
    housing_deduction_tot = fields.Float(string="Housing Deduction Tot")
    mobile_deduction_tot = fields.Float(string="Mobile Deduction Tot")
    social_deduction_tot = fields.Float(string="Social Deduction Tot")
    car_deduction_tot = fields.Float(string="Car Deduction Tot")
    supervision_deduction_tot = fields.Float(string="Supervision Deduction Tot")
    eobs_deduction_tot = fields.Float(string="EOBS Deduction Tot")
    monthly_incentive_deduction_tot = fields.Float(string="Monthly Incentive Deduction Tot")
    representative_deduction_tot = fields.Float(string="Representative Deduction Tot")
    work_condition_deduction_tot = fields.Float(string="Work Condition Deduction Tot")

    leave_ids = fields.One2many(comodel_name="hr.leave", inverse_name="attendance_sheet_id")
    employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee', required=True)
    employee_number = fields.Char(related='employee_id.registration_number', string='Employee Number')
    department_id = fields.Many2one(related='employee_id.department_id', store=True)
    date_from = fields.Date(string="From", required=True, default=time.strftime('%Y-%m-01'))
    date_to = fields.Date(string="To", required=True,
                          default=str(datetime.now() + relativedelta(months=+1, day=1, days=-1))[:10])
    actual_date_from = fields.Date()
    actual_date_to = fields.Date()
    att_sheet_line_ids = fields.One2many(comodel_name='attendance.sheet.line', string='Attendances', readonly=True,
                                         inverse_name='att_sheet_id')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('done', 'Approved')], default='draft', track_visibility='onchange',
        string='Status', required=True, readonly=True, index=True,
        help=' * The \'Draft\' status is used when a HR user is creating a new  attendance sheet. '
             '\n* The \'Confirmed\' status is used when  attendance sheet is confirmed by HR user.'
             '\n* The \'Approved\' status is used when  attendance sheet is accepted by the HR Manager.')
    # payslip_id = fields.Many2one(comodel_name='hr.payslip', string='PaySlip', copy=False)

    total_num_of_abscence_days = fields.Float("Abscence Days", default=0)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    note = fields.Text("Notes", readonly=True)
    batch_id = fields.Many2one(comodel_name='hr.attendance.batch', string='Attendance Sheet Batch', ondelete="cascade")
    lines_count = fields.Integer(compute='_compute_lines_count')

    total_termination_days = fields.Integer()
    basic_deduction_termination = fields.Float()
    other_deduction_termination = fields.Float()
    transportation_deduction_termination = fields.Float()
    housing_deduction_termination = fields.Float()
    mobile_deduction_termination = fields.Float()
    social_deduction_termination = fields.Float()
    car_deduction_termination = fields.Float()
    supervision_deduction_termination = fields.Float()
    eobs_deduction_termination = fields.Float()
    monthly_incentive_deduction_termination = fields.Float()
    representative_deduction_termination = fields.Float()
    work_condition_deduction_termination = fields.Float()

    @api.depends('employee_id')
    def _get_employee_contract(self):
        for rec in self:
            if rec.employee_id:
                rec.contract_id = rec.employee_id.contract_id.id
            else:
                rec.contract_id = None

    @api.onchange('employee_id', 'date_from', 'date_to')
    def onchange_employee(self):
        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return
        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to

        # ttyme = datetime.fromtimestamp(time.mktime(time.strptime(date_from, "%Y-%m-%d")))
        locale = self.env.context.get('lang', 'en_US')
        if locale == "ar_SY":
            locale = "ar"
        self.name = _('Attendance Sheet of %s for %s') % (employee.name,
                                                          tools.ustr(
                                                              babel.dates.format_date(date=date_from, format='MMMM-y',
                                                                                      locale=locale)))
        # self.company_id = employee.company_id

    def _get_days_since_joining_days(self):
        for rec in self:
            joining_date = rec.employee_id.joining_date
            if not joining_date:
                raise ValidationError(_("Please, Set Joining Date of Employee %s" % (rec.employee_id.name)))
            if joining_date and joining_date <= rec.date_from:
                return [(rec.date_from + timedelta(days=x)) for x in range((rec.date_to - rec.date_from).days + 1)]
            else:
                return [(joining_date + timedelta(days=x)) for x in range((rec.date_to - joining_date).days + 1)]

    def get_leave_days(self, leaves, work_days):
        for rec in self:
            legal_days = []
            unpaid_leaves = []
            for leave in leaves:
                from_date = leave.date_from.date()
                to_date = leave.date_to.date()
                if leave.holiday_status_id.is_unpaid:
                    if leave.holiday_status_id.days_based_on == 'calendar_days':
                        unpaid_leaves += [(leave.holiday_status_id,from_date + timedelta(days=x)) for x in range((to_date - from_date).days + 1)
                                          if rec.date_from <= (from_date + timedelta(days=x)) <= rec.date_to]
                    else:
                        unpaid_leaves += [(leave.holiday_status_id,from_date + timedelta(days=x)) for x in range((to_date - from_date).days + 1)
                                          if rec.date_from <= (from_date + timedelta(days=x)) <= rec.date_to and str((from_date + timedelta(days=x)).weekday()) in work_days]

                else:
                    if leave.number_of_days >= 1:
                        legal_days += [(leave.holiday_status_id,from_date + timedelta(days=x)) for x in
                                       range((to_date - from_date).days + 1)
                                       if rec.date_from <= (from_date + timedelta(days=x)) <= rec.date_to]
            return legal_days, unpaid_leaves

    def get_employee_leaves(self, work_days):
        for rec in self:
            leaves = rec.env['hr.leave'].search(
                [('employee_id', '=', rec.employee_id.id), ('date_from', '<=', rec.date_to),
                 ('date_to', '>=', rec.date_from), ('state', '=', 'validate')])
            return rec.get_leave_days(leaves, work_days)

    def get_public_holidays(self):
        for rec in self:
            public_holidays = []
            contracts = rec.contract_ids
            if len(contracts) >= 2:
                for contract in rec.contract_ids:
                    for p_holiday in contract.resource_calendar_id.global_leave_ids:
                        from_date = p_holiday.date_from.date()
                        to_date = p_holiday.date_to.date()
                        if from_date <= rec.date_to and to_date >= rec.date_from:
                            public_holidays += [(from_date + timedelta(days=x)) for x in
                                                range((to_date - from_date).days + 1) if
                                                rec.date_from <= (from_date + timedelta(days=x)) <= rec.date_to]
            else:
                for p_holiday in rec.contract_id.resource_calendar_id.global_leave_ids:
                    from_date = p_holiday.date_from.date()
                    to_date = p_holiday.date_to.date()
                    if from_date <= rec.date_to and to_date >= rec.date_from:
                        public_holidays += [(from_date + timedelta(days=x)) for x in
                                            range((to_date - from_date).days + 1) if
                                            rec.date_from <= (from_date + timedelta(days=x)) <= rec.date_to]
            return public_holidays

    def get_working_days_of_the_week(self):
        for rec in self:
            return set(
                [workday.dayofweek for workday in rec.contract_id.resource_calendar_id.attendance_ids])

    def _get_employee_leave_balance(self):
        for rec in self:
            remaining_leaves = 0
            balance = rec.env['hr.leave.allocation'].search([('employee_id', '=', rec.employee_id.id),
                                                             ('holiday_status_id.is_casual_leave_type', '=', True),
                                                             ('state', '=', 'validate')])

            if balance:
                for allocation in balance:
                    if allocation.date_from and allocation.date_to:
                        if rec.date_from >= allocation.date_from and rec.date_to <= allocation.date_to:
                            remaining_leaves += allocation.remaining_leaves
                    elif allocation.date_from and not allocation.date_to:
                        if rec.date_from >= allocation.date_from:
                            remaining_leaves += allocation.remaining_leaves

            # n_of_allocations = sum(balance.mapped('number_of_days'))
            # leaves_taken = sum(rec.env['hr.leave'].search([('employee_id', '=', rec.employee_id.id),
            #                                                ('holiday_status_id.is_annual', '=', True),
            #                                                ('state', '=', 'validate')]).mapped('number_of_days'))
            # remaining_leaves = n_of_allocations - leaves_taken
            return remaining_leaves

    def prepare_sheet_lines(self, latest_contract, work_days):
        for rec in self:
            sheet_days = rec._get_days_since_joining_days()
            day_status = {}
            attendance = rec.env["hr.attendance"].search([('employee_id', '=', rec.employee_id.id)],
                                                         order='id').filtered(
                lambda x: x.check_in.date() >= sheet_days[0] and x.check_in.date() <= sheet_days[-1])
            public_holidays = rec.get_public_holidays()
            leaves = rec.get_employee_leaves(work_days)
            legal_leaves, unpaid_leaves = leaves
            for attend in attendance:
                if latest_contract.date_end and attend.check_in.date() <= latest_contract.date_end:
                    day_status.update({f'{attend.check_in.date()}': ('', attend)})
            for day in public_holidays:
                if not day_status.get(f'{day}') and latest_contract.date_end and day <= latest_contract.date_end:
                    day_status.update({f'{day}': ('Public Holiday', day)})
            for day in legal_leaves:
                if not day_status.get(f'{day[1]}') and latest_contract.date_end and day[1] <= latest_contract.date_end:
                    day_status.update({f'{day[1]}': (day[0], day[1])})
            for day in unpaid_leaves:
                if not day_status.get(f'{day[1]}') and latest_contract.date_end and day[1] <= latest_contract.date_end:
                    day_status.update({f'{day[1]}': (day[0], day[1])})
            return sheet_days, day_status, unpaid_leaves, attendance, legal_leaves

    # def check_weekend_status(self, day, day_str, unpaid_leaves, day_status_dict):
    #     for rec in self:
    #         absent = 0
    #         day_before = day + relativedelta(days=-1)
    #         day_after = day + relativedelta(days=1)
    #         day_before_st = day_status_dict.get(f'{day_before}')
    #         day_after_st = day_status_dict.get(f'{day_after}')
    #         if (day_before_st and day_before_st[0] == 'a') or (day_after_st and day_after_st[0] == 'a'):
    #             return {'date': day, 'day': day_str, 'att_sheet_id': rec.id, 'status': 'weekend'}, absent
    #         else:
    #             absent += 1
    #             return {'date': day, 'day': day_str, 'att_sheet_id': rec.id, 'status': 'unpaid_leave'}, absent

    def check_absence_days_status(self, absence_days, result):
        return 0
        # for rec in self:
        #     total_absence_days = 0
        #     if rec.employee_id.out_of_attendance:
        #         for day in absence_days:
        #             result.append({'date': day[0], 'day': day[1], 'att_sheet_id': rec.id, 'status_char': 'Out OF Attednance'})
        #     else:
        #         r_leave_balance = rec._get_employee_leave_balance()
        #         new_leaves = []
        #         consecutive_days = []
        #         res = []
        #         daily_working_hours = rec.contract_ids[-1].resource_calendar_id.hours_per_day
        #         for day in absence_days:
        #             if rec.employee_id.out_of_attendance:
        #                 result.append({'date': day[0], 'day': day[1], 'att_sheet_id': rec.id, 'status_char': 'Absence'})
        #             if r_leave_balance >= daily_working_hours:
        #                 r_leave_balance -= daily_working_hours
        #                 new_leaves.append(day)
        #             else:
        #                 total_absence_days += 1
        #                 result.append({'date': day[0], 'day': day[1], 'att_sheet_id': rec.id, 'status_char': 'Absence'})
        #         if new_leaves:
        #             leave_type = rec.env['hr.leave.type'].search([('is_casual_leave_type', '=', True)],
        #                                                          limit=1)
        #             # result.append({'date': new_leaves[0][0], 'day': new_leaves[0][1], 'att_sheet_id': rec.id,
        #             #                'status_char': leave_type.name})
        #             for i in range(0, len(new_leaves)):
        #                 result.append({'date': new_leaves[i][0], 'day': new_leaves[i][1], 'att_sheet_id': rec.id,
        #                                'status_char': leave_type.name})
        #                 # if new_leaves[i][0] + relativedelta(days=-1) == new_leaves[i - 1][0]:
        #                 #     consecutive_days.append(new_leaves[i][0])
        #                 # else:
        #                 #     fmt = "%Y-%m-%d %H:%M:%S"
        #                 #     tz = pytz.timezone('Asia/Qatar')
        #                 #     now_utc = datetime.now(pytz.timezone('UTC'))
        #                 #     now_timezone = now_utc.astimezone(tz)
        #                 #     UTC_OFFSET_TIMEDELTA = datetime.strptime(now_timezone.strftime(fmt), fmt) - datetime.strptime(
        #                 #         now_utc.strftime(fmt), fmt)
        #                 #
        #                 #     date_from = datetime.strptime(consecutive_days[0].strftime(fmt), fmt)
        #                 #     date_from = date_from - UTC_OFFSET_TIMEDELTA
        #                 #     date_to = datetime.strptime(consecutive_days[-1].strftime(fmt), fmt)
        #                 #     date_to = date_to - UTC_OFFSET_TIMEDELTA
        #                 day_date = new_leaves[i][0]
        #                 date_from = datetime(day_date.year, day_date.month,
        #                                           day_date.day, 5, 0, 0)
        #                 date_to = datetime(day_date.year, day_date.month,
        #                                           day_date.day, 14, 0, 0)
        #
        #                 res.append({
        #                     'employee_id': rec.employee_id.id,
        #                     'holiday_status_id': leave_type.id,
        #                     'request_date_from': day_date,
        #                     'request_date_to': day_date,
        #                     'date_from': date_from,
        #                     'date_to': date_to,
        #                     'state': 'draft',
        #                     'number_of_days': 1,
        #                     'approved_automatic': True,
        #                     'attendance_sheet_id': rec.id
        #                 })
        #             #         consecutive_days = [new_leaves[i][0]]
        #             # if consecutive_days:
        #             #     fmt = "%Y-%m-%d %H:%M:%S"
        #             #     tz = pytz.timezone('Asia/Qatar')
        #             #     now_utc = datetime.now(pytz.timezone('UTC'))
        #             #     now_timezone = now_utc.astimezone(tz)
        #             #     UTC_OFFSET_TIMEDELTA = datetime.strptime(now_timezone.strftime(fmt), fmt) - datetime.strptime(
        #             #         now_utc.strftime(fmt), fmt)
        #             #
        #             #     date_from = datetime.strptime(consecutive_days[0].strftime(fmt), fmt)
        #             #     date_from = date_from - UTC_OFFSET_TIMEDELTA
        #             #     date_to = datetime.strptime(consecutive_days[-1].strftime(fmt), fmt)
        #             #     date_to = date_to - UTC_OFFSET_TIMEDELTA
        #             #     res.append({'employee_id': rec.employee_id.id,
        #             #                 'holiday_status_id': leave_type.id,
        #             #                 'request_date_from': consecutive_days[0],
        #             #                 'request_date_to': consecutive_days[-1],
        #             #                 'date_from': date_from,
        #             #                 'date_to': date_to,
        #             #                 'state': 'draft',
        #             #                 'approved_automatic': True,
        #             #                 'attendance_sheet_id': rec.id})
        #             print('employee', rec.employee_id.name)
        #             leaves = rec.env['hr.leave'].create(res)
        #             # leaves._compute_number_of_days()
        #             for l in leaves:
        #                 l.write({'state': 'validate'})
        #     return total_absence_days

    def check_if_is_new_joiner(self):
        for rec in self:
            joining_date = rec.employee_id.joining_date
            date_from = rec.date_from
            date_to = rec.date_to
            c_m_remaining_d = 0
            r_d_from_p_month = 0
            if date_from < joining_date <= date_to:
                if rec.actual_date_from < joining_date <= date_to:
                    c_m_remaining_d += joining_date.day - 1
                else:
                    last_day = rec.actual_date_from + relativedelta(days=-1)
                    r_d_from_p_month += (last_day - joining_date).days + 1
            return rec.get_new_joiners_salary_settlements(c_m_remaining_d, r_d_from_p_month)

    def get_new_joiners_salary_settlements(self, c_m_remaining_d, r_d_from_p_month):
        for rec in self:
            res = {}
            if r_d_from_p_month:
                res.update({'earning_allowance': rec.contract_id.gross / 30 * r_d_from_p_month,
                            'deduction_settlement': 0})
            elif c_m_remaining_d:
                print('rec.contract_id.gross / 30 * c_m_remaining_d', rec.contract_id.gross / 30 * c_m_remaining_d)
                res.update({'deduction_settlement': rec.contract_id.gross / 30 * c_m_remaining_d,
                            'earning_allowance': 0})
            return res

    def get_salary_allowances_and_deductions(self, total_absence_days, total_termination_days):
        for rec in self:
            res = {}
            termination_rate = total_termination_days / 30
            if len(rec.contract_ids) >= 2:
                contracts = rec.contract_ids.sorted(key=lambda x: x.date_start)
                first_contract = contracts[0]
                second_contract = contracts[1]
                f_contract_days = rec.att_sheet_line_ids.filtered(
                    lambda x: first_contract.date_start <= x.date <= first_contract.date_end)
                s_contract_days = rec.att_sheet_line_ids.filtered(
                    lambda x: second_contract.date_start <= x.date <= second_contract.date_end)
                total_days = len(f_contract_days) + len(s_contract_days)
                if rec.date_from.month == 2:
                    last_date = rec.actual_date_from + relativedelta(days=-1)
                    increment = 1 if last_date.day == 29 else 2
                    total_days += increment
                    if first_contract.date_start < last_date < first_contract.date_end:
                        f_c_days_num = (len(f_contract_days) + 1) / 30
                        s_c_days_num = len(s_contract_days) / 30 if total_days <= 30 else (len(s_contract_days) - 1) / 30

                    else:
                        f_c_days_num = len(f_contract_days) / 30
                        s_c_days_num = (len(s_contract_days) + 1) / 30 if total_days <= 30 else (len(s_contract_days) - 1) / 30
                else:
                    f_c_days_num = len(f_contract_days) / 30
                    s_c_days_num = len(s_contract_days) / 30 if total_days <= 30 else (len(s_contract_days) - 1) / 30

                f_contract_a_days = f_contract_days.filtered(lambda x: x.status == 'Absence' or (x.leave_type_id and x.leave_type_id.is_unpaid))
                s_contract_a_days = s_contract_days.filtered(lambda x: x.status in ['Absence', 'End Contract'] or (x.leave_type_id and x.leave_type_id.is_unpaid))
                f_day_abs_rate = len(f_contract_a_days) / 30
                s_day_abs_rate = (total_absence_days - len(f_contract_a_days)) / 30
                res.update({
                    'basic_allowance': f_c_days_num * first_contract.wage,
                    'basic_deduction': f_day_abs_rate * first_contract.wage,
                    'mobile_allowance': f_c_days_num * first_contract.mobile_alw,
                    'mobile_deduction': f_day_abs_rate * first_contract.mobile_alw,
                    'housing_allowance': f_c_days_num * first_contract.housing_alw,
                    'housing_deduction': f_day_abs_rate * first_contract.housing_alw,
                    'other_allowance': f_c_days_num * first_contract.other_alw,
                    'other_deduction': f_day_abs_rate * first_contract.other_alw,
                    'transportation_allowance': f_c_days_num * first_contract.transport_alw,
                    'transportation_deduction': f_day_abs_rate * first_contract.transport_alw,
                    'social_allowance': f_c_days_num * first_contract.social_alw,
                    'social_deduction': f_day_abs_rate * first_contract.social_alw,
                    'car_allowance': f_c_days_num * first_contract.car_alw,
                    'car_deduction': f_day_abs_rate * first_contract.car_alw,
                    'supervision_allowance': f_c_days_num * first_contract.supervision_alw,
                    'supervision_deduction': f_day_abs_rate * first_contract.supervision_alw,
                    'eobs_allowance': f_c_days_num * first_contract.end_of_basic_salary_bonus,
                    'eobs_deduction': f_day_abs_rate * first_contract.end_of_basic_salary_bonus,
                    'monthly_incentive_allowance': f_c_days_num * first_contract.monthly_incentive,
                    'monthly_deduction': f_day_abs_rate * first_contract.monthly_incentive,
                    'representative_monthly_allowance': f_c_days_num * first_contract.representative_monthly_allowance,
                    'representative_deduction': f_day_abs_rate * first_contract.representative_monthly_allowance,
                    'work_condition_allowance': f_c_days_num * first_contract.work_condition_allowance,
                    'work_condition_deduction': f_day_abs_rate * first_contract.work_condition_allowance,

                    'basic_allowance_second': s_c_days_num * second_contract.wage,
                    'basic_deduction_second': s_day_abs_rate * second_contract.wage,
                    'mobile_allowance_second': s_c_days_num * second_contract.mobile_alw,
                    'mobile_deduction_second': s_day_abs_rate * second_contract.mobile_alw,
                    'housing_allowance_second': s_c_days_num * second_contract.housing_alw,
                    'housing_deduction_second': s_day_abs_rate * second_contract.housing_alw,
                    'other_allowance_second': s_c_days_num * second_contract.other_alw,
                    'other_deduction_second': s_day_abs_rate * second_contract.other_alw,
                    'transportation_allowance_second': s_c_days_num * second_contract.transport_alw,
                    'transportation_deduction_second': s_day_abs_rate * second_contract.transport_alw,
                    'social_allowance_second': s_c_days_num * second_contract.social_alw,
                    'social_deduction_second': s_day_abs_rate * second_contract.social_alw,
                    'car_allowance_second': s_c_days_num * second_contract.car_alw,
                    'car_deduction_second': s_day_abs_rate * second_contract.car_alw,
                    'supervision_allowance_second': s_c_days_num * second_contract.supervision_alw,
                    'supervision_deduction_second': s_day_abs_rate * second_contract.supervision_alw,
                    'eobs_allowance_second': s_day_abs_rate * second_contract.end_of_basic_salary_bonus,
                    'eobs_deduction_second': s_day_abs_rate * second_contract.end_of_basic_salary_bonus,
                    'monthly_incentive_allowance_second': s_day_abs_rate * second_contract.monthly_incentive,
                    'monthly_deduction_second': s_day_abs_rate * second_contract.monthly_incentive,
                    'representative_monthly_allowance_second': s_day_abs_rate * second_contract.representative_monthly_allowance,
                    'representative_deduction_second': s_day_abs_rate * second_contract.representative_monthly_allowance,
                    'work_condition_allowance_second': s_day_abs_rate * second_contract.work_condition_allowance,
                    'work_condition_deduction_second': s_day_abs_rate * second_contract.work_condition_allowance,

                    'basic_allowance_tot': f_c_days_num * first_contract.wage + s_c_days_num * second_contract.wage,
                    'basic_deduction_tot': f_day_abs_rate * first_contract.wage + s_day_abs_rate * second_contract.wage,
                    'mobile_allowance_tot': f_c_days_num * first_contract.mobile_alw + s_c_days_num * second_contract.mobile_alw,
                    'mobile_deduction_tot': f_day_abs_rate * first_contract.mobile_alw + s_day_abs_rate * second_contract.mobile_alw,
                    'housing_allowance_tot': f_c_days_num * first_contract.housing_alw + s_c_days_num * second_contract.housing_alw,
                    'housing_deduction_tot': f_day_abs_rate * first_contract.housing_alw + s_day_abs_rate * second_contract.housing_alw,
                    'other_allowance_tot': f_c_days_num * first_contract.other_alw + s_c_days_num * second_contract.other_alw,
                    'other_deduction_tot': f_day_abs_rate * first_contract.other_alw + s_day_abs_rate * second_contract.other_alw,
                    'transportation_allowance_tot': f_c_days_num * first_contract.transport_alw + s_c_days_num * second_contract.transport_alw,
                    'transportation_deduction_tot': f_day_abs_rate * first_contract.transport_alw + s_day_abs_rate * second_contract.transport_alw,
                    'social_allowance_tot': f_c_days_num * first_contract.social_alw + s_c_days_num * second_contract.social_alw,
                    'social_deduction_tot': f_day_abs_rate * first_contract.social_alw + s_day_abs_rate * second_contract.social_alw,
                    'car_allowance_tot': f_c_days_num * first_contract.car_alw + s_c_days_num * second_contract.car_alw,
                    'car_deduction_tot': f_day_abs_rate * first_contract.car_alw + s_day_abs_rate * second_contract.car_alw,
                    'supervision_allowance_tot': f_c_days_num * first_contract.supervision_alw + s_c_days_num * second_contract.supervision_alw,
                    'supervision_deduction_tot': f_day_abs_rate * first_contract.supervision_alw + s_day_abs_rate * second_contract.supervision_alw,
                    'eobs_allowance_tot': f_c_days_num * first_contract.end_of_basic_salary_bonus + s_c_days_num * second_contract.end_of_basic_salary_bonus,
                    'eobs_deduction_tot': f_day_abs_rate * first_contract.end_of_basic_salary_bonus + s_day_abs_rate * second_contract.end_of_basic_salary_bonus,
                    'monthly_incentive_allowance_tot': f_c_days_num * first_contract.monthly_incentive + s_c_days_num * second_contract.monthly_incentive,
                    'monthly_incentive_deduction_tot': f_day_abs_rate * first_contract.monthly_incentive + s_day_abs_rate * second_contract.monthly_incentive,
                    'representative_monthly_allowance_tot': f_c_days_num * first_contract.representative_monthly_allowance + s_c_days_num * second_contract.representative_monthly_allowance,
                    'representative_deduction_tot': f_day_abs_rate * first_contract.representative_monthly_allowance + s_day_abs_rate * second_contract.representative_monthly_allowance,
                    'work_condition_allowance_tot': f_c_days_num * first_contract.work_condition_allowance + s_c_days_num * second_contract.work_condition_allowance,
                    'work_condition_deduction_tot': f_day_abs_rate * first_contract.work_condition_allowance + s_day_abs_rate * second_contract.work_condition_allowance,

                    'basic_deduction_termination': termination_rate * second_contract.wage,
                    'other_deduction_termination': termination_rate * second_contract.other_alw,
                    'transportation_deduction_termination': termination_rate * second_contract.transport_alw,
                    'housing_deduction_termination': termination_rate * second_contract.housing_alw,
                    'mobile_deduction_termination': termination_rate * second_contract.mobile_alw,
                    'social_deduction_termination': termination_rate * second_contract.social_alw,
                    'car_deduction_termination': termination_rate * second_contract.car_alw,
                    'supervision_deduction_termination': termination_rate * second_contract.supervision_alw,
                    'eobs_deduction_termination': termination_rate * second_contract.end_of_basic_salary_bonus,
                    'monthly_incentive_deduction_termination': termination_rate * second_contract.monthly_incentive,
                    'representative_deduction_termination': termination_rate * second_contract.representative_monthly_allowance,
                    'work_condition_deduction_termination': termination_rate * second_contract.work_condition_allowance,
                })
            elif rec.contract_ids:
                contract = rec.contract_ids[0]
                all_absent_days = total_absence_days + total_termination_days
                day_rate = all_absent_days / 30
                res.update({
                    'basic_allowance_tot': contract.wage,
                    'basic_deduction_tot': day_rate * contract.wage,
                    'mobile_allowance_tot': contract.mobile_alw,
                    'mobile_deduction_tot': day_rate * contract.mobile_alw,
                    'housing_allowance_tot': contract.housing_alw,
                    'housing_deduction_tot': day_rate * contract.housing_alw,
                    'other_allowance_tot': contract.other_alw,
                    'other_deduction_tot': day_rate * contract.other_alw,
                    'transportation_allowance_tot': contract.transport_alw,
                    'transportation_deduction_tot': day_rate * contract.transport_alw,
                    'social_allowance_tot': contract.social_alw,
                    'social_deduction_tot': day_rate * contract.social_alw,
                    'car_allowance_tot': contract.car_alw,
                    'car_deduction_tot': day_rate * contract.car_alw,
                    'supervision_allowance_tot': contract.supervision_alw,
                    'supervision_deduction_tot': day_rate * contract.supervision_alw,
                    'eobs_allowance_tot': contract.end_of_basic_salary_bonus,
                    'eobs_deduction_tot': day_rate * contract.end_of_basic_salary_bonus,
                    'monthly_incentive_allowance_tot': contract.monthly_incentive,
                    'monthly_incentive_deduction_tot': day_rate * contract.monthly_incentive,
                    'representative_monthly_allowance_tot': contract.representative_monthly_allowance,
                    'representative_deduction_tot': day_rate * contract.representative_monthly_allowance,
                    'work_condition_allowance_tot': contract.work_condition_allowance,
                    'work_condition_deduction_tot': day_rate * contract.work_condition_allowance,

                    'basic_deduction_termination': termination_rate * contract.wage,
                    'other_deduction_termination': termination_rate * contract.other_alw,
                    'transportation_deduction_termination': termination_rate * contract.transport_alw,
                    'housing_deduction_termination': termination_rate * contract.housing_alw,
                    'mobile_deduction_termination': termination_rate * contract.mobile_alw,
                    'social_deduction_termination': termination_rate * contract.social_alw,
                    'car_deduction_termination': termination_rate * contract.car_alw,
                    'supervision_deduction_termination': termination_rate * contract.supervision_alw,
                    'eobs_deduction_termination': termination_rate * contract.end_of_basic_salary_bonus,
                    'monthly_incentive_deduction_termination': termination_rate * contract.monthly_incentive,
                    'representative_deduction_termination': termination_rate * contract.representative_monthly_allowance,
                    'work_condition_deduction_termination': termination_rate * contract.work_condition_allowance,

                })
            return res

    def _check_off_employee(self, employee, day):
        off = False
        for record in self:
            contracts = self.env['hr.contract'].search([
                ('employee_id', '=', employee.id),
                ('state', 'in', ['open', 'probation', 'close'])
            ], order='date_end desc')
            if contracts:
                if day > contracts[-1].date_end:
                    off = True
            return off

    def get_attendances(self):
        for rec in self:
            for att_sheet in self:
                att_sheet.att_sheet_line_ids.unlink()
            att_line = rec.env["attendance.sheet.line"]
            latest_contract = rec.contract_ids.sorted(lambda x: x.date_start)[-1]
            work_days = rec.get_working_days_of_the_week()
            sheet_status = rec.prepare_sheet_lines(latest_contract, work_days)
            days, day_status_dict, unpaid_leaves, attendances, legal_leaves = sheet_status
            result = []
            absence_days = []
            data = {}
            total_absence_days = 0
            total_termination_days = 0
            for day in days:
                day_str = str(day.weekday())
                status = day_status_dict.get(f'{day}')
                if status and (day_str in work_days or status[0] == ''):
                    if status[0] == '':
                        attend_day = attendances.filtered(lambda x: x.check_in.date() == day)
                        total_hours=0
                        for attend in attend_day:
                            total_hours += attend.worked_hours
                        result.append({
                            'date': day,
                            'day': day_str,
                            'ac_sign_in': _get_float_from_time(attend_day[0].check_in),
                            'ac_sign_out': _get_float_from_time(attend_day[-1].check_out) if status[1].check_out else 0,
                            'worked_hours': total_hours,
                            'att_sheet_id': rec.id,
                            'display_attendance': True,
                            'status_char': status[0]
                        })
                    else:
                        if status[0] != 'Public Holiday' and status[0].is_unpaid:
                            total_absence_days += 1
                        result.append({
                            'date': day,
                            'day': day_str,
                            'att_sheet_id': rec.id,
                            'status_char': status[0] if status[0] == 'Public Holiday' else status[0].name,
                            'leave_type_id': False if status[0] == 'Public Holiday' else status[0].id,
                        })
                else:
                    if latest_contract.date_end and day > latest_contract.date_end:
                        total_termination_days += 1
                        result.append({'date': day, 'day': day_str, 'att_sheet_id': rec.id, 'status_char': 'End Contract'})
                    else:
                        if day_str not in work_days and status and type(status[0]) != str and status[0].is_unpaid:
                            total_absence_days += 1
                            result.append(
                                {'date': day, 'day': day_str, 'att_sheet_id': rec.id, 'status_char': status[0].name, 'leave_type_id': status[0].id})
                        elif day_str not in work_days:
                            result.append({'date': day, 'day': day_str, 'att_sheet_id': rec.id, 'status_char': 'Weekend'})

                        else:
                            absence_days.append((day, day_str))
            total_absence_days += rec.check_absence_days_status(absence_days, result)
            att_line.create(result)
            total_absence_days = rec.check_absent_days_number(total_absence_days)
            allowance_deductions = rec.get_salary_allowances_and_deductions(total_absence_days, total_termination_days)
            # leave_settlements = rec.get_leave_advance_settlement()
            new_joiner_calculations = rec.check_if_is_new_joiner()
            rec.write({'total_num_of_abscence_days': total_absence_days,
                       'total_termination_days': total_termination_days})
            if allowance_deductions:
                data.update(allowance_deductions)
            if new_joiner_calculations:
                data.update(new_joiner_calculations)
            if data:
                rec.write(data)

    def check_absent_days_number(self, total_absence_days):
        return min(total_absence_days, 30)

    def action_payslip(self):
        self.ensure_one()

        payslip_id = self.payslip_id
        if not payslip_id:
            payslip_id = self.action_create_payslip()[0]
        return {'type': 'ir.actions.act_window', 'res_model': 'hr.payslip', 'view_mode': 'form', 'view_type': 'form',
                'res_id': payslip_id.id, 'views': [(False, 'form')], }

    def _compute_lines_count(self):
        for rec in self:
            rec.lines_count = len(rec.att_sheet_line_ids)

    def action_open_attendance_sheet_lines(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "attendance.sheet.line",
            "view_mode": "tree",
            "domain": [['id', 'in', self.att_sheet_line_ids.ids]],
            "name": "Lines",
        }
