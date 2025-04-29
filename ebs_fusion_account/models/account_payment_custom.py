from odoo import api, fields, models, _
from lxml import etree
import inflect
from odoo.exceptions import UserError, ValidationError


class AccountPayment(models.Model):
    """Account Payment Model."""

    _inherit = 'account.payment'

    def number_to_word(self, number):
        p = inflect.engine()
        return p.number_to_words(int(number)).title()

    is_payment_read_access = fields.Boolean('Payment Read Access', compute='compute_payment_read_access', default=False)
    apply_withholding_tax = fields.Boolean()
    withholding_tax_id = fields.Many2one('account.tax', string="Withholding Tax")
    payed_by_fusion = fields.Boolean(string="Payed By Main Company")
    bill_amount = fields.Float()
    withholding_tax_move_id = fields.Many2one('account.move', string='Withholding Tax JV')
    analytic_account = fields.Many2one('account.analytic.account', string="Analytic Account")
    desc = fields.Text('Description')
    is_post_dated_check = fields.Boolean('Is post date')
    is_proforma = fields.Boolean("Is Proforma")
    proforma_ids = fields.One2many("ebs.proforma.lines", 'payment_id')
    payment_sequence = fields.Char('Sequence')

    @api.onchange('proforma_ids')
    def onchange_proforma_ids(self):
        if self.is_proforma:
            amount = sum(self.proforma_ids.mapped('amount'))
            self.amount = amount

    def confirm_proforma_inv(self):
        for rec in self:
            total = 0
            for line in rec.proforma_ids:
                total += line.amount
            if not rec.amount == total:
                raise UserError("The payment amount and Proforma Lines total amount is not matching")
            proforma_sequence_id = rec.company_id.proforma_sequence_id
            if not proforma_sequence_id:
                raise UserError('Please configure Proforma Sequence in accounting settings')
            if not rec.payment_sequence:
                rec.payment_sequence = proforma_sequence_id.next_by_id()

    def unlink(self):
        for payment in self:
            if payment.withholding_tax_move_id:
                payment.withholding_tax_move_id.button_draft()
                payment.withholding_tax_move_id.with_context(force_delete=True).unlink()
        return super(AccountPayment, self).unlink()

    def action_draft(self):
        res = super(AccountPayment, self).action_draft()
        for payment in self:
            if payment.withholding_tax_move_id:
                payment.withholding_tax_move_id.button_draft()
                payment.withholding_tax_move_id.with_context(force_delete=True).unlink()
        return res

    def post(self):
        """ Create the journal items for the payment and update the payment's state to 'posted'.
            A journal entry is created containing an item in the source liquidity account (selected journal's default_debit or default_credit)
            and another in the destination reconcilable account (see _compute_destination_account_id).
            If invoice_ids is not empty, there will be one reconcilable move line per invoice to reconcile with.
            If the payment is a transfer, a second journal entry is created in the destination journal to receive money from the transfer account.
        """
        AccountMove = self.env['account.move'].with_context(default_move_type='entry')
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_("Only a draft payment can be posted."))

            if any(inv.state != 'posted' for inv in rec.invoice_ids):
                raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))

            if rec.invoice_ids and rec.invoice_ids[0].apply_withholding_tax:
                rec.apply_withholding_tax = True
                rec.withholding_tax_id = rec.invoice_ids[0].withholding_tax_id.id
                rec.payed_by_fusion = rec.invoice_ids[0].payed_by_fusion
                rec.bill_amount = rec.invoice_ids[0].amount_total
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
                rec.name = self.env['ir.sequence'].next_by_code(sequence_code, sequence_date=rec.date)
                if not rec.name and rec.payment_type != 'transfer':
                    raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))

            moves = AccountMove.create(rec._prepare_payment_moves())
            if rec.apply_withholding_tax:
                self.generate_withholding_tax_lines(rec)
            moves.filtered(lambda move: move.journal_id.post_at != 'bank_rec').post()
            for line in moves.line_ids:
                line.write({'analytic_account_id': self.analytic_account.id})
            # Update the state / move before performing any reconciliation.
            move_name = self._get_move_name_transfer_separator().join(moves.mapped('name'))
            rec.write({'state': 'posted', 'move_name': move_name})

            if rec.payment_type in ('inbound', 'outbound'):
                # ==== 'inbound' / 'outbound' ====
                if rec.invoice_ids:
                    (moves[0] + rec.invoice_ids).line_ids \
                        .filtered(
                        lambda line: not line.reconciled and line.account_id == rec.destination_account_id and not (
                                line.account_id == line.payment_id.writeoff_account_id and line.name == line.payment_id.writeoff_label)) \
                        .reconcile()
            elif rec.payment_type == 'transfer':
                # ==== 'transfer' ====
                moves.mapped('line_ids') \
                    .filtered(lambda line: line.account_id == rec.company_id.transfer_account_id) \
                    .reconcile()
            rec.withholding_tax_move_id.post()

        return True

    def generate_withholding_tax_lines(self, payment):
        withholding_tax_journal_id = payment.company_id.withholding_tax_journal_id
        if not withholding_tax_journal_id:
            raise UserError(_('Please Add Withholding Tax Journal in Account Configuration.'))
        taxes_res = self.env['account.move.line']._get_price_total_and_subtotal_model(
            price_unit=payment.amount,
            quantity=1,
            discount=False,
            product=False,
            partner=payment.partner_id,
            currency=payment.currency_id,
            taxes=payment.withholding_tax_id,
            move_type='in_invoice'
        )
        tax_amount = taxes_res.get('price_total') - taxes_res.get('price_subtotal')
        if payment.payed_by_fusion:
            account_id = payment.journal_id.default_debit_account_id
        else:
            account_id = payment.destination_account_id
        line_ids = [
            (0, 0, {
                'account_id': account_id.id,
                'partner_id': payment.partner_id.id,
                'credit': tax_amount,
                'exclude_from_invoice_tab': True,
                'payment_id': payment.id,
                'is_withholding_tax_entry': True
            }),
            (0, 0, {
                'account_id': payment.withholding_tax_id.tax_group_id.property_tax_payable_account_id.id,
                'name': 'Withholding Tax Payable',
                'partner_id': payment.partner_id.id,
                'debit': tax_amount,
                'exclude_from_invoice_tab': True,
                'payment_id': payment.id,
                'is_withholding_tax_entry': True
            })
        ]
        move_vals = {
            'move_type': 'entry',
            'ref': payment.name,
            'journal_id': withholding_tax_journal_id.id,
            'line_ids': line_ids
        }
        withholding_tax_move_id = self.env['account.move'].create(move_vals)
        payment.write({'withholding_tax_move_id': withholding_tax_move_id})

    def compute_payment_read_access(self):
        for rec in self:
            if self.env.user.has_group('ebs_fusion_account.group_access_invoice_read'):
                rec.is_payment_read_access = True
            else:
                rec.is_payment_read_access = False

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):

        res = super(AccountPayment, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)
        if self.env.user.has_group('ebs_fusion_account.group_access_invoice_read'):
            root = etree.fromstring(res['arch'])
            root.set('edit', 'false')
            root.set('create', 'false')
            root.set('delete', 'false')
            res['arch'] = etree.tostring(root)
        return res


class EbsProformaLines(models.Model):
    _name = 'ebs.proforma.lines'
    _description = 'EBS Proforma Lines'

    payment_id = fields.Many2one('account.payment')
    service_order_id = fields.Many2one('ebs.crm.service.process')
    employee_ids = fields.Many2many('hr.employee')
    quantity = fields.Integer(string="Quantity", default=1)
    description = fields.Char(string="Description")
    rate = fields.Monetary(string="Rate")
    amount = fields.Monetary(string="Amount", compute="compute_amount")
    currency_id = fields.Many2one('res.currency', related='payment_id.currency_id')

    @api.depends('rate', 'quantity')
    def compute_amount(self):
        for record in self:
            if record.rate or record.quantity:
                record.amount = record.rate * record.quantity


class AccountMove(models.Model):
    """Account Move Model."""

    _inherit = 'account.move'

    is_invoice_read_access = fields.Boolean('Invoice Read Access', compute='compute_invoice_read_access', default=False)

    def compute_invoice_read_access(self):
        for rec in self:
            if self.env.user.has_group('ebs_fusion_account.group_access_invoice_read'):
                rec.is_invoice_read_access = True
            else:
                rec.is_invoice_read_access = False

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):

        res = super(AccountMove, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)
        if self.env.user.has_group('ebs_fusion_account.group_access_invoice_read'):
            root = etree.fromstring(res['arch'])
            root.set('edit', 'false')
            root.set('create', 'false')
            root.set('delete', 'false')
            res['arch'] = etree.tostring(root)
        return res


class HRemployee(models.Model):
    _inherit = "hr.employee"

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        if self._context.get('proforma_partner_id'):
            args.append(('partner_parent_id', '=', self._context.get('proforma_partner_id')))
        return super(HRemployee, self)._search(args, offset=offset, limit=limit, order=order, count=count,
                                               access_rights_uid=access_rights_uid)
