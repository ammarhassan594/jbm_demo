# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class PayrollPaymentWiz(models.TransientModel):
    _name = 'ebs.payroll.payment.wiz'
    _description = 'Generate payment from payroll'

    payslip_ids = fields.Many2many('hr.payslip', string='Orders')
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal',
        required=True)
    payment_date = fields.Date(
        string='Date',
        required=True)
    payment_method_id = fields.Many2one(
        comodel_name='account.payment.method',
        string='Payment Method',
        required=True)

    @api.model
    def default_get(self, fields):
        res = super(PayrollPaymentWiz, self).default_get(fields)
        res.update({'payslip_ids': self._context.get('active_ids')})
        return res

    def generate_payments(self):
        for rec in self.payslip_ids:
            if not rec.employee_id.user_partner_id:
                raise ValidationError('Please link partner for %s '%rec.employee_id.name)
            if rec.state == 'done':
                generate = False
                if not rec.payment_id:
                    generate = True
                else:
                    if rec.payment_id.state == 'cancelled':
                        generate = True
                    else:
                        generate = False
                if generate:
                    net_amount = 0
                    for line in rec.line_ids:
                        if line.code == 'NET':
                            net_amount = line.amount
                    payment = self.env['account.payment'].create({
                        'company_id': rec.company_id.id,
                        'state': 'draft',
                        'payment_type': 'outbound',
                        'journal_id': self.journal_id.id,
                        'date': self.payment_date,
                        'partner_id': rec.employee_id.user_partner_id.id,
                        'partner_type': 'supplier',
                        'is_employee_payment': True,
                        'amount': net_amount,
                        'payment_method_id': self.payment_method_id.id
                    })
                    rec.write({
                        'payment_id': payment.id
                    })
