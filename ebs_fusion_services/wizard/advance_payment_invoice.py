# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from datetime import date


class EbsAdvancePaymentInv(models.TransientModel):
    _name = "ebs.advance.payment.inv"
    _description = "Ebs Advance Payment Invoice"

    @api.model
    def default_get(self, field_list):
        result = super(EbsAdvancePaymentInv, self).default_get(field_list)
        order_id = self.env[self.env.context.get('active_model')].search([('id', 'in', self.env.context.get('active_ids'))])
        partner_ids = []
        for order in order_id:
            if order.client_id:
                partner_ids.append(order.client_id)
            elif order.partner_id:
                partner_ids.append(order.partner_id)
        if len(set(partner_ids)) > 1:
            raise UserError("Please select service orders with the same Client to generate an invoice.")

        additional = 0
        additional_invoiced = 0
        result['remaining_govt'] = 0
        result['govt_fees'] = 0
        result['fusion_fees'] = 0
        result['remaining_fusion'] = 0
        result['remaining_additional'] = 0
        result['additional_fees'] = 0
        result['remaining_payments'] = 0
        result['discount'] = 0
        for order in order_id:
            for add_exp in order.additional_expenses:
                if not add_exp.is_invoiced:
                    additional += add_exp.amount
                    additional_invoiced += add_exp.amount_invoiced
            if self._context.get('proforma'):
                result['remaining_govt'] += order.govt_fees - order.govt_payment
                result['govt_fees'] += order.govt_fees - order.govt_payment
                result['fusion_fees'] += order.fusion_fees - order.fusion_payment
                result['remaining_fusion'] += order.fusion_fees - order.fusion_payment
            if self._context.get('invoices'):
                result['remaining_govt'] += order.govt_fees - order.govt_invoiced
                result['govt_fees'] += order.govt_fees - order.govt_invoiced
                result['remaining_fusion'] += order.fusion_fees - order.fusion_invoiced
                result['fusion_fees'] += order.fusion_fees - order.fusion_invoiced
                result['remaining_additional'] = additional - additional_invoiced
                result['additional_fees'] = additional - additional_invoiced
                result['discount'] += order.discount
                result['remaining_payments'] += sum(order.workflow_payment_ids.filtered(lambda l: not l.is_invoiced).mapped('amount'))
        if result['remaining_govt'] <= 0 and result['remaining_fusion'] <= 0 and \
            result['remaining_payments'] <= 0 and result['remaining_additional'] <= 0:
            raise UserError('There are no fees left to be invoiced!')

        return result


    remaining_govt = fields.Float('Remaining Govt. Fees',readonly=1)
    remaining_fusion = fields.Float('Remaining Main Company Fees',readonly=1)
    remaining_additional = fields.Float('Remaining Additional Fees',readonly=1)
    remaining_payments = fields.Float('Remaining Payments', readonly=1)
    govt_fees = fields.Float('Govt. Fees Payment')
    govt_analytic_account = fields.Many2one('account.analytic.account', string='Govt. Analytic Account')
    fusion_analytic_account = fields.Many2one('account.analytic.account', string='Fusion Analytic Account')
    additional_analytic_account = fields.Many2one('account.analytic.account', string='Additional Analytic Account')
    fusion_fees = fields.Float('Main Company Fees Payment')
    additional_fees = fields.Float('Additional Fees Payment')
    discount = fields.Float('Discount')
    invoice_date = fields.Date(string="Invoice Date", default=date.today())

    @api.onchange('govt_fees','fusion_fees','additional_fees')
    def onchange_fees(self):
        if not self._context.get('proforma'):
            if self.govt_fees > self.remaining_govt or self.fusion_fees > self.remaining_fusion or self.additional_fees > self.remaining_additional:
                raise ValidationError("The fees to be paid cannot be greater than the remaining fees")


    def confirm_button(self):
        if not self._context.get('full'):
            order_id = self.env[self.env.context.get('active_model')].browse([self.env.context.get('active_id')])
            analytic_account = {'govt_acc': self.govt_analytic_account.id,
                                'fusion_acc': self.fusion_analytic_account.id,
                                'additional_acc': self.additional_analytic_account.id}
            order_id.generate_invoice(self.govt_fees, self.fusion_fees, self.additional_fees, self.discount, analytic_account, self.invoice_date)
        else:
            analytic_account = {'govt_acc': False,
                                'fusion_acc': False,
                                'additional_acc': False}
            order_ids = self.env[self.env.context.get('active_model')].search([('id', 'in', self.env.context.get('active_ids'))])
            company = self.env.user.company_id
            journal = self.env['account.move'].sudo().with_context(force_company=company.id,
                                                                   type='out_invoice')._get_default_journal()
            if not journal:
                raise UserError(_('Please define an accounting sales journal for the company %s (%s).') % (
                    self.company_id.name, self.company_id.id))
            if order_ids[0].partner_id:
                partner_invoice = order_ids[0].partner_id
            else:
                partner_invoice = order_ids[0].client_id
            if not partner_invoice:
                raise UserError(_('You have to select an invoice address in the service form.'))

            invoice_vals = {
                'type': 'out_invoice',
                'partner_id': partner_invoice.id,
                'invoice_origin': ", ".join(order_ids.mapped('name')),

                'invoice_line_ids': [],
                'invoice_date': self.invoice_date,
            }
            invoice_line_vals = []
            for order in order_ids:
                additional_amount = sum(order.additional_expenses.mapped('amount'))
                invoice_line_vals.extend(order.get_invoice_line_vals(order.govt_fees, order.fusion_fees, additional_amount, self.discount, analytic_account, self.invoice_date))
            invoice_vals['invoice_line_ids'] = invoice_line_vals

            if not len(invoice_vals['invoice_line_ids']) == 0:
                self.env['account.move'].with_context(default_move_type='out_invoice').sudo().create(invoice_vals)
            else:
                raise UserError(_('No invoiceable lines remaining'))


    def confirm_proforma_button(self):
        if not self._context.get('full'):
            order_id = self.env[self.env.context.get('active_model')].browse([self.env.context.get('active_id')])

            order_id.generate_payments(self.govt_fees, self.fusion_fees, self.invoice_date)
        else:
            order_ids = self.env[self.env.context.get('active_model')].search(
                [('id', 'in', self.env.context.get('active_ids'))])
            company = self.env.user.company_id
            journal = self.env['account.move'].sudo().with_context(force_company=company.id,
                                                                   type='out_invoice')._get_default_journal()
            if not journal:
                raise UserError(_('Please define an accounting sales journal for the company %s (%s).') % (
                    self.company_id.name, self.company_id.id))
            if order_ids[0].partner_id:
                partner_invoice = order_ids[0].partner_id
            else:
                partner_invoice = order_ids[0].client_id
            if not partner_invoice:
                raise UserError(_('You have to select an invoice address in the service form.'))

            payment_vals = {
                'payment_type': 'inbound',
                'payment_method_id': 1,
                'partner_type': 'customer',
                'is_proforma': True,

                'amount': self.govt_fees + self.fusion_fees,
                'partner_id': partner_invoice.id,
                'date': self.invoice_date,
                'journal_id': journal.id,
                'proforma_ids': [],
                'ref': ", ".join(order_ids.mapped('name')),
            }
            payment_line_vals = []
            for order in order_ids:
                payment_line_vals.extend(order.get_payment_line_vals(order.govt_fees, order.fusion_fees))
                order.write({'govt_payment': order.govt_payment + order.govt_fees,
                            'fusion_payment': order.fusion_payment + order.fusion_fees})

            payment_vals['proforma_ids'] = payment_line_vals
            if not len(payment_vals['proforma_ids']) == 0:
                self.env['account.payment'].sudo().create(payment_vals)
            else:
                raise UserError(_('No invoiceable lines remaining'))
