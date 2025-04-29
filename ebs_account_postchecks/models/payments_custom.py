# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PaymentsCustom(models.Model):
    _inherit = "account.payment"

    # is_bank_transfer = fields.Boolean(string='Is Bank Transfer')
    # bank_account_id = fields.Many2one('res.partner.bank', string='Bank Account')
    # parent_account_number = fields.Char(related='partner_id.parent_bank_account.acc_number')
    # account_number_ids = fields.One2many('res.partner.bank', 'partner_id', related='partner_id.bank_ids')

    is_post_dated_check = fields.Boolean(
        string='Post Dated Check',
        required=False, default=False)

    check_template_id = fields.Many2one(
        comodel_name='ebs.checks.templates',
        string='Check Template',
        required=False)

    check_date = fields.Date(
        string='Check Date',
        required=False)

    post_check_entry_id = fields.Many2one(
        comodel_name='account.move',
        string='Post Check Entry',
        required=False)

    def action_draft(self):
        super(PaymentsCustom, self).action_draft()
        if self.post_check_entry_id:
            if self.post_check_entry_id.state == 'posted':
                self.post_check_entry_id.button_draft()
            self.post_check_entry_id.with_context(force_delete=True).unlink()

    @api.onchange('payment_type')
    def change_bank_transfer(self):
        if self.payment_type == 'transfer':
            self.is_post_dated_check = False
        # self.payment_type = False
        # self.bank_account_id = ""

    def button_journal_voucher(self):
        vouchers = []
        for vitems in self.env['account.move.line'].search([('payment_id', '=', self.id)]):
            vouchers.append(vitems.move_id.id)

        for moves in self.env['account.move'].search([('related_payment_id', '=', self.id)]):
            vouchers.append(moves.id)
        return {
            'name': _('Journal Voucher'),
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', list(set(vouchers)))],
        }

    def post(self):
        for rec in self:
            if rec.new_post():
                if rec.is_post_dated_check:
                    journal_entry = self.env['account.move'].create({
                        'name': '/',
                        'journal_id': rec.journal_id.id,
                        'date': rec.check_date,
                        'related_payment_id': rec.id
                    })
                    if rec.payment_type == 'outbound':
                        self.env['account.move.line'].create({
                            'move_id': journal_entry.id,
                            'account_id': rec.check_template_id.account_for_post_checks.id,
                            'name': rec.name,
                            'debit': 0.0,
                            'credit': rec.amount
                        })
                        self.env['account.move.line'].create({
                            'move_id': journal_entry.id,
                            'account_id': rec.journal_id.default_debit_account_id.id,
                            'name': rec.name,
                            'debit': rec.amount,
                            'credit': 0.0
                        })
                    if rec.payment_type == 'inbound':
                        self.env['account.move.line'].create({
                            'move_id': journal_entry.id,
                            'account_id': rec.check_template_id.account_for_post_checks.id,
                            'name': rec.name,
                            'debit': rec.amount,
                            'credit': 0.0
                        })
                        self.env['account.move.line'].create({
                            'move_id': journal_entry.id,
                            'account_id': rec.journal_id.default_debit_account_id.id,
                            'name': rec.name,
                            'debit': 0.0,
                            'credit': rec.amount
                        })
                rec.post_check_entry_id = journal_entry.id
        return True

    def new_post(self):
        """ Create the journal items for the payment and update the payment's state to 'posted'.
            A journal entry is created containing an item in the source liquidity account (selected journal's default_debit or default_credit)
            and another in the destination reconcilable account (see _compute_destination_account_id).
            If invoice_ids is not empty, there will be one reconcilable move line per invoice to reconcile with.
            If the payment is a transfer, a second journal entry is created in the destination journal to receive money from the transfer account.
        """
        AccountMove = self.env['account.move'].with_context(default_type='entry')
        for rec in self:

            if rec.state != 'draft':
                raise UserError(_("Only a draft payment can be posted."))

            if any(inv.state != 'posted' for inv in rec.invoice_ids):
                raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))

            # keep the name in case of a payment reset to draft
            if not rec.name:
                # Use the right sequence to set the name
                if rec.payment_type == 'transfer':
                    sequence_code = 'account.payment.transfer'
                else:
                    if rec.partner_type == 'customer':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.customer.invoice'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.customer.refund'
                    if rec.partner_type == 'supplier':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.supplier.refund'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.supplier.invoice'
                rec.name = self.env['ir.sequence'].next_by_code(sequence_code, sequence_date=rec.payment_date)
                if not rec.name and rec.payment_type != 'transfer':
                    raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))

            moves = AccountMove.create(rec._prepare_payment_moves())
            for move in moves:
                move.related_payment_id = rec.id
            if rec.is_post_dated_check:
                for move in moves:
                    move.date = rec.check_date
                    for line in move.line_ids:
                        line.date_maturity = rec.check_date
            else:
                moves.filtered(lambda move: move.journal_id.post_at != 'bank_rec').post()

            # Update the state / move before performing any reconciliation.
            move_name = self._get_move_name_transfer_separator().join(moves.mapped('name'))
            rec.write({'state': 'posted', 'move_name': move_name})

            if rec.payment_type in ('inbound', 'outbound'):
                # ==== 'inbound' / 'outbound' ====
                if rec.invoice_ids:
                    (moves[0] + rec.invoice_ids).line_ids \
                        .filtered(lambda line: not line.reconciled and line.account_id == rec.destination_account_id) \
                        .reconcile()
            elif rec.payment_type == 'transfer':
                # ==== 'transfer' ====
                moves.mapped('line_ids') \
                    .filtered(lambda line: line.account_id == rec.company_id.transfer_account_id) \
                    .reconcile()

        return True

    # def custom_print_check(self):
    #     template_id = self.check_template_id.template.xml_id
    #     return self.env.ref(template_id).report_action(self)
    #     # raise ValidationError(_("Template Missing"))
    #
    # def custom_bank_transfer(self):
    #     return self.env.ref("ebs_account_postchecks.bank_transfer_action").report_action(self)
    #
    # def next_check_sequence(self):
    #     self.check_template_id.get_check_sequence()
