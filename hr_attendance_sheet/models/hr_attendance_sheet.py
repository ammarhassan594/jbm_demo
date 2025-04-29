import time
import datetime
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from odoo import models, fields, tools, api, exceptions, _
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.tools.date_utils import end_of
import babel

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TIME_FORMAT = "%H:%M:%S"


def float_to_time(float_type):
    str_off_time = str(float_type)
    official_hour = str_off_time.split('.')[0]
    official_minute = (
            "%2d" % int(
        str(float("0." + str_off_time.split('.')[1]) * 60).split('.')[
            0])).replace(
        ' ', '0')
    str_off_time = official_hour + ":" + official_minute
    str_off_time = datetime.strptime(str_off_time, "%H:%M").time()
    return str_off_time


def _get_float_from_time(time):
    time_type = datetime.strftime(time + timedelta(hours=3), "%H:%M")
    signOnP = [int(n) for n in time_type.split(":")]
    signOnH = signOnP[0] + signOnP[1] / 60.0
    return signOnH


class hr_public_holiday(models.Model):
    _name = "hr.public.holiday"
    _description = "hr.public.holiday"

    name = fields.Char(string="Reason")
    date_from = fields.Date(string="From")
    date_to = fields.Date(string="To")
    state = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Not Active')], default='inactive',
        string='Status', required=True, index=True, )
    note = fields.Text("Notes")


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

    overtime_request_ids = fields.One2many(comodel_name="hr.overtime", inverse_name="attendance_sheet_ids",
                                           string="Overtime",
                                           domain="[('employee_id', '=', 'employee_id')]")

    leave_ids = fields.One2many(comodel_name="hr.leave", inverse_name="attendance_sheet_id")

    employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee', required=True)
    employee_number = fields.Char(related='employee_id.registration_number', string='Employee Number')
    department_id = fields.Many2one(related='employee_id.department_id', store=True)
    date_from = fields.Date(string="From", required=True, default=time.strftime('%Y-%m-01'))
    date_to = fields.Date(string="To", required=True,
                          default=str(datetime.now() + relativedelta(months=+1, day=1, days=-1))[:10])
    att_sheet_line_ids = fields.One2many(comodel_name='attendance.sheet.line', string='Attendances', readonly=True,
                                         inverse_name='att_sheet_id')
    project_id = fields.Many2one(
        'project.project',
        string='Project'
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('done', 'Approved')], default='draft',
        string='Status', required=True, readonly=True, index=True,
        help=' * The \'Draft\' status is used when a HR user is creating a new  attendance sheet. '
             '\n* The \'Confirmed\' status is used when  attendance sheet is confirmed by HR user.'
             '\n* The \'Approved\' status is used when  attendance sheet is accepted by the HR Manager.')
    payslip_id = fields.Many2one(comodel_name='hr.payslip', string='PaySlip', copy=False)

    total_late_in = fields.Float("Total Late", default=0.0)

    total_num_of_abscence_days = fields.Float("Abscence Days", default=0)

    accommodation_late = fields.Monetary('Accommodation', default=0.0)

    mobile_allowance_late = fields.Monetary('Mobile Allowance', default=0.0)

    food_allowance_late = fields.Monetary('Food Allowance',
                                          default=0.0)
    site_allowance_late = fields.Monetary('Site Allowance', default=0.0)

    transport_allowance_late = fields.Monetary('Transport Allowance', default=0.0)
    other_allowance_late = fields.Monetary('Other Allowance', default=0.0)

    fixed_overtime_allowance_late = fields.Monetary('Fixed Overtime Allowance', default=0.0)

    project_has_food_allowance = fields.Integer(default=0)

    accommodation_half_paid = fields.Monetary(default=0.0)
    mobile_half_paid = fields.Monetary(default=0.0)
    site_half_paid = fields.Monetary(default=0.0)
    transport_half_paid = fields.Monetary(default=0.0)
    other_half_paid = fields.Monetary(default=0.0)
    uniform_half_paid = fields.Monetary(default=0.0)
    social_half_paid = fields.Monetary(default=0.0)
    wage_half_paid = fields.Monetary('Basic Salary', default=0.0, )

    accommodation_unpaid = fields.Monetary(default=0.0)
    mobile_unpaid = fields.Monetary(default=0.0)
    site_unpaid = fields.Monetary(default=0.0)
    transport_unpaid = fields.Monetary(default=0.0)
    other_unpaid = fields.Monetary(default=0.0)
    uniform_unpaid = fields.Monetary(default=0.0)
    social_unpaid = fields.Monetary(default=0.0)
    wage_unpaid = fields.Monetary('Basic Salary', default=0.0, )

    n_half_p_days = fields.Integer("Half Paid Days", default=0)
    n_unpaid_days = fields.Integer("UnPaid Days", default=0)

    num_of_leave_days = fields.Integer("Leave Days", default=0)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)

    # leave advance salary
    has_leave = fields.Boolean(default=False)
    in_leave = fields.Boolean(default=False)

    # Leave Advance Allowance
    leave_advance_wage = fields.Monetary()
    leave_advance_accommodation = fields.Monetary()
    leave_advance_mobile_allowance = fields.Monetary()
    leave_advance_food_allowance = fields.Monetary()
    leave_advance_site_allowance = fields.Monetary()
    leave_advance_transport_allowance = fields.Monetary()
    leave_advance_other_allowance = fields.Monetary()
    leave_advance_uniform_allowance = fields.Monetary()
    leave_advance_social_allowance = fields.Monetary()

    # Leave Advance Deduction
    leave_advance_wage_ded = fields.Monetary()
    leave_advance_accommodation_ded = fields.Monetary()
    leave_advance_mobile_ded = fields.Monetary()
    leave_advance_food_ded = fields.Monetary()
    leave_advance_site_ded = fields.Monetary()
    leave_advance_transport_ded = fields.Monetary()
    leave_advance_other_ded = fields.Monetary()
    leave_advance_uniform_ded = fields.Monetary()
    leave_advance_social_ded = fields.Monetary()
    advance_leave_count_days = fields.Monetary()
    return_from_leave_days = fields.Monetary()
    food_deduction = fields.Monetary()

    pension_employee = fields.Monetary()
    pension_employer = fields.Monetary()
    social_allowance = fields.Monetary()
    laundry_allowance = fields.Monetary()
    furniture_allowance = fields.Monetary()
    amount_l_un_cut = fields.Monetary()
    note = fields.Text("Notes", readonly=True, default='')
    actual_date_from = fields.Date(string="Actual Date From", compute="compute_actual_date", store=True)
    actual_date_to = fields.Date(string="Actual Date To", store=True)

    @api.depends('date_to', 'date_from')
    def compute_actual_date(self):
        for rec in self:
            date_from = False
            date_to = False
            if rec.date_from or rec.date_to:
                date_from = rec.date_from
                date_to = rec.date_to
            rec.actual_date_to = date_to
            rec.actual_date_from = date_from

    def create_overtime_request(self):
        for rec in self:
            for line in rec.att_sheet_line_ids:
                if line.project_id:
                    rec.project_id = line.project_id.id
                    break
            special_ot = 0
            normal_ot = 0
            overtime_cutoff_day = int(
                rec.env['ir.config_parameter'].sudo().get_param('ohrms_overtime.overtime_cutoff_day'))
            month = int(rec.date_from.strftime('%m'))
            year = int(rec.date_from.strftime('%Y'))

            # if month is January, we edit the month and the year values
            if month == 1:
                month = 13
                year = year - 1

            overtime_cutoff_from = rec.date_from.replace(year=year, month=month - 1, day=overtime_cutoff_day)
            overtime_cutoff_to = rec.date_from.replace(day=overtime_cutoff_day - 1)

            rec.overtime_allowance = 0
            attendances = rec.env["hr.attendance"].search([('employee_id', '=', self.employee_id.id),
                                                           ('day_from', '<=', overtime_cutoff_to),
                                                           ('day_from', '>=', overtime_cutoff_from)])
            overtime_lines = []
            for line in attendances:
                if line.overtime_hours:
                    overtime_lines.append((0, 0, {
                        'employee_id': rec.employee_id.id,
                        'date': line.day_from,
                        'overtime_type': 'normal',
                        'hours': line.overtime_hours,
                        # 'project': line.project_id.id,
                        'paid': True,
                    }))
                    normal_ot += line.overtime_hours
                if line.special_overtime:
                    overtime_lines.append((0, 0, {
                        'employee_id': rec.employee_id.id,
                        'date': line.day_from,
                        'overtime_type': 'special',
                        'hours': line.special_overtime,
                        # 'project': line.project_id.id,
                        'paid': True,
                    }))
                    special_ot += line.special_overtime

            # lines = self.env['hr.overtime.line'].create(overtime_lines)
            overtime = rec.env['hr.overtime']
            # self.overtime_request_ids = [(5, 0, {})]

            # .filtered(
            # lambda x: overtime_cutoff_from <= x.day_from <= overtime_cutoff_to)
            # special_ot = sum(attendances.mapped('special_overtime'))
            # normal_ot = sum(attendances.mapped('overtime_hours'))
            total_hours = normal_ot + special_ot
            if total_hours:
                overtime.create({
                    'employee_id': rec.employee_id.id,
                    'type': 'cash',
                    'duration_type': 'hours',
                    # 'overtime_date': line.date,
                    'date_from': rec.date_from,
                    'date_to': rec.date_to,
                    'actual_date_from': rec.actual_date_from,
                    'actual_date_to': rec.actual_date_to,
                    'state': 'approved',
                    # 'overtime_types': 'no',
                    'overtime_lines': overtime_lines,
                    # 'days_no_tmp': total_hours,
                    'project_id': rec.project_id.id,
                    'attendance_sheet_ids': rec.id,
                    'ot_remarks': f'Total {normal_ot} NO-Overtime & {special_ot} SP-Overtime'
                })

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
            if joining_date and joining_date <= rec.date_from:
                return [(rec.date_from + timedelta(days=x)) for x in range((rec.date_to - rec.date_from).days + 1)]
            else:
                return [(joining_date + timedelta(days=x)) for x in range((rec.date_to - joining_date).days + 1)]

    def get_leave_days(self, leaves):
        for rec in self:
            legal_days = []
            unpaid_leaves = []
            illegal_leaves = []
            legal_permissions = []
            for leave in leaves:
                from_date = leave.date_from.date()
                to_date = leave.date_to.date()
                if leave.holiday_status_id.is_unpaid:
                    unpaid_leaves += [(from_date + timedelta(days=x)) for x in
                                      range((to_date - from_date).days + 1)
                                      if rec.date_from <= (from_date + timedelta(days=x)) <= rec.date_to]
                elif leave.holiday_status_id.legal:
                    legal_days += [(from_date + timedelta(days=x)) for x in
                                   range((to_date - from_date).days + 1)
                                   if rec.date_from <= (from_date + timedelta(days=x)) <= rec.date_to]
                elif not leave.holiday_status_id.legal:
                    if leave.holiday_status_id.is_permission:
                        permission = leave.holiday_status_id.permission_config_ids.filtered(
                            lambda x: x.permission_leave_type == leave.permission_leave_type)
                        if permission and permission.is_attendance:
                            legal_permissions += [(from_date + timedelta(days=x)) for x in
                                                  range((to_date - from_date).days + 1)
                                                  if rec.date_from <= (from_date + timedelta(days=x)) <= rec.date_to]
                        else:
                            illegal_leaves += [(from_date + timedelta(days=x)) for x in
                                               range((to_date - from_date).days + 1)
                                               if rec.date_from <= (from_date + timedelta(days=x)) <= rec.date_to]
                    else:
                        illegal_leaves += [(from_date + timedelta(days=x)) for x in
                                           range((to_date - from_date).days + 1)
                                           if rec.date_from <= (from_date + timedelta(days=x)) <= rec.date_to]

            return legal_days, unpaid_leaves, illegal_leaves, legal_permissions

    def get_employee_leaves(self):
        for rec in self:
            leaves = rec.env['hr.leave'].search(
                [('employee_id', '=', rec.employee_id.id), ('request_date_from', '<=', rec.date_to),
                 ('request_date_to', '>=', rec.date_from), ('state', '=', 'validate')])
            return rec.get_leave_days(leaves)

    def get_public_holidays(self):
        for rec in self:
            public_holidays = []
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
            balance = rec.env['hr.leave.allocation'].search([('employee_id', '=', rec.employee_id.id),
                                                             ('holiday_status_id.is_annual', '=', True),
                                                             ('state', '=', 'validate')])
            n_of_allocations = sum(balance.mapped('number_of_days'))
            leaves_taken = sum(rec.env['hr.leave'].search([('employee_id', '=', rec.employee_id.id),
                                                           ('holiday_status_id.is_annual', '=', True),
                                                           ('state', '=', 'validate')]).mapped('number_of_days'))
            remaining_leaves = n_of_allocations - leaves_taken
            return remaining_leaves

    def get_december_leave_balance(self):
        for rec in self:
            allocation = sum(rec.env['hr.leave.allocation'].search([('employee_id', '=', rec.employee_id.id),
                                                                    ('holiday_status_id.is_annual', '=', True),
                                                                    ('state', '=', 'validate'),
                                                                    ('year', '=', rec.date_from.year)]).mapped(
                'number_of_days'))
            leaves = self.env['hr.leave'].search([('employee_id', '=', rec.employee_id.id),
                                                  ('holiday_status_id.is_annual', '=', True),
                                                  ('state', '=', 'validate')])
            leaves_taken = sum(leaves.mapped('number_of_days'))
            jan_leaves = sum(
                leaves.filtered(lambda x: x.date_from.date() >= rec.date_to.replace(day=1)).mapped('number_of_days'))
            dec_balance = allocation - leaves_taken + jan_leaves
            return dec_balance

            # allocation_num = rec.env['hr.leave.allocation'].search([('employee_id', '=', rec.employee_id.id),
            #                                                     ('holiday_status_id.is_annual', '=', True),
            #                                                     ('state', '=', 'validate')])
            #
            # allocation_no_days = sum(rec.env['hr.leave.allocation'].search([('employee_id', '=', rec.employee_id.id),
            #                                                                 ('holiday_status_id.is_annual', '=', True),
            #                                                                 ('state', '=', 'validate'),
            #                                                                 ('year', '=', rec.date_to.year)]).mapped(
            #     'number_of_days'))

            # tot_balance = allocation.max_leaves - allocation.leaves_taken
            # if dec_balance < 0
            # jan_leaves = sum(rec.env['hr.leave'].search([('employee_id', '=', rec.employee_id.id),
            #                                              ('holiday_status_id.is_annual', '=', True),
            #                                              ('date_from', '>=', rec.date_to.replace(day=1)),
            #                                              ('state', '=', 'validate')]).mapped('number_of_days'))

            # dec_balance = tot_balance - allocation.number_of_days + jan_leaves
            # print(dec_balance)
            # dec_balance = allocation.max_leaves - allocation_no_days - allocation.leaves_taken + jan_leaves
            # print('dec_balance',rec.employee_number, dec_balance, allocation, leaves_taken,  'jan_leaves', jan_leaves,allocation_no_days, sum(allocation_num.mapped(
            #     'number_of_days')))

    def _get_sick_leave_calculations(self):
        for rec in self:
            days = []
            half_paid_days = []
            unpaid_days = []
            leaves = rec.env['hr.leave'].search(
                [('employee_id', '=', rec.employee_id.id), ('date_from', '<=', rec.date_to),
                 ('date_to', '>=', rec.date_from), ('state', '=', 'validate'),
                 ('holiday_status_id.is_leave_deduction', '=', True), ('holiday_status_id.legal', '=', True)])
            if leaves:
                work_days = rec.get_working_days_of_the_week()
                if rec.employee_type == 'perm_staff':
                    for leave in leaves:
                        days += [leave.date_from.date() + timedelta(days=x) for x in
                                 range((leave.date_to.date() - leave.date_from.date()).days + 1) if
                                 str((leave.date_from.date() + timedelta(days=x)).weekday()) in work_days and (
                                         leave.date_from.date() + timedelta(days=x)).year == rec.actual_date_from.year]
                    number_of_days = len(days)
                    leave_type_id = rec.env['hr.leave.type'].search([('id', '=', leaves[0].holiday_status_id.id)])
                    if rec.employee_id.country_id.code == 'QA':
                        if number_of_days > leave_type_id.qatari_leave_end:
                            start_date_index = rec.date_from in days and days.index(rec.date_from) or 0
                            if start_date_index > (leave_type_id.qatari_leave_end - 1):
                                if days[-1] <= rec.date_to:
                                    half_paid_days += days[start_date_index:]
                                else:
                                    half_paid_days += days[start_date_index:days.index(rec.date_to) + 1]
                            else:
                                half_paid_days += days[start_date_index:leave_type_id.qatari_leave_end]
                                if days[-1] <= rec.date_to:
                                    half_paid_days += days[leave_type_id.qatari_leave_end:]
                                else:
                                    end_date_index = days.index(rec.date_to)
                                    half_paid_days += days[leave_type_id.qatari_leave_end:end_date_index + 1]

                    else:
                        if leave_type_id.expait_leave_start <= number_of_days <= leave_type_id.expait_leave_end:
                            if rec.date_from <= days[-1] and days[0] <= rec.date_to:
                                # start_date_index = self.date_from in days and days.index(self.date_from) or 0
                                if days[-1] <= rec.date_to:
                                    half_paid_days += days[leave_type_id.expait_leave_start:]
                                else:
                                    half_paid_days += days[leave_type_id.expait_leave_start:days.index(rec.date_to) + 1]

                        elif number_of_days > leave_type_id.expait_leave_end:
                            start_date_index = rec.date_from in days and days.index(rec.date_from) or 0
                            if start_date_index > (leave_type_id.expait_leave_end - 1):
                                if days[-1] <= rec.date_to:
                                    unpaid_days += days[start_date_index:]
                                else:
                                    end_date_index = days.index(rec.date_to)
                                    unpaid_days += days[start_date_index:end_date_index + 1]
                            else:
                                half_paid_days += days[start_date_index:leave_type_id.expait_leave_end]
                                if days[-1] <= rec.date_to:
                                    unpaid_days += days[leave_type_id.expait_leave_end:]
                                else:
                                    end_date_index = days.index(self.date_to)
                                    unpaid_days += days[leave_type_id.expait_leave_end:end_date_index + 1]

                elif rec.employee_type == 'perm_in_house':
                    for leave in leaves:
                        days += [leave.date_from.date() + timedelta(days=x) for x in
                                 range((leave.date_to.date() - leave.date_from.date()).days + 1) if
                                 str((leave.date_from.date() + timedelta(days=x)).weekday()) in work_days and (
                                         leave.date_from.date() + timedelta(
                                     days=x)).year == rec.actual_date_from.year and
                                 (leave.date_from.date() + timedelta(days=x)) <= rec.date_to]

                    number_of_days = len(days)
                    leave_type_id = rec.env['hr.leave.type'].search([('id', '=', leaves[0].holiday_status_id.id)])
                    if leave_type_id.inhouse_leave_start <= number_of_days <= leave_type_id.inhouse_leave_end:
                        if rec.date_from <= days[-1] and days[0] <= rec.date_to:
                            # start_date_index = self.date_from in days and days.index(self.date_from) or 0)
                            if days[-1] <= rec.date_to:
                                half_paid_days += days[leave_type_id.inhouse_leave_start:]
                            else:
                                end_date_index = days.index(rec.date_to)
                                half_paid_days += days[leave_type_id.inhouse_leave_start:end_date_index]

                    elif number_of_days > leave_type_id.inhouse_leave_end:

                        if rec.date_from <= days[-1] and days[0] <= rec.date_to:
                            start_date_index = rec.date_from in days and days.index(rec.date_from) or 0
                            if start_date_index > (leave_type_id.inhouse_leave_end - 1):
                                if days[-1] <= rec.date_to:
                                    unpaid_days += days[start_date_index:]
                                else:
                                    end_date_index = days.index(rec.date_to)
                                    unpaid_days += days[start_date_index:end_date_index + 1]
                            else:
                                half_paid_days += days[start_date_index:leave_type_id.inhouse_leave_end]
                                if days[-1] <= rec.date_to:
                                    unpaid_days += days[leave_type_id.inhouse_leave_end:]
                                else:
                                    end_date_index = days.index(rec.date_to)
                                    unpaid_days += days[leave_type_id.inhouse_leave_end:end_date_index + 1]

            return half_paid_days, unpaid_days

    def prepare_sheet_lines(self):
        for rec in self:
            sheet_days = rec._get_days_since_joining_days()
            day_status = {}
            attendance = rec.env["hr.attendance"].search([('employee_id', '=', rec.employee_id.id),
                                                          ('day_from', '>=', sheet_days[0]),
                                                          ('day_from', '<=', sheet_days[-1])], order='id')
            # attendance_days = set(attendance.mapped('day_from'))
            public_holidays = rec.get_public_holidays()
            leaves = rec.get_employee_leaves()
            legal_leaves = leaves[0]
            unpaid_leaves = leaves[1]
            illegal_leaves = leaves[2]
            legal_permissions = leaves[3]
            sick_leaves = rec._get_sick_leave_calculations()
            s_l_half_paid = sick_leaves[0]
            s_l_unpaid = sick_leaves[1]
            for attend in attendance:
                day_status.update({f'{attend.day_from}': ('a', attend)})
            for day in public_holidays:
                if not day_status.get(f'{day}'):
                    day_status.update({f'{day}': ('ph', day)})
            for day in s_l_half_paid:
                if not day_status.get(f'{day}'):
                    day_status.update({f'{day}': ('half_paid', day)})
            for day in s_l_unpaid:
                if not day_status.get(f'{day}'):
                    day_status.update({f'{day}': ('unpaid', day)})
            for day in legal_leaves:
                if not day_status.get(f'{day}'):
                    day_status.update({f'{day}': ('leave', day)})
            for day in unpaid_leaves:
                if not day_status.get(f'{day}'):
                    day_status.update({f'{day}': ('unpaid_leave', day)})
            for day in legal_permissions:
                if not day_status.get(f'{day}'):
                    day_status.update({f'{day}': ('legal_permission', day)})
            for day in illegal_leaves:
                if not day_status.get(f'{day}'):
                    day_status.update({f'{day}': ('illegal', day)})
            return sheet_days, day_status, unpaid_leaves, attendance, legal_leaves

    def check_weekend_status(self, day, day_str, unpaid_leaves, day_status_dict):
        for rec in self:
            absent = 0
            # if any((rec.employee_type == 'perm_staff', not unpaid_leaves, day <= unpaid_leaves[0], unpaid_leaves[-1] <= day)):
            if rec.employee_type == 'perm_staff' or not unpaid_leaves or day <= unpaid_leaves[0] or unpaid_leaves[
                -1] <= day:
                return {'date': day, 'day': day_str, 'att_sheet_id': rec.id, 'status': 'weekend'}, absent
            else:
                # if day_status_dict.get(f'{day}'):
                day_before = day + relativedelta(days=-1)
                day_after = day + relativedelta(days=1)
                day_before_st = day_status_dict.get(f'{day_before}')
                day_after_st = day_status_dict.get(f'{day_after}')
                if (day_before_st and day_before_st[0] == 'a') or (day_after_st and day_after_st[0] == 'a'):
                    return {'date': day, 'day': day_str, 'att_sheet_id': rec.id, 'status': 'weekend'}, absent
                else:
                    absent += 1
                    return {'date': day, 'day': day_str, 'att_sheet_id': rec.id, 'status': 'unpaid_leave'}, absent

    def check_absence_days_status(self, absence_days, result):
        return 0
        # for rec in self:
        #     total_absence_days = 0
        #     r_leave_balance = rec._get_employee_leave_balance()
        #     new_leaves = []
        #     consecutive_days = []
        #     res = []
        #     if rec.actual_date_from.month == 1 and rec.employee_type == 'perm_staff':
        #         dec_balance = rec.get_december_leave_balance()
        #         # dec_abs_days = [day for day in absence_days if day < rec.actual_date_from]
        #         for day in absence_days:
        #             if day[0] < rec.actual_date_from and dec_balance >= 1:
        #                 dec_balance -= 1
        #                 new_leaves.append(day)
        #             elif r_leave_balance >= 1 and day[0] >= rec.actual_date_from:
        #                 r_leave_balance -= 1
        #                 new_leaves.append(day)
        #             else:
        #                 total_absence_days += 1
        #                 result.append({'date': day[0], 'day': day[1], 'att_sheet_id': rec.id, 'status': 'ab'})
        #     else:
        #         for day in absence_days:
        #             if r_leave_balance >= 1:
        #                 r_leave_balance -= 1
        #                 new_leaves.append(day)
        #             else:
        #                 total_absence_days += 1
        #                 result.append({'date': day[0], 'day': day[1], 'att_sheet_id': rec.id, 'status': 'ab'})
        #     if new_leaves:
        #         leave_type = rec.env['hr.leave.type'].search([('is_annual', '=', True)],
        #                                                      limit=1)
        #         consecutive_days.append(new_leaves[0][0])
        #         result.append({'date': new_leaves[0][0], 'day': new_leaves[0][1], 'att_sheet_id': rec.id,
        #                        'status': 'leave'})
        #         for i in range(1, len(new_leaves)):
        #             result.append({'date': new_leaves[i][0], 'day': new_leaves[i][1], 'att_sheet_id': rec.id,
        #                            'status': 'leave'})
        #             if new_leaves[i][0] + relativedelta(days=-1) == new_leaves[i - 1][0]:
        #                 consecutive_days.append(new_leaves[i][0])
        #             else:
        #                 res.append({
        #                     'employee_id': rec.employee_id.id,
        #                     'holiday_status_id': leave_type.id,
        #                     'request_date_from': consecutive_days[0],
        #                     'request_date_to': consecutive_days[-1],
        #                     'date_from': datetime(consecutive_days[0].year, consecutive_days[0].month,
        #                                           consecutive_days[0].day, 10, 0, 0),
        #                     'date_to': datetime(consecutive_days[-1].year, consecutive_days[-1].month,
        #                                         consecutive_days[-1].day, 20, 0, 0),
        #                     'state': 'draft',
        #                     'number_of_days': 1,
        #                     'approved_automatic': True,
        #                     'attendance_sheet_id': rec.id
        #                 })
        #                 consecutive_days = [new_leaves[i][0]]
        #         if consecutive_days:
        #             res.append({'employee_id': rec.employee_id.id,
        #                         'holiday_status_id': leave_type.id,
        #                         'request_date_from': consecutive_days[0],
        #                         'request_date_to': consecutive_days[-1],
        #                         'date_from': datetime(consecutive_days[0].year, consecutive_days[0].month,
        #                                               consecutive_days[0].day, 8, 0, 0),
        #                         'date_to': datetime(consecutive_days[-1].year, consecutive_days[-1].month,
        #                                             consecutive_days[-1].day, 8, 0, 0),
        #                         'state': 'draft',
        #                         'approved_automatic': True,
        #                         'attendance_sheet_id': rec.id})
        #         leaves = rec.env['hr.leave'].with_context(from_attendance_sheet=True).create(res)
        #         leaves.write({'state': 'validate'})
        #     return total_absence_days

    def get_attendances(self):
        for rec in self:
            for att_sheet in self:
                att_sheet.att_sheet_line_ids.unlink()
            att_line = rec.env["attendance.sheet.line"]
            work_days = rec.get_working_days_of_the_week()
            sheet_status = rec.prepare_sheet_lines()
            days = sheet_status[0]
            day_status_dict = sheet_status[1]
            unpaid_leaves = sheet_status[2]
            attendance = sheet_status[3]
            legal_leaves = sheet_status[4]
            result = []
            absence_days = []
            data = {}
            total_absence_days = s_h_paid_days = s_u_days = 0
            if all((not attendance, not legal_leaves)):
                lines = []
                for day in days:
                    day_str = str(day.weekday())
                    values = {
                        'date': day,
                        'day': day_str,
                        'att_sheet_id': rec.id,
                        'status': 'ab',
                        'att_status': '',
                        'note': ''
                    }
                    lines.append(values)
                if rec.employee_id.wassef_employee_type == 'perm_staff':
                    total_absence_days += 21.75
                else:
                    total_absence_days += 30
                att_line.create(lines)
            else:
                for day in days:
                    day_str = str(day.weekday())
                    status = day_status_dict.get(f'{day}')
                    if status and (day_str in work_days or status[0] == 'a'):
                        if status[0] == 'a':
                            result.append({
                                'date': day,
                                'day': day_str,
                                'overtime': status[1].overtime_hours,
                                'special_overtime': status[1].special_overtime,
                                'ac_sign_in': _get_float_from_time(status[1].check_in),
                                'ac_sign_out': _get_float_from_time(status[1].check_out),
                                'worked_hours': status[1].worked_hours,
                                'project_id': status[1].project_id.id,
                                'att_sheet_id': rec.id,
                            })
                        else:
                            if status[0] == 'half_paid':
                                s_h_paid_days += 1
                            elif status[0] == 'unpaid':
                                s_u_days += 1
                            elif status[0] == 'unpaid_leave' or status[0] == 'illegal':
                                total_absence_days += 1
                            result.append({
                                'date': day,
                                'day': day_str,
                                'att_sheet_id': rec.id,
                                'status': status[0],
                            })
                    else:
                        if day_str not in work_days:
                            check_weekend = rec.check_weekend_status(day, day_str, unpaid_leaves, day_status_dict)
                            result.append(check_weekend[0])
                            total_absence_days += check_weekend[1]
                        else:
                            absence_days.append((day, day_str))

                total_absence_days += rec.check_absence_days_status(absence_days, result)
                att_line.create(result)
                total_absence_days, s_h_paid_days, s_u_days = rec.check_absent_half_unpaid_days_number(
                    total_absence_days,
                    s_h_paid_days,
                    s_u_days)
            allowance_deductions = rec.get_salary_allowances_and_deductions(total_absence_days, s_h_paid_days, s_u_days)
            leave_settlements = rec.get_leave_advance_settlement()
            new_joiner_calculations = rec.check_if_is_new_joiner()
            rec.write({'total_num_of_abscence_days': total_absence_days})
            if allowance_deductions:
                data.update(allowance_deductions)
            if leave_settlements:
                data.update(leave_settlements)
            if new_joiner_calculations:
                data.update(new_joiner_calculations)
            if data:
                rec.write(data)
            # rec.get_leave_advance_settlement()
            # rec.check_if_is_new_joiner()
            rec.create_overtime_request()

    def check_if_is_new_joiner(self):
        for rec in self:
            joining_date = rec.employee_id.joining_date
            date_from = rec.date_from
            date_to = rec.date_to
            c_m_remaining_d = 0
            r_d_from_p_month = 0
            if date_from < joining_date <= date_to:
                if rec.actual_date_from <= joining_date <= date_to:
                    if rec.employee_type == 'perm_staff':
                        c_m_remaining_d += rec.contract_id.resource_calendar_id.get_working_days(date_from,
                                                                                                 joining_date)
                    else:
                        c_m_remaining_d += joining_date.day - 1
                else:
                    last_day = rec.actual_date_from + relativedelta(days=-1)
                    if rec.employee_type == 'perm_staff':
                        r_d_from_p_month += rec.contract_id.resource_calendar_id.get_working_days(joining_date,
                                                                                                  last_day)
                    else:
                        r_d_from_p_month += (last_day - joining_date).days + 1
            return rec.get_new_joiners_salary_settlements(c_m_remaining_d, r_d_from_p_month)

    def get_new_joiners_salary_settlements(self, c_m_remaining_d, r_d_from_p_month):
        for rec in self:
            res = {}
            if r_d_from_p_month:
                if rec.employee_type == 'perm_staff':
                    res.update({'earning_allowance': rec.contract_id.gross_salary / 21.75 * r_d_from_p_month})
                    # print('r_d_from_p_month', r_d_from_p_month, res)
                else:
                    res.update({'earning_allowance': rec.contract_id.gross_salary / 30 * r_d_from_p_month})

            if c_m_remaining_d:
                if rec.employee_type == 'perm_staff':
                    res.update({'deduction_settlements': rec.contract_id.gross_salary / 21.75 * c_m_remaining_d})
                else:
                    deduction = 0.0
                    deduction += c_m_remaining_d * (rec.contract_id.gross_salary / 30)
                    if rec.contract_id.provided_1:
                        deduction -= c_m_remaining_d * (
                                rec.contract_id.accommodation / 30)

                    if rec.contract_id.provided_2:
                        deduction -= c_m_remaining_d * (
                                rec.contract_id.transport_allowance / 30)

                    if rec.contract_id.provided_3:
                        deduction -= c_m_remaining_d * (
                                rec.contract_id.food_allowance / 30)

                    if rec.contract_id.uniform_provided:
                        deduction -= c_m_remaining_d * (
                                rec.contract_id.uniform / 30)

                    res.update({'deduction_settlements': rec.contract_id.gross_salary / 30 * r_d_from_p_month})
            return res

    def check_absent_half_unpaid_days_number(self, total_absence_days, s_h_paid_days, s_u_days):
        for rec in self:
            if rec.employee_type == "perm_staff":
                return min(total_absence_days, 21.75), min(s_h_paid_days, 21.75), min(s_u_days, 21.75)
            else:
                return min(total_absence_days, 30), min(s_h_paid_days, 30), min(s_u_days, 30)

    def get_leave_advance_settlement(self):
        for rec in self:
            start_date = rec.actual_date_from
            end_date = rec.actual_date_to
            include_food = 0
            res = {}
            leaves = rec.env['hr.leave'].search(
                [('holiday_status_id.is_annual', '=', True), ('has_leave_advance', '=', True),
                 ('employee_id', '=', rec.employee_id.id), ('state', '=', 'validate'), '|', '&',
                 ('pay_on', '>=', start_date), ('pay_on', '<=', end_date),
                 '&', ('pay_off_for_staff', '>=', start_date),
                 ('pay_off_for_staff', '<=', end_date)])
            wage = mobile = site = other = social = accommodation = transport = uniform = food = 0
            wage_ded = mobile_ded = site_ded = other_ded = social_ded = accommodation_ded = transport_ded = uniform_ded = food_ded = 0
            if leaves:
                if rec.contract_id.payroll_group.l_a_food_alw:
                    include_food += 1
                for leave in leaves:
                    if start_date <= leave.pay_on <= end_date:
                        wage += leave.leave_wage
                        mobile += leave.leave_mobile_allowance
                        site += leave.leave_site_allowance
                        other += leave.leave_other_allowance
                        social += leave.leave_social_allowance
                        accommodation += leave.leave_accommodation
                        transport += leave.leave_transport_allowance
                        uniform += leave.leave_uniform_allowance
                        food += leave.leave_food_allowance if include_food else 0
                    elif start_date <= leave.pay_off_for_staff <= end_date:
                        wage_ded += leave.leave_wage
                        mobile_ded += leave.leave_mobile_allowance
                        site_ded += leave.leave_site_allowance
                        other_ded += leave.leave_other_allowance
                        social_ded += leave.leave_social_allowance
                        accommodation_ded += leave.leave_accommodation
                        transport_ded += leave.leave_transport_allowance
                        uniform_ded += leave.leave_uniform_allowance
                        food_ded += leave.leave_food_allowance if include_food else 0

            res.update({
                'leave_advance_wage': wage, 'leave_advance_mobile_allowance': mobile,
                'leave_advance_site_allowance': site,
                'leave_advance_other_allowance': other, 'leave_advance_accommodation': accommodation,
                'leave_advance_social_allowance': social, 'leave_advance_transport_allowance': transport,
                'leave_advance_uniform_allowance': uniform, 'leave_advance_food_allowance': food,
                'leave_advance_wage_ded': wage_ded, 'leave_advance_mobile_ded': mobile_ded,
                'leave_advance_site_ded': site_ded,
                'leave_advance_other_ded': other_ded, 'leave_advance_accommodation_ded': accommodation_ded,
                'leave_advance_social_ded': social_ded, 'leave_advance_transport_ded': transport_ded,
                'leave_advance_uniform_ded': uniform_ded, 'leave_advance_food_ded': food_ded,
            })
            return res

    def get_salary_allowances_and_deductions(self, total_absence_days, s_h_paid_days, s_u_days):
        for rec in self:
            if rec.contract_id:
                res = {}
                accommodation = acc_ded = acc_half = acc_unpaid = transport = trans_ded = trans_half = trans_unpaid = uniform = uniform_ded = uniform_half = \
                    uniform_unpaid = food = food_ded = 0

                if rec.employee_type != 'perm_staff':
                    if not rec.contract_id.uniform_provided:
                        uniform += rec.contract_id.uniform
                        uniform_ded += total_absence_days * rec.contract_id.uniform / 30
                        uniform_half += s_h_paid_days * rec.contract_id.uniform / 30 * 0.5
                        uniform_unpaid += s_u_days * rec.contract_id.uniform / 30
                    if not rec.contract_id.provided_1:
                        accommodation += rec.contract_id.accommodation
                        acc_ded += total_absence_days * rec.contract_id.accommodation / 30
                        acc_half += s_h_paid_days * rec.contract_id.accommodation / 30 * 0.5
                        acc_unpaid += s_u_days * rec.contract_id.accommodation / 30
                    if not rec.contract_id.provided_2:
                        transport += rec.contract_id.transport_allowance
                        trans_ded += total_absence_days * rec.contract_id.transport_allowance / 30
                        trans_half += s_h_paid_days * rec.contract_id.transport_allowance / 30 * 0.5
                        trans_unpaid += s_u_days * rec.contract_id.transport_allowance / 30
                    if not rec.contract_id.provided_3:
                        if rec.contract_id.payroll_group.fixed_food_allowance:
                            food += rec.contract_id.food_allowance
                            food_ded += total_absence_days / 30 * rec.contract_id.food_allowance
                        else:
                            num_of_days = (rec.date_to - rec.date_from).days + 1
                            num_of_days = min(num_of_days, 30)
                            num_of_days -= total_absence_days
                            food += num_of_days / 30 * rec.contract_id.food_allowance
                            food_ded += rec.contract_id.payroll_group.fixed_food_allowance
                    res.update({
                        'basic_deduction': total_absence_days * rec.contract_id.wage / 30,
                        'wage_unpaid': s_u_days * rec.contract_id.wage / 30,
                        'wage_half_paid': s_h_paid_days * rec.contract_id.wage / 30 * 0.5,
                        'mobile_allowance': rec.contract_id.mobile_allowance,
                        'mobile_deduction': total_absence_days * rec.contract_id.mobile_allowance / 30,
                        'mobile_half_paid': s_h_paid_days * rec.contract_id.mobile_allowance / 30 * 0.5,
                        'mobile_unpaid': s_u_days * rec.contract_id.mobile_allowance / 30,
                        'fixed_overtime_allowance': rec.contract_id.fixed_overtime_allowance,
                        'ticket_allowance': rec.contract_id.ticket_allowance,
                        'site_allowance': rec.contract_id.site_allowance,
                        'site_deduction': total_absence_days * rec.contract_id.site_allowance / 30,
                        'site_half_paid': s_h_paid_days * rec.contract_id.site_allowance / 30 * 0.5,
                        'site_unpaid': s_u_days * rec.contract_id.site_allowance / 30,
                        'accommodation_allowance': rec.contract_id.accommodation,
                        'accommodation_deduction': acc_ded,
                        'accommodation_half_paid': acc_half,
                        'accommodation_unpaid': acc_unpaid,
                        'other_allowance': rec.contract_id.other_allowance,
                        'other_deduction': total_absence_days * rec.contract_id.other_allowance / 30,
                        'other_half_paid': s_h_paid_days * rec.contract_id.other_allowance / 30 * 0.5,
                        'other_unpaid': s_u_days * rec.contract_id.other_allowance / 30,
                        'uniform_deduction': uniform_ded,
                        'uniform_half_paid': uniform_half,
                        'uniform_unpaid': uniform_unpaid,
                        'laundry_allowance': uniform,
                        'transportation_allowance': rec.contract_id.transport_allowance,
                        'transportation_deduction': trans_ded,
                        'transport_half_paid': trans_half,
                        'transport_unpaid': trans_unpaid,
                        'food_allowance': food,
                        'food_deduction': food_ded,
                    })
                elif rec.employee_type == 'perm_staff':

                    res.update({
                        'basic_deduction': total_absence_days * rec.contract_id.wage / 21.75,
                        'wage_unpaid': s_u_days * rec.contract_id.wage / 21.75,
                        'wage_half_paid': s_h_paid_days * rec.contract_id.wage / 21.75 * 0.5,
                        'mobile_allowance': rec.contract_id.mobile_allowance,
                        'mobile_deduction': total_absence_days * rec.contract_id.mobile_allowance / 21.75,
                        'mobile_half_paid': s_h_paid_days * rec.contract_id.mobile_allowance / 21.75 * 0.5,
                        'mobile_unpaid': s_u_days * rec.contract_id.mobile_allowance / 21.75,
                        'fixed_overtime_allowance': rec.contract_id.fixed_overtime_allowance,
                        'ticket_allowance': rec.contract_id.ticket_allowance,
                        'accommodation_allowance': rec.contract_id.accommodation,
                        'accommodation_deduction': total_absence_days * rec.contract_id.accommodation / 21.75,
                        'accommodation_half_paid': s_h_paid_days * rec.contract_id.accommodation / 21.75 * 0.5,
                        'accommodation_unpaid': s_u_days * rec.contract_id.accommodation / 21.75,
                        'other_allowance': rec.contract_id.other_allowance if rec.employee_id.is_classified else 0,
                        'other_deduction': total_absence_days * rec.contract_id.other_allowance / 21.75 if rec.employee_id.is_classified else 0,
                        'transportation_allowance': rec.contract_id.transport_allowance,
                        'transportation_deduction': total_absence_days * rec.contract_id.transport_allowance / 21.75,
                        'transport_half_paid': s_h_paid_days * rec.contract_id.wage / 21.75 * 0.5,
                        'transport_unpaid': s_u_days * rec.contract_id.wage / 21.75,
                        'social_allowance': rec.contract_id.social_allowance_for_permanent_staff,
                        'social_deduction': total_absence_days * rec.contract_id.social_allowance_for_permanent_staff / 21.75,
                        'social_half_paid': s_h_paid_days * rec.contract_id.social_allowance_for_permanent_staff / 21.75 * 0.5,
                        'social_unpaid': s_u_days * rec.contract_id.social_allowance_for_permanent_staff / 21.75,
                        'other_half_paid': s_h_paid_days * rec.contract_id.other_allowance / 21.75 * 0.5 if rec.employee_id.is_classified else 0,
                        'other_unpaid': s_u_days * rec.contract_id.other_allowance / 21.75 if rec.employee_id.is_classified else 0,
                    })
                return res

    def create_payslip(self):
        if self.employee_id.status not in ['suspended', 'terminated', 'resigned', 'terminated_w_reason']:
            payslip = self.env['hr.payslip']
            payslip_input_type = self.env['hr.payslip.input.type'].search([])

            for att_sheet in self:
                if att_sheet.payslip_id:
                    new_payslip = att_sheet.payslip_id
                    continue

                from_date = att_sheet.date_from
                to_date = att_sheet.date_to
                employee = att_sheet.employee_id
                salary_rules = []
                res = {
                    'name': 'draft',
                    'contract_id': employee.contract_id.id,
                    'employee_id': employee.id,
                    'date_from': self.actual_date_from,
                    'date_to': self.actual_date_to,
                    'actual_day_from': self.actual_date_from,
                    'actual_day_to': self.actual_date_to,
                    'remarks': self.note,
                }
                if att_sheet.batch_id and att_sheet.batch_id.payslip_batch_id:
                    res['payslip_run_id'] = att_sheet.batch_id.payslip_batch_id.id
                new_payslip = payslip.create(res)

                # add Accommodation Allowance
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'ACCOMM')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': self.accommodation_allowance
                })
                # add Transport Allowance
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'TRA')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': self.transportation_allowance
                })
                # add Food Allowance
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'FOOD')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': self.food_allowance
                })
                # add site Allowance
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'Site')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': self.site_allowance
                })
                # add mobile Allowance
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'MOBILE')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': self.mobile_allowance
                })
                # add other Allowance
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'OTHER')

                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': self.other_allowance
                })
                # add ticket Allowance
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'TICKET')

                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': self.ticket_allowance
                })
                # # add overtime Allowance

                # add Laundry Allowance
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'LAUNDRY')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': self.laundry_allowance
                })

                # add Earning Settlement Allowance
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'EARNING')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': self.earning_allowance
                })
                # add Social Allowance
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'SOCIAL')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': self.social_allowance
                })

                # add furniture Allowance
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'FURNITURE')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': self.furniture_allowance
                })

                # add leave basic salary allowance to
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'LADW')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': self.leave_advance_wage
                })

                # add leave accommodation allowance
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'LADACM')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': self.leave_advance_accommodation
                })

                # add leave mobile allowance
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'LADMO')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': self.leave_advance_mobile_allowance
                })

                # add leave food allowance
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'LADFDW')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': self.leave_advance_food_allowance
                })

                # add leave site allowance
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'LADSTW')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': self.leave_advance_site_allowance
                })

                # add leave transportation allowance
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'LADTRW')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': self.leave_advance_transport_allowance
                })

                # add leave other allowance
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'LADOTHW')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': self.leave_advance_other_allowance
                })

                # add leave uniform allowance
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'LADUNIFORM')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': self.leave_advance_uniform_allowance
                })

                # add leave social allowance
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'LADSOC')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': self.leave_advance_social_allowance
                })
                # add leave wage deduction
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'LADWD')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -self.leave_advance_wage_ded
                })
                #
                # add leave accommodation deduction
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'LADACMD')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -self.leave_advance_accommodation_ded
                })
                # add leave mobile deduction
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'LADMOD')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -self.leave_advance_mobile_ded
                })

                # add leave food deduction
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'LADFDWD')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -self.leave_advance_food_ded
                })
                # add leave site deduction
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'LADSTWD')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -self.leave_advance_site_ded
                })
                # add leave transportation deduction
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'LADTRWD')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -
                    self.leave_advance_transport_ded
                })
                # add leave other deduction
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'LADOTHWD')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -self.leave_advance_other_ded
                })
                # add leave uniform deduction
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'LADUNID')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -self.leave_advance_uniform_ded
                })
                # add leave social deduction
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'LADSOCD')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -self.leave_advance_social_ded
                })

                # add Basic Deduction
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'BASICDED')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -(self.basic_deduction + self.wage_half_paid + self.wage_unpaid)
                })
                # add Other Deduction
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'OTHERDED')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -(self.other_deduction + self.other_half_paid + self.other_unpaid)
                })
                # add Transport Deduction
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'TRANSDED')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -(self.transportation_deduction + self.transport_half_paid + self.transport_unpaid)
                })
                # add Accommodation Deduction
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'ACCOMMDED')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -(self.accommodation_deduction + self.accommodation_half_paid + self.accommodation_unpaid)
                })
                # add Mobile Deduction
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'MOBILEDED')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -(self.mobile_deduction + self.mobile_half_paid + self.mobile_unpaid)
                })
                # add Food Deduction
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'FOODDED')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -self.food_deduction
                })
                # add Laundry Deduction
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'UNIFORMDED')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -(self.uniform_deduction + self.uniform_half_paid + self.uniform_unpaid)
                })
                # add Social Deduction
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'SOCIALDED')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -(self.social_deduction + self.uniform_half_paid + self.uniform_unpaid)
                })
                # add Site Deduction
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'SITEDED')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -(self.site_deduction + self.site_half_paid + self.site_unpaid)
                })
                # add overtime Deduction
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'OVERTDED')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -self.overtime_deduction
                })
                # add Deduction Settlement
                acc_input_type = payslip_input_type.filtered(lambda x: x.code == 'SETTLEDED')
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': self.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -self.deduction_settlements
                })
                self.env['hr.payslip.input'].create(salary_rules)


class attendance_sheet_line(models.Model):
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
    att_sheet_id = fields.Many2one(comodel_name='attendance.sheet', string='Attendance Sheet', readonly=True, )
    employee_number = fields.Char(related='att_sheet_id.employee_id.registration_number', store=True)
    employee_id = fields.Many2one(comodel_name='hr.employee', related='att_sheet_id.employee_id', store=True)
    pl_sign_in = fields.Float("Planned sign in", readonly=True)
    pl_sign_out = fields.Float("Planned sign out", readonly=True)
    worked_hours = fields.Float("Worked Hours", readonly=True)
    ac_sign_in = fields.Float("Actual sign in", readonly=True)
    ac_sign_out = fields.Float("Actual sign out", readonly=True)
    overtime_cuttoff_date = fields.Date("OVertime Cuttoff Date", readonly=True)
    overtime = fields.Float("Overtime", readonly=True)
    remaining_overtime = fields.Float("Remaining Overtime Amount", readonly=True)
    special_overtime = fields.Float("SP Overtime", readonly=True)
    remaining_special_overtime = fields.Float("Remaining SP Overtime Amount", readonly=True)
    late_in = fields.Float("Late In", readonly=True)
    diff_time = fields.Float("Diff Time", help="Diffrence between the working time and attendance time(s) ",
                             readonly=True)
    note = fields.Text("Note", readonly=True)
    status = fields.Selection(string="Status",
                              selection=[('ab', 'Absence'), ('weekend', 'Week End'), ('ph', 'Public Holiday'),
                                         ('leave', 'Leave'), ('illegal', 'Absence'),
                                         ('half_paid', 'Half Paid'), ('unpaid', 'Unpaid'),
                                         ('unpaid_leave', 'Unpaid Leave'),
                                         ('legal_permission', ''),
                                         ],
                              required=False, readonly=True)
    att_status = fields.Selection(string="Att Status",
                                  selection=[('late', 'Late In'), ('diff', 'Early Leave'),
                                             ('over', 'Overtime'),
                                             ('over+late', 'Late In, Overtime'),
                                             ('diff+late', 'Late In, Early Leave'), ],
                                  required=False, readonly=True)
    # employee_project = fields.Many2one(comodel_name="project_project", string="Project", required=False)
    project_id = fields.Many2one(
        'project.project',
        string='Project'
    )
