# -*- coding: utf-8 -*-
from datetime import date
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from calendar import monthrange
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta

from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT, format_date


class EmployeeMasterInherit(models.Model):
    _inherit = 'hr.leave'

    def _get_working_days(self, start_date, end_date):
        if start_date and end_date:
            # get list of all days

            all_days = (start_date + timedelta(x) for x in range((end_date - start_date).days + 1))

            # filter business days
            # weekday from 0 to 4. 0 is monday adn 4 is friday
            # increase counter in each iteration if it is a weekday

            count = sum(1 for day in all_days if day.weekday() in [0, 1, 2, 3, 6])
            return count

    # @api.depends('leave_checklist')
    # def leave_progress(self):
    #     for each in self:
    #         total_len = self.env['employee.checklist'].search_count([('document_type', '=', 'leave')])
    #         entry_len = len(each.leave_checklist)
    #         if total_len != 0:
    #             each.leave_progress = (entry_len * 100) / total_len
    #         else:
    #             each.leave_progress = 0

    # leave_checklist = fields.Many2many('employee.checklist', 'leave_obj', 'leave_hr_rel', 'hr_leave_rel',
    #                                    string='Leave Process',
    #                                    domain=[('document_type', '=', 'leave')])
    # leave_progress = fields.Float(compute=leave_progress, string='Leave Progress', store=True, default=0.0)
    maximum_rate = fields.Integer(default=100)
    check_list_enable = fields.Boolean(invisible=True, copy=False)
    approved_automatic = fields.Boolean(string="Created Automatically", default=False)
    employee_type = fields.Selection(string="Employment Category", related="employee_id.employee_type")

    contract_id = fields.Many2one('hr.contract', related="employee_id.contract_id")
    currency_id = fields.Many2one('res.currency', related="contract_id.currency_id")

    pay_on = fields.Date(string="Pay on", compute="_get_pay_on_date", store=True)
    pay_off_for_staff = fields.Date(string="Pay Back", compute="_get_pay_off_for_staff_date", store=True,
                                    states={'draft': [('readonly', False)], 'confirm': [('readonly', False)],
                                            'first_approval': [('readonly', False)], 'validate1': [('readonly', False)]
                                            })
    payslip_id = fields.Many2one(comodel_name="hr.payslip", string="Payslip", required=False)

    wage = fields.Monetary('Basic Salary', required=False, related="contract_id.wage")
    leave_wage = fields.Monetary('Leave Basic Salary', required=False)
    has_wage = fields.Boolean(string="", default=True, readonly=True)

    accommodation = fields.Monetary('Accommodation', related="contract_id.accommodation")
    leave_accommodation = fields.Monetary('Leave Accommodation', )
    has_accommodation = fields.Boolean(string="", default=True, readonly=False)

    mobile_allowance = fields.Monetary('Mobile Allowance', related="contract_id.mobile_allowance")
    leave_mobile_allowance = fields.Monetary('Leave Mobile Allowance')
    has_mobile_allowance = fields.Boolean(string="", default=True, readonly=False)

    food_allowance = fields.Monetary('Food Allowance', related="contract_id.food_allowance")
    leave_food_allowance = fields.Monetary('Food Allowance')

    has_food_allowance = fields.Boolean(string="", default=True, readonly=False)

    site_allowance = fields.Monetary('Site Allowance',
                                     related="contract_id.site_allowance")
    leave_site_allowance = fields.Monetary('Site Allowance')
    has_site_allowance = fields.Boolean(string="", default=True, readonly=False)

    transport_allowance = fields.Monetary('Transport Allowance',
                                          related="contract_id.transport_allowance")
    leave_transport_allowance = fields.Monetary('Transport Allowance')

    has_transport_allowance = fields.Boolean(string="", default=True, readonly=False)

    social_allowance = fields.Monetary('Social Allowance',
                                       related="contract_id.social_allowance_for_permanent_staff")
    has_social_allowance = fields.Boolean(string="", default=True, readonly=False)

    leave_social_allowance = fields.Monetary('Social Allowance')

    other_allowance = fields.Monetary('Other Allowance',
                                      related="contract_id.other_allowance")

    leave_other_allowance = fields.Monetary('Leave Other Allowance')

    has_other_allowance = fields.Boolean(string="", default=True, readonly=False)

    uniform_allowance = fields.Monetary('Uniform Allowance',
                                        related="contract_id.uniform")

    leave_uniform_allowance = fields.Monetary('Leave Uniform Allowance')

    has_uniform_allowance = fields.Boolean(string="", default=True, readonly=False)

    total_amount = fields.Monetary('Total Amount', compute='_compute_leave_amount', default=0.0)
    is_legal = fields.Boolean(string="", related='holiday_status_id.legal')
    food_alw_visible = fields.Boolean(string="")
    leave_count = fields.Integer(compute="get_leave_count")

    def get_leave_count(self):
        for rec in self:
            leaves = self.env['return.from.leave'].search([('leave_id', '=', rec.id)]).ids
            if len(leaves) > 0:
                rec.leave_count = len(leaves)
            else:
                rec.leave_count = 0

    def create_early_return(self):
        # return self.env.ref('ebs_waseef_leave_advance.action_return_from_leave_data_wizard').read()[0]
        return {
            'name': "Early Return From Leave",
            'view_mode': 'form',
            'res_model': 'return.leave.wizard',
            'type': 'ir.actions.act_window',
            'context': {'default_has_leave_advance': self.has_leave_advance},
            'target': 'new',
        }

    def action_get_return_leave(self):
        leaves = self.env['return.from.leave'].search([('leave_id', '=', self.id)])
        if len(leaves) > 0:
            return {
                'name': "Early Return",
                'view_mode': 'tree,form',
                'res_model': 'return.from.leave',
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', leaves.ids)]
            }

    def action_cancel(self):
        self.action_refuse()
        self.write({"state": "cancel"})

    def action_draft(self):
        if any(holiday.state not in ['confirm', 'refuse', 'cancel'] for holiday in self):
            raise UserError(
                _('Time off request state must be "Refused" or "To Approve" in order to be reset to draft.'))
        self.write({
            'state': 'draft',
            'first_approver_id': False,
            'second_approver_id': False,
        })
        linked_requests = self.mapped('linked_request_ids')
        if linked_requests:
            linked_requests.action_draft()
            linked_requests.unlink()
        self.activity_update()
        return True

    # @api.onchange('pay_on')
    # @api.constrains('pay_on')
    # def _check_pay_on_date(self):
    #     if self.employee_id and self.pay_on:
    #         if self.date_from <= self.pay_on:
    #             raise ValidationError(f'Pay On date should be before {self.date_from}')

    # @api.model
    # def create(self, vals):
    #     leave = super(EmployeeMasterInherit, self).create(vals)
    #     leave._onchange_request_parameters()
    #     leave._get_calendar_days()
    #     leave._calculate_actual_leave_amount()
    #     return leave
    @api.onchange('employee_id')
    def check_emp_grade(self):
        for rec in self:
            if rec.employee_id and rec.employee_id.contract_id and rec.employee_id.contract_id.payroll_group:
                if not rec.employee_id.contract_id.provided_3 and rec.employee_id.contract_id.food_allowance and rec.employee_id.contract_id.payroll_group.l_a_food_alw:
                    rec.food_alw_visible = True
                else:
                    rec.food_alw_visible = False

    @api.depends('date_from')
    def _get_pay_on_date(self):
        for rec in self:
            if rec.date_from:
                month = int(rec.date_from.strftime('%m'))
                year = int(rec.date_from.strftime('%Y'))
                # if month is January, we edit the month and the year values
                if month == 1:
                    month = 13
                    year = year - 1

                rec.pay_on = rec.date_from.replace(year=year, month=month - 1, day=1)

    @api.depends('pay_on')
    def _get_pay_off_for_staff_date(self):
        for rec in self:
            if rec.pay_on and rec.pay_on:
                rec.pay_off_for_staff = rec.pay_on + relativedelta(months=1)
                # print(self.pay_off_for_staff)
                # month = int(self.date_from.strftime('%m'))
                # year = int(self.date_from.strftime('%Y'))
                # # if month is January, we edit the month and the year values
                # if month == 12:
                #     month = 0
                #     year = year + 1
                # self.pay_off_for_staff = self.date_from.replace(year=year, month=month + 1, day=1)

    # @api.depends('employee_id')
    # def _get_emp_type(self):
    #     for rec in self:
    #         if rec.employee_id:
    #             rec.employee_type = rec.employee_id.employee_type

    @api.depends('employee_id', 'has_wage', 'has_accommodation', 'has_mobile_allowance', 'has_site_allowance',
                 'has_leave_advance', 'has_uniform_allowance', 'has_social_allowance',
                 'has_transport_allowance', 'has_other_allowance', 'date_from', 'date_to')
    def _compute_leave_amount(self):
        for rec in self:
            rec._calculate_actual_leave_amount()
            rec.total_amount = 0
            if rec.has_leave_advance and rec.employee_id:
                if rec.employee_type == 'perm_in_house':
                    total_amount = 0.0
                    if rec.has_wage:
                        total_amount += rec.leave_wage
                    if rec.has_accommodation:
                        total_amount += rec.leave_accommodation
                    if rec.has_mobile_allowance:
                        total_amount += rec.leave_mobile_allowance
                    if rec.has_site_allowance:
                        total_amount += rec.leave_site_allowance
                    if rec.has_transport_allowance:
                        total_amount += rec.leave_transport_allowance
                    if rec.has_other_allowance:
                        total_amount += rec.leave_other_allowance
                    if rec.has_uniform_allowance:
                        total_amount += rec.leave_uniform_allowance
                    if rec.employee_id.contract_id.payroll_group.l_a_food_alw:
                        if rec.has_food_allowance:
                            total_amount += rec.leave_food_allowance
                    rec.total_amount = round(total_amount, 0)

                elif rec.employee_type == 'perm_staff':
                    total_amount = 0.0
                    if rec.has_wage:
                        total_amount += rec.wage
                    if rec.has_accommodation:
                        total_amount += rec.accommodation
                    if rec.has_mobile_allowance:
                        total_amount += rec.mobile_allowance
                    if rec.has_transport_allowance:
                        total_amount += rec.transport_allowance
                    if rec.has_social_allowance:
                        total_amount += rec.social_allowance
                    if rec.employee_id.is_classified:
                        if rec.has_other_allowance:
                            total_amount += rec.other_allowance
                    rec.total_amount = total_amount

    # @api.onchange('has_leave_advance')
    @api.constrains('has_leave_advance', 'request_date_to', 'request_date_from')
    def check_duration_of_leave(self):
        for rec in self:
            # Staff employee has at most one leave advance on year
            # In house employee has more than one leave advance on year
            # can not create same leave advance o same month
            if rec.has_leave_advance and rec.request_date_to:
                domain = [
                    ('employee_id', '=', rec.employee_id.id),
                    ('id', '!=', rec.id), ('state', '=', 'validate'),
                    ('has_leave_advance', '=', True),
                ]
                current_year = rec.request_date_to.year or date.today().year
                first_day_year = date(current_year, 1, 1)
                last_day_year = date(current_year, 12, 31)
                if rec.employee_type == 'perm_staff':
                    domain.extend(
                        (
                            ('request_date_from', '>=', first_day_year),
                            ('request_date_from', '<=', last_day_year)
                        )
                    )
                # print("domain ", domain)
                leaves = rec.env['hr.leave'].search(domain).filtered(
                    lambda x: x.pay_on and rec.pay_on and x.pay_on.month == rec.pay_on.month
                              and x.pay_on.year == rec.pay_on.year == rec.pay_on.year)
                # print("leaves ", leaves)
                if leaves:
                    raise ValidationError(_('The employee has already leave advance in the current year'))
                if rec.employee_type == 'perm_staff' and rec.date_from and rec.date_to:
                    print("number_of_days ", rec.number_of_days, rec)
                    if rec.has_leave_advance and rec.number_of_days < 15:
                        raise ValidationError(f'You can not request advance leave payment for < 15 days')

    def _calculate_actual_leave_amount(self):
        for rec in self:
            if rec.employee_type == 'perm_in_house':
                number_of_days = rec.calendar_days
                # allocations = rec.env['hr.leave.allocation'].search([('employee_id', '=', rec.employee_id.id),
                #                                                      ('holiday_status_id.is_annual', '=', True),
                #                                                      ('state', '=', 'validate')])
                # n_of_allocations = sum(allocations.mapped('number_of_days'))
                # if number_of_days > n_of_allocations:
                #     # raise ValidationError(f"The requested leave days is greater than the employee's leave allocation")
                #     number_of_days = n_of_allocations
                if rec.has_wage:
                    rec.leave_wage = number_of_days * rec.wage / 30
                else:
                    rec.leave_wage = 0

                if rec.has_accommodation:
                    rec.leave_accommodation = number_of_days * rec.accommodation / 30
                else:
                    rec.leave_accommodation = 0

                if rec.has_mobile_allowance:
                    rec.leave_mobile_allowance = number_of_days * rec.mobile_allowance / 30
                else:
                    rec.leave_mobile_allowance = 0

                if rec.has_food_allowance and rec.employee_id.contract_id.payroll_group.l_a_food_alw:
                    rec.leave_food_allowance = number_of_days * rec.food_allowance / 30
                else:
                    rec.leave_food_allowance = 0

                if rec.has_site_allowance:
                    rec.leave_site_allowance = number_of_days * rec.site_allowance / 30
                else:
                    rec.leave_site_allowance = 0

                if rec.has_transport_allowance:
                    rec.leave_transport_allowance = number_of_days * rec.transport_allowance / 30
                else:
                    rec.leave_transport_allowance = 0

                if rec.has_other_allowance:
                    rec.leave_other_allowance = number_of_days * rec.other_allowance / 30
                else:
                    rec.leave_other_allowance = 0

                if rec.has_uniform_allowance:
                    rec.leave_uniform_allowance = number_of_days * rec.uniform_allowance / 30
                else:
                    rec.leave_uniform_allowance = 0
                # number_of_days = self.number_of_days
                # self.leave_wage = number_of_days / 30 * self.wage
                # if not self.employee_id.contract_id.provided_1:
                #     self.leave_accommodation = number_of_days / 30 * self.accommodation
                # if not self.employee_id.contract_id.provided_2:
                #     self.leave_mobile_allowance = number_of_days / 30 * self.mobile_allowance
                # if not self.employee_id.contract_id.provided_3:
                #     self.leave_transport_allowance = number_of_days / 30 * self.transport_allowance
                # if not self.employee_id.contract_id.uniform_provided:
                #     self.leave_uniform_allowance = number_of_days / 30 * self.uniform
            elif rec.employee_type == 'perm_staff':
                if rec.has_wage:
                    rec.leave_wage = rec.wage
                else:
                    rec.leave_wage = 0

                if rec.has_accommodation:
                    rec.leave_accommodation = rec.accommodation
                else:
                    rec.leave_accommodation = 0

                if rec.has_mobile_allowance:
                    rec.leave_mobile_allowance = rec.mobile_allowance
                else:
                    rec.leave_mobile_allowance = 0

                if rec.has_transport_allowance:
                    rec.leave_transport_allowance = rec.transport_allowance
                else:
                    rec.leave_transport_allowance = 0
                if rec.has_social_allowance:
                    rec.leave_social_allowance = rec.social_allowance
                else:
                    rec.leave_social_allowance = 0
                if rec.has_other_allowance:
                    if rec.employee_id.is_classified:
                        rec.leave_other_allowance = rec.other_allowance
                else:
                    rec.leave_other_allowance = 0

    def get_number_of_days_in_month(self, year, month):
        return monthrange(year, month)[1]

    # to calculate the leave amount based on the number of actual leave days
    # def _calculate_actual_leave_amount(self):
    #     if self.employee_type == 'perm_in_house':
    #         # year_from, month_from = int(self.date_from.strftime('%y')), int(self.date_from.strftime('%m'))
    #         # year_to, month_to = int(self.date_to.strftime('%y')), int(self.date_to.strftime('%m'))
    #         # # month_from_days = self.get_number_of_days_in_month(year_from, month_from)
    #         # # month_to_days = self.get_number_of_days_in_month(year_to, month_to)
    #         # month_from_days = 30
    #         # month_to_days = 30
    #         # diff = (self.date_to.year - self.date_from.year) * 12 + (self.date_to.month - self.date_from.month)
    #         # total = 0
    #         wage_total = 0
    #         accommodation_total = 0
    #         transportation_total = 0
    #         food_total = 0
    #         site_total = 0
    #         other_total = 0
    #         mobile_total = 0
    #         social_total = 0
    #         uniform_total = 0
    #
    #         # to check the difference of months between two dates
    #         # if diff > 1:
    #         #     in_between_months = diff - 1
    #         #     total += self.total_amount * in_between_months
    #         #     wage_total += self.wage * in_between_months
    #         #     accommodation_total += self.accommodation * in_between_months
    #         #     transportation_total += self.transport_allowance * in_between_months
    #         #     food_total += self.food_allowance * in_between_months
    #         #     site_total += self.site_allowance * in_between_months
    #         #     other_total += self.other_allowance * in_between_months
    #         #     mobile_total += self.mobile_allowance * in_between_months
    #         #     social_total += self.social_allowance * in_between_months
    #         #     uniform_total += self.uniform_allowance * in_between_months
    #         #     self._calculate_total_amount(total, month_from_days, month_to_days)
    #         #     self._calculate_allowances_amount(wage_total, accommodation_total, transportation_total, food_total,
    #         #                                       site_total, other_total, mobile_total, social_total, uniform_total,
    #         #                                       month_from_days, month_to_days)
    #         # elif diff == 0:
    #         #     days_num = (int(self.date_to.strftime('%d')) - int(self.date_from.strftime('%d'))) + 1
    #         #     self.total_amount = days_num * self.total_amount / month_from_days
    #         #
    #         #     if self.has_wage:
    #         #         self.leave_wage = days_num * self.wage / month_from_days
    #         #     else:
    #         #         self.leave_wage = 0
    #         #
    #         #     if self.has_accommodation:
    #         #         self.leave_accommodation = days_num * self.accommodation / month_from_days
    #         #     else:
    #         #         self.leave_accommodation = 0
    #         #
    #         #     if self.has_mobile_allowance:
    #         #         self.leave_mobile_allowance = days_num * self.mobile_allowance / month_from_days
    #         #     else:
    #         #         self.leave_mobile_allowance = 0
    #         #
    #         #     if self.has_food_allowance:
    #         #         self.leave_food_allowance = days_num * self.food_allowance / month_from_days
    #         #     else:
    #         #         self.leave_food_allowance = 0
    #         #
    #         #     if self.has_site_allowance:
    #         #         self.leave_site_allowance = days_num * self.site_allowance / month_from_days
    #         #     else:
    #         #         self.leave_site_allowance = 0
    #         #
    #         #     if self.has_transport_allowance:
    #         #         self.leave_transport_allowance = days_num * self.transport_allowance / month_from_days
    #         #     else:
    #         #         self.leave_transport_allowance = 0
    #         #
    #         #     if self.has_other_allowance:
    #         #         self.leave_other_allowance = days_num * self.other_allowance / month_from_days
    #         #     else:
    #         #         self.leave_other_allowance = 0
    #         #
    #         #     if self.has_social_allowance:
    #         #         self.leave_social_allowance = days_num * self.social_allowance / month_from_days
    #         #     else:
    #         #         self.leave_social_allowance = 0
    #         #
    #         #     if self.has_uniform_allowance:
    #         #         self.leave_uniform_allowance = days_num * self.uniform_allowance / month_from_days
    #         #     else:
    #         #         self.leave_uniform_allowance = 0
    #         #
    #         # else:
    #         #     # self._calculate_total_amount(total, month_from_days, month_to_days)
    #         #     # self._calculate_allowances_amount(wage_total, accommodation_total, transportation_total, food_total,
    #         #     #                                   site_total, other_total, mobile_total, social_total, uniform_total,
    #         #     #                                   month_from_days, month_to_days)
    #     elif self.employee_type == 'perm_staff':
    #         self.leave_wage = self.wage
    #         self.leave_accommodation = self.accommodation
    #         self.leave_mobile_allowance = self.mobile_allowance
    #         self.leave_transport_allowance = self.transport_allowance
    #         self.leave_social_allowance = self.social_allowance
    #         if self.employee_id.is_classified:
    #             self.leave_other_allowance = self.other_allowance
    #
    # def _calculate_total_amount(self, total, month_from_days, month_to_days):
    #     total_from = ((month_from_days - int(self.date_from.strftime('%d')) + 1) * self.total_amount / month_from_days)
    #     total_to = (int(self.date_to.strftime('%d')) * self.total_amount / month_to_days)
    #     self.total_amount = total + total_from + total_to
    #
    # def _calculate_allowances_amount(self, wage_total, accommodation_total, transportation_total, food_total,
    #                                  site_total, other_total, mobile_total, social_total, uniform_total,
    #                                  month_from_days, month_to_days):
    #
    #     wage_total_from = ((month_from_days - int(self.date_from.strftime('%d')) + 1) * self.wage / month_from_days)
    #     wage_total_to = (int(self.date_to.strftime('%d')) * self.wage / month_to_days)
    #     accommodation_total_from = (
    #             (month_from_days - int(self.date_from.strftime('%d')) + 1) * self.accommodation / month_from_days)
    #     accommodation_total_to = (int(self.date_to.strftime('%d')) * self.accommodation / month_to_days)
    #
    #     transportation_total_from = ((month_from_days - int(
    #         self.date_from.strftime('%d')) + 1) * self.transport_allowance / month_from_days)
    #     transportation_total_to = (int(self.date_to.strftime('%d')) * self.transport_allowance / month_to_days)
    #
    #     food_total_from = (
    #             (month_from_days - int(self.date_from.strftime('%d')) + 1) * self.food_allowance / month_from_days)
    #     food_total_to = (int(self.date_to.strftime('%d')) * self.food_allowance / month_to_days)
    #
    #     site_total_from = (
    #             (month_from_days - int(self.date_from.strftime('%d')) + 1) * self.site_allowance / month_from_days)
    #     site_total_to = (int(self.date_to.strftime('%d')) * self.site_allowance / month_to_days)
    #
    #     other_total_from = (
    #             (month_from_days - int(self.date_from.strftime('%d')) + 1) * self.other_allowance / month_from_days)
    #     other_total_to = (int(self.date_to.strftime('%d')) * self.other_allowance / month_to_days)
    #
    #     mobile_total_from = ((month_from_days - int(
    #         self.date_from.strftime('%d')) + 1) * self.mobile_allowance / month_from_days)
    #     mobile_total_to = (int(self.date_to.strftime('%d')) * self.mobile_allowance / month_to_days)
    #
    #     social_total_from = ((month_from_days - int(
    #         self.date_from.strftime('%d')) + 1) * self.social_allowance / month_from_days)
    #     social_total_to = (int(self.date_to.strftime('%d')) * self.social_allowance / month_to_days)
    #
    #     uniform_total_from = ((month_from_days - int(
    #         self.date_from.strftime('%d')) + 1) * self.uniform_allowance / month_from_days)
    #     uniform_total_to = (int(self.date_to.strftime('%d')) * self.uniform_allowance / month_to_days)
    #
    #     if self.has_wage:
    #         self.leave_wage = wage_total + wage_total_from + wage_total_to
    #     else:
    #         self.leave_wage = 0
    #
    #     if self.has_accommodation:
    #         self.leave_accommodation = accommodation_total + accommodation_total_from + accommodation_total_to
    #     else:
    #         self.leave_accommodation = 0
    #
    #     if self.has_mobile_allowance:
    #         self.leave_mobile_allowance = mobile_total + mobile_total_from + mobile_total_to
    #     else:
    #         self.leave_mobile_allowance = 0
    #
    #     if self.has_food_allowance:
    #         self.leave_food_allowance = food_total + food_total_from + food_total_to
    #     else:
    #         self.leave_food_allowance = 0
    #
    #     if self.has_site_allowance:
    #         self.leave_site_allowance = site_total + site_total_from + site_total_to
    #     else:
    #         self.leave_site_allowance = 0
    #
    #     if self.has_transport_allowance:
    #         self.leave_transport_allowance = transportation_total + transportation_total_from + transportation_total_to
    #     else:
    #         self.leave_transport_allowance = 0
    #
    #     if self.has_other_allowance:
    #         self.leave_other_allowance = other_total + other_total_from + other_total_to
    #     else:
    #         self.leave_other_allowance = 0
    #
    #     if self.has_social_allowance:
    #         self.leave_social_allowance = social_total + social_total_from + social_total_to
    #     else:
    #         self.leave_social_allowance = 0
    #
    #     if self.has_uniform_allowance:
    #         self.leave_uniform_allowance = uniform_total + uniform_total_from + uniform_total_to
    #     else:
    #         self.leave_uniform_allowance = 0

# class EmployeeChecklistInherit(models.Model):
#     _inherit = 'employee.checklist'
#
#     leave_obj = fields.Many2many('hr.leave', 'leave_checklist', 'hr_leave_rel', 'leave_hr_rel', invisible=1)
