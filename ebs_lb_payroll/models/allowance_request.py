# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date
from dateutil.relativedelta import relativedelta
from calendar import monthrange


class AllowanceRequest(models.Model):
    _name = 'ebs.payroll.allowance.request'
    _description = 'Allowance Request'
    _order = "request_date desc"

    name = fields.Char(readonly=True, required=True, copy=False, default='New')
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        required=True)
    company_id = fields.Many2one(related='employee_id.company_id', string='Company')

    request_type = fields.Many2one(
        comodel_name='ebs.payroll.allowance.request.type',
        string='Type',
        required=True)
    amount = fields.Float(
        string='Amount',
        required=True)
    request_date = fields.Date(
        string='Request Date',
        required=True, default=date.today())
    payment_date = fields.Date(
        string='Payment Date',
        required=False)
    amortization_start_date = fields.Date(
        string='Amortization Start Date',
        required=False)
    number_of_month = fields.Integer(
        string='Number of Month',
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

    lines_ids = fields.One2many(
        comodel_name='ebs.payroll.allowance.request.lines',
        inverse_name='parent_id',
        string='Lines',
        required=False)
    is_date_compute = fields.Boolean('Is Date Compute')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('ebs.payroll.allowance.request') or 'New'

        result = super(AllowanceRequest, self).create(vals)
        return result

    def submit_request(self):
        self.state = 'submit'

    def compute_date_lines(self):
        if not self.payment_date:
            raise ValidationError(_("Missing Payment Date"))
        if not self.amortization_start_date:
            raise ValidationError(_("Missing amortization date"))
        if not self.number_of_month:
            raise ValidationError(_("Missing number of month"))

        for line in self.lines_ids:
            line.unlink()
        divide_by = round(self.number_of_month * (360 / 12))
        total = 0.0
        for x in range(self.number_of_month):
            line_date = self.amortization_start_date + relativedelta(months=x)
            # days = monthrange(line_date.year, line_date.month)[1]
            days = 30
            if x != (self.number_of_month - 1):
                payment = (self.amount / divide_by) * days
                total += payment
            else:
                payment = self.amount - total

            self.env['ebs.payroll.allowance.request.lines'].create({
                'parent_id': self.id,
                'date': line_date,
                'amount': payment
            })
        self.is_date_compute = True

    def accept_request(self):
        if self.amount < 0:
            raise ValidationError("Amount can not be in minus")
        if self.amount != sum(self.lines_ids.mapped('amount')):
            raise ValidationError("Total monthly divided amount and total amount must be same.")
        self.state = 'approved'

    def reject_request(self):
        self.state = 'reject'

    def draft_request(self):
        self.state = 'draft'

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError("Only draft records can be deleted")
        return super(AllowanceRequest, self).unlink()


class AllowanceRequestlines(models.Model):
    _name = 'ebs.payroll.allowance.request.lines'
    _description = 'Allowance Request lines'

    parent_id = fields.Many2one(
        comodel_name='ebs.payroll.allowance.request',
        string='Request',
        required=False)
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        required=False, related='parent_id.employee_id')

    parent_type = fields.Many2one(
        comodel_name='ebs.payroll.allowance.request.type',
        string='Type',
        required=False, related='parent_id.request_type')

    parent_state = fields.Selection(
        string='State',
        selection=[('draft', 'Draft'),
                   ('submit', 'Submitted'),
                   ('approved', 'Approved'),
                   ('reject', 'Rejected'),
                   ],
        required=False, related='parent_id.state')

    date = fields.Date(
        string='Date',
        required=False)

    amount = fields.Float(
        string='Amount',
        required=False)
