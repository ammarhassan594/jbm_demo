# -*- coding: utf-8 -*-

from odoo import models, fields, _
from dateutil.relativedelta import relativedelta


class AccountMove(models.Model):
    _inherit = 'account.move'

    prop_id = fields.Many2one('ebs.crm.proposal')
    monthly_generated = fields.Boolean('Monthly Generated')
    service_process_id = fields.Many2one('ebs.crm.service.process')
    note = fields.Text(string='Description')

    def write(self, vals):
        for rec in self:
            res = super(AccountMove, rec).write(vals)
            if vals.get('state') == 'cancel':
                for line in rec.invoice_line_ids:
                    if line.contract_fees_id and line.exclude_from_invoice_tab == False:
                        line.check_contract_next_invoice_date()
            return res


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    proposal_line_ids = fields.One2many('ebs.crm.proposal.line', 'invoice_line_id', readonly=True, copy=False)
    service_process_id = fields.Many2one('ebs.crm.service.process', readonly=True, copy=False)
    additional_expense_id = fields.Many2one('ebs.crm.additional.expenses', readonly=True, copy=False)
    onetime_fee_line_id = fields.Many2one('ebs.crm.employee.onetime.fees', readonly=True, copy=True)
    monthly_fee_line_id = fields.Many2one('ebs.crm.employee.monthly.fees', readonly=True, copy=True)
    contract_fees_id = fields.Many2one('ebs.contract.proposal.fees', 'Contract Fees')
    workflow_payment_id = fields.Many2one('ebs.workflow.payment', string='Workflow Payment')
    govt = fields.Boolean()
    fusion = fields.Boolean()

    def unlink(self):
        for rec in self:
            if rec.move_id != 'cancel' and rec.contract_fees_id and rec.exclude_from_invoice_tab == False:
                rec.check_contract_next_invoice_date()
        return super(AccountMoveLine, self).unlink()

    def check_contract_next_invoice_date(self):
        if self.contract_fees_id.invoice_period == 'yearly':
            years = relativedelta(self.contract_fees_id.next_invoice_date,
                                  self.contract_fees_id.contract_id.start_date).years
            i = 1
            for period in range(years):
                start_date = self.contract_fees_id.contract_id.start_date + relativedelta(years=i - 1)
                end_date = self.contract_fees_id.contract_id.start_date + relativedelta(years=i)
                invoice_line_ids = self.search(
                    [('move_id.invoice_date', '>=', start_date), ('move_id.invoice_date', '<', end_date),
                     ('contract_fees_id', '=', self.contract_fees_id.id), ('move_id.state', '!=', 'cancel')]) - self
                if sum(invoice_line_ids.mapped('price_subtotal')) != self.contract_fees_id.amount:
                    self.contract_fees_id.next_invoice_date = start_date
                    break
                i += 1
        if self.contract_fees_id.invoice_period == 'monthly':
            months = relativedelta(self.contract_fees_id.next_invoice_date,
                                   self.contract_fees_id.contract_id.start_date).months
            i = 1
            for period in range(months):
                start_date = self.contract_fees_id.contract_id.start_date + relativedelta(months=i - 1)
                end_date = self.contract_fees_id.contract_id.start_date + relativedelta(months=i)
                invoice_line_ids = self.search(
                    [('move_id.invoice_date', '>=', start_date), ('move_id.invoice_date', '<', end_date),
                     ('contract_fees_id', '=', self.contract_fees_id.id), ('move_id.state', '!=', 'cancel')]) - self
                if sum(invoice_line_ids.mapped('price_subtotal')) != self.contract_fees_id.amount:
                    self.contract_fees_id.next_invoice_date = start_date
                    break
                i += 1
