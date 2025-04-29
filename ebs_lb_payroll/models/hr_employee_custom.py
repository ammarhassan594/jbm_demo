# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import date, timedelta
from calendar import monthrange


class HREmployeeCustom(models.Model):
    _inherit = 'hr.employee'

    eos_amount = fields.Float(
        string='End of Service',
        compute="compute_end_of_service_amount",
        required=False)
    eos_taken_amount = fields.Float(string='End of Service Taken', compute='compute_end_of_service_taken')
    eos_ids = fields.One2many('ebs.mod.end.of.service.payment.request', 'employee_id')
    prorata_method = fields.Selection(related='partner_parent_id.prorata_method', readonly=False,
                                      string='Prorata Method')
    private_medical_insurance = fields.Float(string="Private Medical Insurance ")
    air_ticket_deposit = fields.Float(string="Air Ticket Deposit")
    workmen_compensation = fields.Float(string="Workmen's Compensation")

    wage_type = fields.Selection(
        [('monthly', 'Monthly Fixed Wage'),
         ('daily', 'Daily Wage'),
         ('hourly', 'Hourly Wage')], default='monthly',
        related='contract_id.wage_type')
    company_currency_id = fields.Many2one(related='company_id.currency_id', string='Company Currency',
                                          readonly=True, store=True,
                                          help='Utility field to express amount currency')

    emp_wage = fields.Monetary(related='contract_id.wage', currency_field='company_currency_id')
    emp_accommodation = fields.Monetary(related='contract_id.accommodation', currency_field='company_currency_id')
    emp_package = fields.Monetary(related='contract_id.package', currency_field='company_currency_id')
    emp_mobile_allowance = fields.Monetary(related='contract_id.mobile_allowance', currency_field='company_currency_id')
    emp_food_allowance = fields.Monetary(related='contract_id.food_allowance', currency_field='company_currency_id')
    emp_transport_allowance = fields.Monetary('Transport Allowance',
                                              related='contract_id.transport_allowance',
                                              currency_field='company_currency_id')
    emp_living_allowance = fields.Monetary('Living Allowance',
                                           related='contract_id.living_allowance', currency_field='company_currency_id')
    emp_other_allowance = fields.Monetary('Other Allowance', related='contract_id.other_allowance',
                                          currency_field='company_currency_id')
    emp_maximum_ticket_allowance = fields.Monetary('Maximum Ticket Allowance',
                                                   related='contract_id.maximum_ticket_allowance',
                                                   currency_field='company_currency_id')
    emp_eligible_after = fields.Integer('Eligible After', related='contract_id.eligible_after')
    emp_eligible_every_year = fields.Integer('Eligible every/year', related='contract_id.eligible_every_year')
    emp_trial_end_date = fields.Date('Trial End Date', related='contract_id.trial_date_end')

    @api.depends('partner_parent_id')
    def prorata_onchange_partner_parent_id(self):
        for rec in self:
            rec.prorata_method = rec.partner_parent_id.prorata_method

    def get_prorata(self, date):
        if self.prorata_method:
            if self.prorata_method == '30':
                return 1 / 30
            elif self.prorata_method == '365':
                return 12 / 365
            elif self.prorata_method == 'm':
                num_days = monthrange(date.year, date.month)[1]
                return 1 / num_days
        else:
            return 1 / 30

    def compute_end_of_service_amount(self):
        for rec in self:
            first_contract = self.env['hr.contract'].search(
                [('employee_id', '=', rec.id), ('state', 'in', ['open', 'close'])],
                order='date_start asc', limit=1)
            if rec.joining_date and first_contract.date_start:
                if rec.joining_date < first_contract.date_start:
                    start_date = first_contract.date_start
                else:
                    start_date = rec.joining_date
            else:
                start_date = False
            rec.sudo().eos_amount = rec.calculate_remaining_amount_eos(rec, date.today(), rec.eos_taken_amount,
                                                                       start_date)

    @api.depends('eos_ids')
    def compute_end_of_service_taken(self):
        for rec in self:
            total = 0
            for line in rec.eos_ids.filtered(lambda o: o.state == 'hr_approve'):
                total += line.net_gratuity_amount
            rec.sudo().eos_taken_amount = total

    def calculate_remaining_amount_eos(self, employee_id, request_date, eos_taken_amount, start_date):
        eos_config_id = self.env['ebs.hr.eos.config'].search(
            [('start_date', '<=', request_date), ('end_date', '>=', request_date)], limit=1)
        if eos_config_id:
            employee_end_of_service_request = self.env['ebs.mod.end.of.service.payment.request'].search(
                [('employee_id', '=', employee_id.id), ('state', '=', 'hr_approve')])
            first_contract = self.env['hr.contract'].search(
                [('employee_id', '=', employee_id.id), ('state', 'in', ['open', 'close'])],
                order='date_start asc', limit=1)
            if not first_contract:
                return 0
            elif not employee_id.joining_date:
                return 0
            elif not start_date:
                return 0
            # else:
            #     if employee_id.joining_date < first_contract.date_start:
            #         start_date = first_contract.date_start
            #     else:
            #         start_date = employee_id.joining_date

            current_contract = self.env['hr.contract'].search(
                [('employee_id', '=', employee_id.id), ('state', '=', 'open')],
                order='date_start desc', limit=1)
            if current_contract:
                basic_salary = current_contract.wage
                delta = request_date - start_date
                days = delta.days
                if days / 365 >= eos_config_id.eligible_after_years:
                    calculated_gratuity = (days / 365) * (
                                (basic_salary * eos_config_id.working_days) / eos_config_id.salary_days)
                    return round(calculated_gratuity - eos_taken_amount)
                else:
                    return 0
        else:
            return 0
