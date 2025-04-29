from odoo import models, fields, api


class PurchaseContract(models.Model):
    _name = 'purchase.contract'
    _description = 'Purchase Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'contract_number'

    contract_number = fields.Char(string='Contract Number', readonly=False,
                                  default='New', required=True)
    vendor_id = fields.Many2one(comodel_name='res.partner', string='Vendor', required=True,
                                domain=[('is_vendor', '=', True)])
    contact_name = fields.Char(string='Contact Name', related='vendor_id.name', readonly=True)
    payment_terms_id = fields.Many2one(comodel_name='account.payment.term', string='Payment Term', required=True)
    from_date = fields.Date(string='From Date', required=True)
    to_date = fields.Date(string='To Date', required=True)
    terms_and_condition_line_ids = fields.One2many(comodel_name='purchase.contract.term', inverse_name='contract_id',
                                                   string='Terms and Conditions')
    contract_date = fields.Date(string="Contract Date", required=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], default='draft')
    document_ids = fields.Many2many('documents.document', string="Documents")

    def draft_action(self):
        for record in self:
            record.status = 'draft'

    def progress_action(self):
        for record in self:
            if record.status == 'draft':
                record.status = 'in_progress'

    def complete_action(self):
        for record in self:
            if record.status == 'in_progress':
                record.status = 'completed'

    def cancel_action(self):
        for record in self:
            record.status = 'cancelled'

    # @api.model
    # def create(self, vals):
    #     if vals.get('contract_number', 'New') == 'New':
    #         vals['contract_number'] = self.env['ir.sequence'].next_by_code(
    #             'purchase.contract') or 'New'
    #     result = super(PurchaseContract, self).create(vals)
    #     return result


class PurchaseContractTerm(models.Model):
    _name = 'purchase.contract.term'
    _description = 'Purchase Contract Terms and Conditions'

    contract_id = fields.Many2one(comodel_name='purchase.contract', string='Contract', ondelete='cascade')
    description = fields.Text(string='Description', required=True)
    from_date = fields.Date(string='From Date', required=True)
    to_date = fields.Date(string='To Date', required=True)

    @api.constrains('to_date', 'from_date')
    def _check_dates(self):
        for record in self:
            if record.to_date < record.from_date:
                raise ValueError("To date should be greater than From date.")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    general_terms_and_conditions = fields.Text(string='General Terms and Conditions',
                                               related="company_id.general_terms_and_conditions",
                                               readonly=False)


class ResCompanyAdvancePaymentInherit(models.Model):
    _inherit = 'res.company'

    general_terms_and_conditions = fields.Text(string='General Terms and Conditions', )
