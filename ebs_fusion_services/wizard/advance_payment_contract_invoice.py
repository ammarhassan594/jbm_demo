# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError


class EbsAdvancePaymentContractInv(models.TransientModel):
    _name = "ebs.advance.payment.contract.inv"
    _description = "Ebs Advance Payment Contract Invoice"

    def default_fees(self):
        order_id = self.env['ebs.crm.proposal'].browse([self.env.context.get('active_id')])
        fee_ids = []
        for fee in order_id.contract_fees_ids:
            fee.amount_to_be_paid = fee.remaining_amount
            fee.invoice_date = fee.next_invoice_date
            if fee.remaining_amount > 0:
                fee_ids.append(fee.id)
        if not len(fee_ids) > 0:
            raise ValidationError("There are no fees left to be invoiced")
        return fee_ids

    def default_fos(self):
        order_id = self.env['ebs.crm.proposal'].browse([self.env.context.get('active_id')])
        return order_id.fos

    contract_fee_ids = fields.Many2many('ebs.contract.proposal.fees', 'advance_contract_fees_rel', default=default_fees)
    fos = fields.Boolean(default=default_fos)

    @api.onchange('contract_fee_ids')
    def onchange_fees(self):
        if self.contract_fee_ids:
            for fee in self.contract_fee_ids:
                if fee.amount_to_be_paid > fee.remaining_amount:
                    raise ValidationError("The fees to be paid cannot be greater than the remaining fees")

    def confirm_button(self):
        order_id = self.env['ebs.crm.proposal'].browse([self.env.context.get('active_id')])
        flag = True
        for fee in self.contract_fee_ids:
            if fee.amount > 0:
                flag = False
        if flag:
            raise ValidationError("Please enter amount to be paid for any fee.")
        order_id.generate_onetime_invoice(self.contract_fee_ids)

