# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date, datetime
from dateutil.relativedelta import relativedelta


# from calendar import monthrange


class TicketAllowanceRequest(models.Model):
    _name = 'ebs.payroll.ticket.allowance.request'
    _description = 'Ticket Allowance Request'
    _order = "request_date desc"

    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        required=True)
    contract_id = fields.Many2one(
        comodel_name='hr.contract',
        string='Contract',
        required=True)
    remaining_amount = fields.Float(
        string='Remaining Amount',
        required=False,

    )
    remaining_amount2 = fields.Float(
        string='Remaining Amount',
        required=False,
        readonly=True,
    )
    amount = fields.Float(
        string='Amount',
        )
    approved_amount = fields.Float(
        string='Approved Amount',
        required=False)
    request_date = fields.Date(
        string='Request Date',
        required=True, default=date.today())
    payment_date = fields.Date(
        string='Payment Date',
        required=False)
    description = fields.Text(
        string="Description",
        required=False)
    state = fields.Selection(
        string='State',
        selection=[('draft', 'Draft'),
                   ('submit', 'Submitted'),
                   ('approved', 'Approved'),
                   ('reject', 'Rejected'),
                   ],
        required=False, default='draft')

    @api.onchange('contract_id')
    def _contract_id_onchange(self):
        if self.contract_id and self.employee_id and self.request_date:
            remaining_amount = self._get_remaining_amount()
            self.remaining_amount = remaining_amount
            self.remaining_amount2 = remaining_amount
            first_contract = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)],
                                                        order='date_start', limit=1)
            eligible_or_not = False
            if first_contract:
                eligible_or_not = relativedelta(self.request_date,
                                                first_contract.date_start).years >= self.contract_id.eligible_after
            date_difference = self.request_date - relativedelta(years=self.contract_id.eligible_every_year)
            if eligible_or_not:
                # past_request = self.env['ebs.payroll.ticket.allowance.request'].search(
                #     [('state', '=', 'approved'),('employee_id', '=', self.employee_id.id), ('contract_id', '=', self.contract_id.id),
                #      ('request_date', '>=', date_difference)], order='request_date desc', limit=1)
                # if past_request:
                if self.remaining_amount == 0:
                    self.state = 'reject'
                    self.description = 'Employee exceeded allowance limit'
            else:
                self.state = 'reject'
                self.description = 'You are not eligible, check joining date eligibility'



    def _get_remaining_amount(self):
        ticket_amount = self.contract_id.maximum_ticket_allowance
        amount_taken = 0
        start_year = date(self.request_date.year, 1, 1)
        end_year = date(self.request_date.year, 12, 31)
        request_list = self.env['ebs.payroll.ticket.allowance.request'].search([
            ('state', '=', 'approved'),
            ('employee_id', '=', self.employee_id.id),
            ('request_date', '<=', end_year),
            ('request_date', '>=', start_year)
        ])
        for request in request_list:
            amount_taken += request.approved_amount
        return ticket_amount - amount_taken

    @api.model
    def create(self, vals):
        if vals.get('remaining_amount', False):
            vals['remaining_amount2'] = vals['remaining_amount']
        res = super(TicketAllowanceRequest, self).create(vals)
        return res

    def write(self, vals):
        if vals.get('remaining_amount', False):
            vals['remaining_amount2'] = vals['remaining_amount']
        res = super(TicketAllowanceRequest, self).write(vals)
        return res

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError("Only draft records can be deleted")
        return super(TicketAllowanceRequest, self).unlink()

    def submit_request(self):
        # if self.amount > self.remaining_amount:
        #     raise ValidationError("Amount must be less or equal to remaining amount")
        self.state = 'submit'

    def accept_request(self):
        if self.approved_amount > self.remaining_amount:
            raise ValidationError("Approved amount must be less or equal to remaining amount")
        if not self.payment_date:
            raise ValidationError("Enter Payment Date")
        if self.approved_amount:
            if self.approved_amount <= 0:
                raise ValidationError("Enter a valid approved amount")
        else:
            raise ValidationError("Enter Approved Amount")

        self.state = 'approved'

    def reject_request(self):
        self.state = 'reject'

    def draft_request(self):
        self.state = 'draft'
