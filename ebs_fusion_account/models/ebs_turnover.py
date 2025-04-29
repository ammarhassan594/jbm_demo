from odoo import api, fields, models, _
import datetime
from odoo.exceptions import UserError, ValidationError


class ebsTurnover(models.Model):
    _name = 'ebs.turnover'
    _description = 'EBS Turnover'

    name = fields.Char('Name', readonly=True, required=True, copy=False, default='New')
    client_id = fields.Many2one('res.partner', string="Client",
                                domain="[('is_customer', '=', True),('is_company', '=', True),('parent_id', '=', False)]")
    contract_id = fields.Many2one('ebs.crm.proposal', string="Contract", domain="[('contact_id', '=', client_id),('contract_type', '=', 'fme')]")
    invoice_id = fields.Many2one('account.move', string="Invoice")
    currency_id = fields.Many2one('res.currency', string='Currency')
    amount_residual_turnover = fields.Monetary('Amount Residual', related='invoice_id.amount_residual')
    turn_over_rate = fields.Float('Turn Over Rate')
    turn_over_amount = fields.Float('Turn Over Amount')
    discount_rate = fields.Float('Discount Rate', default=0)
    turn_over_date = fields.Date('Turn Over Date', default=datetime.datetime.today().date())
    amount_to_pay = fields.Float('Amount To Pay', compute="calculate_amount_to_pay")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('partially_paid', 'Partially Paid'),
        ('paid', 'Paid'),
    ], default="draft")
    invoice_count = fields.Integer(compute='invoice_compute_count')

    @api.model
    def create(self, vals):
        vals.update({'name': self.env['ir.sequence'].next_by_code('ebs.turnover') or _('New')})
        result = super(ebsTurnover, self).create(vals)
        return result

    def invoice_compute_count(self):
        for record in self:
            record.invoice_count = self.env['account.move'].search_count(
                [('turnover_id', '=', record.id),('move_type', '=', 'out_invoice')])
            if record.state != 'draft' and record.state != 'paid' and record.invoice_id:
                if record.amount_residual_turnover == 0:
                    record.write({'state':'paid'})
                elif record.amount_residual_turnover < record.amount_to_pay:
                    record.write({'state':'partially_paid'})

    def get_invoice(self):
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        action['context'] = {
            'default_turnover_id': self.id,
            'default_type': 'out_invoice',
            'create':False,
        }
        action['domain'] = [('turnover_id', '=', self.id),('move_type', '=', 'out_invoice')]
        return action

    def calculate_amount_to_pay(self):
        for rec in self:
            rec.amount_to_pay = rec.turn_over_amount * rec.turn_over_rate - rec.discount_rate

    def confirm_turnover(self):
        for rec in self:
            if rec.amount_to_pay == 0:
                raise UserError(_('Amount To Pay can not be 0.'))
            rec.state = 'confirmed'

    def generate_invoice(self):
        if not self.client_id:
            raise UserError(_('You have to select an invoice address in Contract.'))
        company = self.env.user.company_id

        journal = self.env['account.move'].with_context(force_company=company.id,
                                                        move_type='out_invoice')._get_default_journal()

        product_id = self.env['product.product'].sudo().search([('default_code', '=', 'P0T1')])
        if not product_id:
            product_id = self.env['product.product'].sudo().create({
                'name': 'Turnover',
                'default_code': 'P0T1',
                'standard_price': '4.5',
                'list_price': '4.5',
                'move_type': 'service',
            })

        if journal:
            if product_id.property_account_income_id:
                invoice = self.env['account.move'].create(
                    {'turnover_id':self.id,'invoice_date': self.turn_over_date, 'move_type': 'out_invoice', 'partner_id': self.client_id.id,
                     'invoice_line_ids': [(0, 0, {'name': product_id.name,
                                                  'account_id': product_id.property_account_income_id.id,
                                                  'quantity': 1,
                                                  'price_unit': self.amount_to_pay,
                                                  'product_id': product_id.id, })]})
                self.invoice_id = invoice

            else:
                raise UserError(_('No account defined for product "%s".') % product_id.name)
        else:
            raise UserError(_('Please define an accounting sales journal for the company %s (%s).') % (
                company.name, company.id))


class ebsCrmProposalInherit(models.Model):
    _inherit = 'ebs.crm.proposal'

    turnover_count = fields.Integer(compute='turnover_compute')

    def turnover_compute(self):
        for record in self:
            record.turnover_count = self.env['ebs.turnover'].search_count(
                [('contract_id', '=', self.id)])

    def get_turnover(self):
        action = self.env.ref('ebs_fusion_account.action_ebs_turnover').read()[0]
        action['context'] = {
            'create': 1,
            'default_contract_id': self.id,
            'default_turn_over_rate': self.turnover,
            'default_client_id': self.contact_id.id,
            'is_from_contract':True,
        }
        action['views'] = [(self.env.ref('ebs_fusion_account.view_ebs_turnover_tree').id, 'tree'),
                           (self.env.ref('ebs_fusion_account.view_ebs_turnover_form').id, 'form')]
        action['view_mode'] = 'form'
        action['domain'] = [('contract_id', '=', self.id)]
        return action


class account_move_inherit(models.Model):
    _inherit = "account.move"

    turnover_id = fields.Many2one('ebs.turnover', 'Turnover')

