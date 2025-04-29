from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import date

class AccountMoveInherit(models.Model):
    _inherit = 'account.move'



    apply_withholding_tax = fields.Boolean()
    withholding_tax_id = fields.Many2one('account.tax', string="Withholding Tax")
    payed_by_fusion = fields.Boolean(string="Payed By Main Company")
    withholding_tax_journal_entry = fields.Many2one('account.move', string='Withholding Tax JV')
    invoice_date = fields.Date(string='Invoice/Bill Date', readonly=True, index=True, copy=False,
                               states={'draft': [('readonly', False)]},
                               default=date.today())
    opening_balance_entry = fields.Boolean(string='Opening Balance Entry')

    # def _check_balanced(self):
    #     if self._context.get('check_move_validity', True):
    #         return super(AccountMoveInherit, self)._check_balanced()
    #     else:
    #         return True

    def action_post(self):
        if self.opening_balance_entry:
            ctx = dict(self.env.context, check_move_validity=False)
            self = self.with_context(ctx)
        return super(AccountMoveInherit, self).action_post()

    def unlink(self):
        for move in self:
            if move.withholding_tax_journal_entry:
                move.withholding_tax_journal_entry.unlink()
        return super(AccountMoveInherit, self).unlink()
            

    def button_cancel(self):
        res = super(AccountMoveInherit, self).button_cancel()
        for move in self:
            if move.withholding_tax_journal_entry:
                move.withholding_tax_journal_entry.button_cancel()
        return res

    def button_draft(self):
        res = super(AccountMoveInherit, self).button_draft()
        for move in self:
            if move.withholding_tax_journal_entry:
                move.withholding_tax_journal_entry.button_draft()
        return res

    def post(self):
        res = super(AccountMoveInherit, self).post()
        for move in self:
            if move.withholding_tax_journal_entry:
                move.withholding_tax_journal_entry.write({'ref': move.name})
                move.withholding_tax_journal_entry.post()
        return res

    def generate_withholding_tax_jounal_lines(self, move_id, lines):
        withholding_tax_journal_id = move_id.company_id.withholding_tax_journal_id
        if not withholding_tax_journal_id:
            raise UserError(_('Please Add Withholding Tax Journal in Account Configuration.'))
        withholding_dict = {}
        total_tax_amount = 0
        for line in lines:
            taxes_res = line._get_price_total_and_subtotal_model(
                price_unit=line.price_unit,
                quantity=line.quantity,
                discount=line.discount,
                currency=line.currency_id,
                product=line.product_id,
                partner=line.partner_id,
                taxes=line.move_id.withholding_tax_id,
                move_type=line.move_id.move_type,
            )
            tax_amount = taxes_res.get('price_total') - taxes_res.get('price_subtotal')
            total_tax_amount += tax_amount
            if line.account_id in withholding_dict:
                withholding_dict.update({line.account_id: withholding_dict.get(line.account_id) + tax_amount})
            else:
                withholding_dict.update({line.account_id: tax_amount})

        line_vals = []
        if not move_id.payed_by_fusion:
            for account_key in withholding_dict:
                line_vals.append((0, 0, {'account_id': account_key.id,
                                         'name': 'Expense',
                                         'partner_id': move_id.partner_id.id,
                                         'credit': withholding_dict[account_key],
                                         'exclude_from_invoice_tab': True,
                                         'is_withholding_tax_entry': True}))
            line_vals.append((0, 0, {'account_id': move_id.partner_id.property_account_payable_id.id,
                                     'name': 'Payable',
                                     'debit': total_tax_amount,
                                     'partner_id': move_id.partner_id.id,
                                     'exclude_from_invoice_tab': True,
                                     'is_withholding_tax_entry': True}))
        if not move_id.withholding_tax_id.tax_group_id.property_tax_payable_account_id:
            raise UserError(_('Please Add Tax current account (payable) In Tax Group Of Withholding Tax.'))
        if not move_id.withholding_tax_id.tax_group_id.property_advance_tax_payment_account_id:
            raise UserError(_('Please Add Advance Tax payment account In Tax Group Of Withholding Tax.'))
        line_vals_2 = [
            (0, 0, {'account_id': move_id.withholding_tax_id.tax_group_id.property_advance_tax_payment_account_id.id,
                    'name': 'Withholding Tax Expense',
                    'partner_id': move_id.partner_id.id,
                    'debit': total_tax_amount,
                    'exclude_from_invoice_tab': True,
                    'is_withholding_tax_entry': True}),
            (0, 0, {'account_id': move_id.withholding_tax_id.tax_group_id.property_tax_payable_account_id.id,
                    'name': 'Withholding Tax Payable',
                    'partner_id': move_id.partner_id.id,
                    'credit': total_tax_amount,
                    'exclude_from_invoice_tab': True,
                    'is_withholding_tax_entry': True})
        ]
        move_vals = {
            'move_type': 'entry',
            'journal_id': withholding_tax_journal_id.id,
            'line_ids': line_vals + line_vals_2
        }
        if move_id.withholding_tax_journal_entry and 'write' in self._context:
            move_id.withholding_tax_journal_entry.write({'line_ids': [(2, line.id) for line in move_id.withholding_tax_journal_entry.line_ids]})
            move_id.withholding_tax_journal_entry.write(move_vals)
        else:
            withholding_tax_move_id = self.env['account.move'].create(move_vals)
            move_id.with_context({'del_line_ids': True}).write({'withholding_tax_journal_entry': withholding_tax_move_id})

    @api.model
    def create(self, vals):
        if vals.get('opening_balance_entry'):
            ctx = dict(self.env.context, check_move_validity=False)
            self = self.with_context(ctx)
        res = super(AccountMoveInherit, self).create(vals)
        if res.apply_withholding_tax:
            self.generate_withholding_tax_jounal_lines(res, res.invoice_line_ids)
        return res

    def write(self, vals):
        if 'opening_balance_entry' in vals:
            if vals.get('opening_balance_entry'):
                ctx = dict(self.env.context, check_move_validity=False)
                self = self.with_context(ctx)
        else:
            for i in self:
                if i.opening_balance_entry:
                    ctx = dict(self.env.context, check_move_validity=False)
                    self = self.with_context(ctx)
        res = super(AccountMoveInherit, self).write(vals)
        for rec in self:
            if rec.apply_withholding_tax and not self._context.get('del_line_ids') and (vals.get('line_ids') or 'payed_by_fusion' in vals):
                rec.with_context({'write': True}).generate_withholding_tax_jounal_lines(self, rec.invoice_line_ids)
        return res

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.move_type == 'in_invoice' and self.partner_id.tax_id:
            self.apply_withholding_tax = True
            self.withholding_tax_id = self.partner_id.tax_id.id
        else:
            self.apply_withholding_tax = False
            self.withholding_tax_id = False
            self.payed_by_fusion = False


class AccountMoveLineInherit(models.Model):
    _inherit = 'account.move.line'

    is_withholding_tax_entry = fields.Boolean(string="Is Withholding Tax Entry")


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    code = fields.Char(string='Short Code', size=999, required=True,
                       help="The journal entries of this journal will be named using this prefix.")
