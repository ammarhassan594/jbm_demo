# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from datetime import date
import math


class AdditionalElements(models.Model):
    _name = 'ebs.mod.end.of.service.payment.request'
    _rec_name = 'employee_id'
    _description = 'AdditionalElements'

    def _get_employee_id(self):
        employee_rec = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        if employee_rec:
            return employee_rec.id
        else:
            return 0

    employee_id = fields.Many2one('hr.employee', string='Employee', default=_get_employee_id, required=1)
    eos_config_id = fields.Many2one('ebs.hr.eos.config', string='Eos Config', ondelete='restrict')
    request_date = fields.Date(string='Request Date', default=datetime.today(), required=True)
    joining_date = fields.Date(string='Joining Date')
    today_date = fields.Date('Today_date', default=date.today())
    amount_to_request = fields.Float(string='Amount To request')
    state = fields.Selection([('draft', 'Draft'),
                              ('submitted', 'Submitted'),
                              ('finance_approve', 'Finance Approve'),
                              ('hr_approve', 'HR Approve'), ],
                             string='Status', default='draft')
    amount_approved = fields.Float(string='Amount Approved')
    payment_date = fields.Date(string='Payment Date')
    remaining_end_of_service_amount = fields.Float(string='Gratuity Amount', readonly=1, force_save=True,
                                                   compute='compute_remaining_end_of_service_amount')
    number_of_days_worked = fields.Float(string="No. Of Days Worked")
    monthly_salary = fields.Float(string="Monthly Salary")
    partial_eos = fields.Boolean(string="Partial End of Service")

    include_unpaid = fields.Boolean(string="Include Unpaid Leaves")
    unpaid_leaves_days = fields.Float(string="Unpaid Leaves Days", readonly=1)
    daily_rate = fields.Float(string="Daily Rate", compute="compute_daily_rate")
    paid_leaves_days = fields.Float(string="Paid Leaves Days")
    unpaid_amount = fields.Float(string="Unpaid Amount", compute="compute_unpaid_leaves_amount")
    paid_leaves_amount = fields.Float(string="paid Amount", compute="compute_paid_leaves_amount")
    payslip_ids = fields.Many2many('hr.payslip', string='Payslip', domain="[('employee_id','=',employee_id)]")
    other_entitlements_ids = fields.One2many('ebs.hr.eos.other.entitlements', 'end_of_service_id',
                                             string='Other Entitlements')
    journal_entries_count = fields.Integer(compute='compute_journal_entries_count')
    eos_taken_amount = fields.Float('End of Service Taken')
    payslip_totals = fields.Float('Payslip Total', compute="payslip_totals_compute")
    net_gratuity_amount = fields.Float('Net Gratuity Amount', compute="net_gratuity_amount_compute")
    other_entitlements_amount = fields.Float('Other Entitlements Amount')
    method = fields.Selection([('default', 'Earliest Date'), ('joining', 'Joining Date'), ('contract', 'Contract Date')], string='Method', default='default')
    contract_date = fields.Date("Contract Date", compute="get_employee_first_contract_date")

    @api.depends('employee_id')
    def get_employee_first_contract_date(self):
        for rec in self:
            if rec.employee_id:
                first_contract = self.env['hr.contract'].search(
                    [('employee_id', '=', rec.employee_id.id), ('state', 'in', ['open', 'close'])],
                    order='date_start asc', limit=1)
                rec.contract_date = first_contract.date_start
            else:
                rec.contract_date = False

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Can Not Delete Record Which Is Not In Draft State.'))
        return super(AdditionalElements, self).unlink()

    @api.model
    def create(self, vals):
        resign_eos_id = self.env['ebs.mod.end.of.service.payment.request'].search(
            [('employee_id', '=', vals.get('employee_id')), ('partial_eos', '=', False)])
        if resign_eos_id:
            raise UserError(_('Not Eligibal To Take Gratuity.'))
        eos_config_id = self.env['ebs.hr.eos.config'].browse(vals.get('eos_config_id'))
        if float(vals.get('number_of_days_worked')) / 365 < eos_config_id.eligible_after_years:
            raise UserError(_('Not Eligibal To Take Gratuity.'))
        return super(AdditionalElements, self).create(vals)

    def write(self, vals):
        if vals.get('eos_config_id'):
            eos_config_id = self.env['ebs.hr.eos.config'].browse(vals.get('eos_config_id'))
        else:
            eos_config_id = self.eos_config_id
        if vals.get('number_of_days_worked'):
            number_of_days_worked = float(vals.get('number_of_days_worked'))
        else:
            number_of_days_worked = self.number_of_days_worked
        if (number_of_days_worked / 365) < eos_config_id.eligible_after_years:
            raise UserError(_('Not Eligibal To Take Gratuity.'))
        return super(AdditionalElements, self).write(vals)

    def get_eos_gratuity(self, payslip):
        if payslip:

            eos_service = self.env['ebs.mod.end.of.service.payment.request'].search(
                [('employee_id', '=', payslip.employee_id), ('payment_date', '>=', payslip.date_from),
                 ('payment_date', '<=', payslip.date_to), ('state', '=', 'hr_approve')])
            if eos_service:
                return eos_service.net_gratuity_amount
            else:
                return 0.0

    def get_eos_paid_leaves(self, payslip):
        if payslip:

            eos_service = self.env['ebs.mod.end.of.service.payment.request'].search(
                [('employee_id', '=', payslip.employee_id), ('payment_date', '>=', payslip.date_from),
                 ('payment_date', '<=', payslip.date_to),
                 ('state', '=', 'hr_approve')])
            if eos_service:
                return eos_service.paid_leaves_amount
            else:
                return 0.0

    def get_eos_other_entitlements(self, payslip, type, is_ded):
        if payslip:
            eos_service = self.env['ebs.mod.end.of.service.payment.request'].search(
                [('employee_id', '=', payslip.employee_id), ('payment_date', '>=', payslip.date_from),
                 ('payment_date', '<=', payslip.date_to),
                 ('state', '=', 'hr_approve')])
            if eos_service:
                other_entitlements = eos_service.other_entitlements_ids.filtered(lambda o: o.type.id == int(type))
                if other_entitlements:
                    total = sum(other_entitlements.mapped('amount'))
                    if is_ded == 'True':
                        total = total * -1
                    return total
                else:
                    return 0

    @api.depends('remaining_end_of_service_amount', 'eos_taken_amount')
    def net_gratuity_amount_compute(self):
        for rec in self:
            rec.net_gratuity_amount = rec.remaining_end_of_service_amount - rec.eos_taken_amount

    @api.depends('payslip_ids')
    def payslip_totals_compute(self):
        for rec in self:
            payslip_amount_list = []
            for record in rec.payslip_ids:
                payslip_amount_list.append(record.line_ids.filtered(lambda o: o.code == 'NET').total)
            rec.payslip_totals = round(sum(payslip_amount_list), 2)

    def compute_journal_entries_count(self):
        for record in self:
            record.journal_entries_count = self.env['account.move'].search_count(
                [('service_payment_id', '=', self.id)])

    def get_journal_entries(self):
        action = self.env.ref('account.action_move_journal_line').read()[0]
        res_id = self.env['account.move'].search(
            [('service_payment_id', '=', self.id)], limit=1)
        action['context'] = {
            'create': 0,
            'edit': 0,
        }
        action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
        action['view_mode'] = 'form'
        # action['domain'] = [('id', '=', res_id.id)]
        action['res_id'] = res_id.id
        return action

    net_payment = fields.Float(string="Net Payment", compute="compute_net_payment")

    @api.depends('employee_id', 'eos_config_id', 'method')
    def compute_remaining_end_of_service_amount(self):
        for rec in self:
            first_contract = self.env['hr.contract'].search(
                [('employee_id', '=', rec.employee_id.id), ('state', 'in', ['open', 'close'])],
                order='date_start asc', limit=1)
            if rec.eos_config_id:
                if rec.include_unpaid:
                    rec.remaining_end_of_service_amount = round(
                        rec.eos_config_id.working_days + rec.unpaid_leaves_days / 365 * (
                                round(first_contract.wage,
                                      2) * rec.number_of_days_worked) / rec.eos_config_id.salary_days, 2)
                else:
                    # rec.remaining_end_of_service_amount = round(rec.eos_config_id.working_days / 365 * (
                    #         round(first_contract.wage, 2) * rec.number_of_days_worked) / rec.eos_config_id.salary_days,
                    #                                             2)
                    if rec.method == 'default' and rec.employee_id.joining_date and first_contract.date_start:
                        if rec.employee_id.joining_date > first_contract.date_start:
                            start_date = rec.employee_id.joining_date
                        else:
                            start_date = first_contract.date_start
                    elif rec.method == 'joining' and rec.employee_id.joining_date:
                        start_date = rec.employee_id.joining_date
                    elif rec.method == 'contract' and first_contract.date_start:
                        start_date = first_contract.date_start
                    else:
                        start_date = False
                    rec.remaining_end_of_service_amount = rec.employee_id.calculate_remaining_amount_eos(rec.employee_id, rec.request_date, rec.eos_taken_amount, start_date)
            else:
                rec.remaining_end_of_service_amount = False

    @api.depends('payslip_ids', 'remaining_end_of_service_amount', 'other_entitlements_ids', 'paid_leaves_amount')
    def compute_net_payment(self):
        for rec in self:
            payslip_amount_list = []
            if rec.payslip_ids:
                for record in rec.payslip_ids:
                    payslip_amount_list.append(record.line_ids.filtered(lambda o: o.code == 'NET').total)
            rec.net_payment = round(sum(payslip_amount_list) + sum(rec.other_entitlements_ids.mapped(
                'amount')) + rec.net_gratuity_amount + rec.paid_leaves_amount)

    # @api.onchange('payslip_ids')
    # def onchange_payslip_ids(self):
    #     for rec in self:
    #         payslip_amount_list = []
    #         for record in rec.payslip_ids:
    #             payslip_amount_list.append(record.line_ids.filtered(lambda o: o.code == 'NET').total)
    #         rec.payslip_totals = sum(payslip_amount_list)

    @api.onchange('other_entitlements_ids')
    def onchange_other_entitlements_ids(self):
        for rec in self:
            rec.other_entitlements_amount = round(sum(rec.other_entitlements_ids.mapped('amount')), 2)

    @api.depends('eos_config_id', 'employee_id')
    def compute_daily_rate(self):
        for rec in self:
            first_contract = self.env['hr.contract'].search(
                [('employee_id', '=', rec.employee_id.id), ('state', 'in', ['open', 'close'])],
                order='date_start asc', limit=1)
            if first_contract and rec.eos_config_id.salary_days > 0:
                rec.daily_rate = round(first_contract.wage, 2) / rec.eos_config_id.salary_days
            else:
                rec.daily_rate = False

    @api.depends('paid_leaves_days', 'daily_rate')
    def compute_paid_leaves_amount(self):
        for rec in self:
            rec.paid_leaves_amount = rec.paid_leaves_days * round(rec.daily_rate, 2)

    @api.depends('unpaid_leaves_days', 'daily_rate')
    def compute_unpaid_leaves_amount(self):
        for rec in self:
            first_contract = self.env['hr.contract'].search(
                [('employee_id', '=', rec.employee_id.id), ('state', 'in', ['open', 'close'])],
                order='date_start asc', limit=1)
            if first_contract and rec.unpaid_leaves_days > 0:
                rec.unpaid_amount = rec.unpaid_leaves_days * round(
                    first_contract.wage, ) / rec.eos_config_id.salary_days
            else:
                rec.unpaid_amount = False

    @api.onchange('partial_eos', 'eos_config_id', 'employee_id', 'request_date')
    def get_partial_eos(self):
        for rec in self:
            if rec.partial_eos:
                rec.paid_leaves_days = 0
            else:
                if rec.eos_config_id and rec.employee_id and rec.request_date:
                    working_years = rec.number_of_days_worked/365
                    notice_period_months = rec.eos_config_id.notice_period_ids.filtered(lambda o: o.from_year <= working_years and o.to_year >= working_years).notice_period_months
                    leaving_date = rec.request_date + relativedelta(months=notice_period_months)
                    paid_leaves_type_ids = self.env['hr.leave.type'].search([('is_paid', '=', True), ('validity_start', '<=', self.request_date), ('validity_stop', '>=', self.request_date)])
                    mapped_days = paid_leaves_type_ids.get_employees_days(self.employee_id.ids)
                    leave_days = mapped_days[self.employee_id.id]
                    for leave_type in paid_leaves_type_ids:
                        leave_days[leave_type.id].update({'allocated_per_month': leave_type.allocated_per_month})
                    total_remaining_leaves = 0.0
                    total_allocated_per_month = 0.0
                    remaining_month_leaves = 0.0
                    total_leaves_taken = 0.0
                    if leaving_date.day == 31:
                        days_in_request_month = 30
                    else:
                        days_in_request_month = leaving_date.day
                    if leaving_date.year > rec.request_date.year:
                        for value in leave_days.values():
                            total_days = (leaving_date.month - 1) * 30
                            remaining_leave = math.ceil(((days_in_request_month + total_days) * value['allocated_per_month']) / 30)
                            total_leaves_taken += value['leaves_taken']
                            total_allocated_per_month += (12 * value['allocated_per_month'])
                            total_remaining_leaves += remaining_leave
                    else:
                        for value in leave_days.values():
                            remaining_month_leaves += (12 - (leaving_date.month)) * value['allocated_per_month']
                            remaining_leave = math.ceil((days_in_request_month * value['allocated_per_month']) / 30)
                            total_leaves_taken += value['leaves_taken']
                            total_allocated_per_month += (12 * value['allocated_per_month'])
                            total_remaining_leaves += remaining_leave
                    rec.paid_leaves_days = total_allocated_per_month - remaining_month_leaves + total_remaining_leaves - total_leaves_taken
                else:
                    rec.paid_leaves_days = 0

    @api.onchange('request_date')
    def get_request_date(self):
        for rec in self:
            rec.eos_config_id = self.env['ebs.hr.eos.config'].search(
                [('start_date', '<=', rec.request_date), ('end_date', '>=', rec.request_date)], limit=1).id

    @api.onchange('employee_id', 'method')
    def compute_employee_details(self):
        if self.method in ['default', 'joining'] and self.employee_id and not self.employee_id.joining_date:
            raise UserError(_('Please Fill Joining Date In Employee.'))
        employee_end_of_service_request = self.env['ebs.mod.end.of.service.payment.request'].search(
            [('employee_id', '=', self.employee_id.id)],
            order='request_date desc', limit=1)
        first_contract = self.env['hr.contract'].search(
            [('employee_id', '=', self.employee_id.id), ('state', 'in', ['open', 'close'])],
            order='date_start asc', limit=1)
        if self.employee_id:
            self.joining_date = self.employee_id.joining_date
            if self.method == 'default':
                if self.employee_id.joining_date > first_contract.date_start:
                    joining_date = self.employee_id.joining_date
                else:
                    joining_date = first_contract.date_start
            elif self.method == 'joining':
                joining_date = self.employee_id.joining_date
            elif self.method == 'contract':
                joining_date = first_contract.date_start
            else:
                joining_date = False
            self.number_of_days_worked = (self.today_date - joining_date).days if joining_date else 0
            self.monthly_salary = round(first_contract.wage, 2) if first_contract else 0
            self.eos_taken_amount = self.employee_id.eos_taken_amount
        else:
            self.joining_date = False
            self.number_of_days_worked = False
            self.monthly_salary = False
            self.eos_taken_amount = False

    @api.onchange('employee_id')
    def compute_end_of_service(self):
        for rec in self:
            if rec.joining_date:
                leaves = self.env['hr.leave'].search(
                    [('employee_id', '=', rec.employee_id.id), ('request_date_from', '>=', rec.joining_date),
                     ('request_date_to', '<=', rec.today_date)])
                unpaid_leave = leaves.filtered(lambda o: o.holiday_status_id.is_unpaid == True)
                self.unpaid_leaves_days = sum(unpaid_leave.mapped('number_of_days'))
            # if rec.employee_id:
            #     rec.remaining_end_of_service_amount = rec.employee_id.calculate_remaining_amount_eos(rec.employee_id,
            #                                                                                          rec.request_date)
            # else:
            #     rec.remaining_end_of_service_amount = 0

    def submit(self):
        self.state = 'submitted'

    def manager_approve(self):
        self.state = 'finance_approve'

    def hr_approve(self):
        self.state = 'hr_approve'

    def reset_to_draft(self):
        self.state = 'draft'

    def journal_entry(self):

        for rec in self:
            journal = self.env['account.move'].with_context(force_company=rec.employee_id.company_id.id,
                                                            type='out_invoice')._get_default_journal()
            if not journal:
                raise UserError(_('Please define an accounting sales journal for the company %s (%s).') % (
                    rec.employee_id.company_id.name, rec.employee_id.company_id.id))
            total_negative = 0.0
            total_positive = 0.0
            account_amount_negative = []
            account_amount_positive = []
            if rec.other_entitlements_ids:
                for record in rec.other_entitlements_ids:
                    if record.amount < 0:
                        total_negative += round(abs(record.amount), 2)
                        account_amount_negative.append([record.type.account_id, round(record.amount, 2)])
                    if record.amount > 0:
                        total_positive += round(record.amount, 2)
                        account_amount_positive.append([record.type.account_id, round(record.amount, 2)])
            line_ids = []
            if account_amount_negative:
                for record in account_amount_negative:
                    line_ids.append((0, 0, {
                        'account_id': record[0].id,
                        'partner_id': rec.employee_id.user_partner_id.id,
                        'name': 'Deduction',
                        'credit': round(abs(record[1]), 2),
                        'debit': 0,
                    }))
            if account_amount_positive:
                for record in account_amount_positive:
                    line_ids.append((0, 0, {
                        'account_id': record[0].id,
                        'partner_id': rec.employee_id.user_partner_id.id,
                        'debit': round(abs(record[1]), 2),
                        'name': 'Addition',
                        'credit': 0,
                    }))
            if rec.eos_config_id.gratuity_account_id:
                line_ids.append((0, 0, {
                    'account_id': rec.eos_config_id.gratuity_account_id.id,
                    'partner_id': rec.employee_id.user_partner_id.id,
                    'debit': round(rec.remaining_end_of_service_amount, 2),
                    'name': 'Gratuity',
                    'credit': 0,
                }))
            if not rec.partial_eos:
                if rec.eos_config_id.paid_leave_account_id:
                    line_ids.append((0, 0, {
                        'account_id': rec.eos_config_id.paid_leave_account_id.id,
                        'partner_id': rec.employee_id.user_partner_id.id,
                        'credit': 0,
                        'name': 'Paid Leaves Amount',
                        'debit': round(rec.paid_leaves_amount, 2),
                    }))
            total_debit = round(
                round(rec.remaining_end_of_service_amount, 2) + round(rec.paid_leaves_amount, 2) + round(total_positive,
                                                                                                         2), 2)
            closing_account_amount = round(round(total_debit, 2) - round(total_negative, 2), 2)
            if rec.eos_config_id.closing_account_id:
                line_ids.append((0, 0, {
                    'account_id': rec.eos_config_id.closing_account_id.id,
                    'partner_id': rec.employee_id.user_partner_id.id,
                    'credit': round(closing_account_amount, 2),
                    'debit': 0,
                }))
            self.env['account.move'].create({
                'service_payment_id': rec.id,
                'ref': 'Gratuity - ' + rec.employee_id.name + ' - ' + rec.joining_date.strftime("%m/%d/%Y"),
                'date': rec.today_date,
                'journal_id': journal.id,
                'type': 'entry',
                'company_id': rec.employee_id.company_id.id,
                'line_ids': line_ids
            })
