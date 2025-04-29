from odoo import api, fields, models, _
from datetime import date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError


class ebsContractProposalFees(models.Model):
    _name = 'ebs.contract.proposal.fees'
    _description = 'EBS Contract Proposal Fees'

    fusion_fees_id = fields.Many2one('ebs.fusion.fees', string='Main Company Fees', required=1)
    type = fields.Selection(related='fusion_fees_id.type',store=True)
    label = fields.Char(string='Label', default=lambda self: self.fusion_fees_id.name)
    amount = fields.Float(string='Amount')
    invoiced_amount = fields.Float(string='Invoiced Amount', compute='compute_amount')
    remaining_amount = fields.Float(string='Remaining Amount', compute='compute_amount')
    amount_to_be_paid = fields.Float(string='Amount to be Paid')
    lead_id = fields.Many2one('crm.lead', string='Deal')
    contract_id = fields.Many2one('ebs.crm.proposal', string='Contract')
    client_id = fields.Many2one('res.partner',related='contract_id.contact_id',store=True)
    fme = fields.Boolean(related='fusion_fees_id.is_fme')
    fss = fields.Boolean(related='fusion_fees_id.is_fss')
    fos = fields.Boolean(related='fusion_fees_id.is_fos')
    lead_fme = fields.Boolean(related='lead_id.fme')
    lead_fss = fields.Boolean(related='lead_id.fss')
    lead_fos = fields.Boolean(related='lead_id.fos')
    move_line_ids = fields.One2many('account.move.line','contract_fees_id', 'Move Line')
    next_invoice_date = fields.Date(string="Next Invoice Date")
    invoice_date = fields.Date(string="Invoice Date")
    payment_ids = fields.One2many('account.payment', 'contract_fees_id', 'Payments')
    invoice_ids = fields.Many2many('account.move', 'contract_fees_invoices_rel', 'fee_id', 'move_id', string='Invoices', compute='compute_invoices')
    invoice_period = fields.Selection(related='fusion_fees_id.invoice_period')
    state = fields.Selection([('draft','Draft'),('active','Active'),('termination', 'Under Termination'),
                               ('cancelled', 'Cancelled')],default='draft',string="Status",related='contract_id.state', store=True)

    @api.depends('fusion_fees_id','client_id')
    def name_get(self):
        result = []
        for rec in self:
            rec_name = ""
            if rec.client_id:
                rec_name = rec.fusion_fees_id.name +'-'+ rec.client_id.name
            else:
                rec_name = rec.fusion_fees_id.name

            result.append((rec.id, rec_name))
        return result

    @api.onchange('invoice_date')
    def onchange_invoice_date(self):
        if self.invoice_date:
            if self.invoice_period == 'yearly' and (self.invoice_date > (self.next_invoice_date + relativedelta(years=1)) or self.invoice_date < self.next_invoice_date):
                raise UserError(_("Please Select Invoice Date Between %s And %s." % (self.next_invoice_date, self.next_invoice_date + relativedelta(years=1))))
            if self.invoice_period == 'monthly' and (self.invoice_date > (self.next_invoice_date + relativedelta(months=1)) or self.invoice_date < self.next_invoice_date):
                raise UserError(_("Please Select Invoice Date Between %s And %s." % (self.next_invoice_date, self.next_invoice_date + relativedelta(months=1))))
            if self.invoice_date < self.next_invoice_date:
                raise UserError(_("Please Select Invoice Date Greater Than Next Invoice Date."))

    @api.onchange('fusion_fees_id')
    def onchange_fusion_fees(self):
        for rec in self:
            if rec.fusion_fees_id:
                rec.label = rec.fusion_fees_id.name
            domain = []
            count = 0
            if rec.contract_id:
                if self.contract_id.contract_type == 'fme':
                    count += 1
                    domain.append(('is_fme', '=', True))
                if self.contract_id.contract_type == 'fss':
                    count += 1
                    domain.append(('is_fss', '=', True))
                if self.contract_id.contract_type == 'fos':
                    count += 1
                    domain.append(('is_fos', '=', True))
                if count == 2:
                    domain.insert(0, '|')
                if count == 3:
                    domain.insert(0, '|')
                    domain.insert(1, '|')
            else:
                if self.lead_fme:
                    count += 1
                    domain.append(('is_fme', '=', self.lead_fme))
                if self.lead_fss:
                    count += 1
                    domain.append(('is_fss', '=', self.lead_fss))
                if self.lead_fos:
                    count += 1
                    domain.append(('is_fos', '=', self.lead_fos))
                if count == 2:
                    domain.insert(0, '|')
                if count == 3:
                    domain.insert(0, '|')
                    domain.insert(1, '|')
            if domain:
                return {
                    'domain':
                        {'fusion_fees_id': domain}
                }
            else:
                return {
                    'domain':
                        {'fusion_fees_id': [('id','in',[])]}
                }

    @api.depends('move_line_ids')
    def compute_invoices(self):
        for rec in self:
            rec.write({'invoice_ids': [(6, 0, rec.move_line_ids.mapped('move_id').ids)]})

    @api.depends('amount', 'fusion_fees_id', 'contract_id.start_date')
    def compute_amount(self):
        for rec in self:

            if rec.fusion_fees_id and rec._origin.id:

                if rec.next_invoice_date:
                    if rec.fusion_fees_id.type != 'proforma':
                        if rec.invoice_period == 'yearly':

                            move_lines = rec.move_line_ids.filtered(lambda o: (o.move_id.invoice_date and rec.next_invoice_date) and o.move_id.invoice_date >= rec.next_invoice_date and o.move_id.invoice_date < (rec.next_invoice_date + relativedelta(years=1)) and o.move_id.state != 'cancel')
                        elif rec.invoice_period == 'monthly':
                            move_lines = rec.move_line_ids.filtered(lambda o: (o.move_id.invoice_date and rec.next_invoice_date) and o.move_id and o.move_id.invoice_date >= rec.next_invoice_date and o.move_id.invoice_date < (rec.next_invoice_date + relativedelta(months=1)) and o.move_id.state != 'cancel')
                        else:
                            move_lines = rec.move_line_ids
                        rec.invoiced_amount = sum(move_lines.mapped('price_subtotal'))
                        rec.remaining_amount = rec.amount - sum(move_lines.mapped('price_subtotal'))
                    else:
                        if rec.invoice_period == 'yearly':
                            payment_ids = rec.payment_ids.filtered(lambda o: o.payment_date >= rec.next_invoice_date and o.payment_date < (rec.next_invoice_date + relativedelta(years=1)) and o.state != 'cancelled')
                        elif rec.invoice_period == 'monthly':
                            payment_ids = rec.payment_ids.filtered(lambda o: o.payment_date >= rec.next_invoice_date and o.payment_date < (rec.next_invoice_date + relativedelta(months=1)) and o.state != 'cancelled')
                        else:
                            payment_ids = rec.payment_ids
                        rec.invoiced_amount = sum(payment_ids.mapped('amount'))
                        rec.remaining_amount = rec.amount - sum(payment_ids.mapped('amount'))
                else:
                    rec.invoiced_amount = 0.0
                    rec.remaining_amount = 0.0
            else:
                rec.invoiced_amount = 0.0
                rec.remaining_amount = 0.0



    @api.onchange('amount')
    def onchange_amount(self):
        for rec in self:
            rec.amount_to_be_paid = rec.amount

