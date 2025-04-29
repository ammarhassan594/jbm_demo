from odoo import api, fields, models, _


class TaxCard(models.Model):
    _name = 'res.partner.tax.card'
    _description = 'Res Partner Tax card'

    partner_id = fields.Many2one('res.partner')
    name = fields.Char(string='Tax card Number')
    issue_date = fields.Date(string='Issue Date')
    expiry_date = fields.Date(string='Expiry Date')
    frequency_of_payment = fields.Selection([('monthly','Monthly'),
                                             ('quarterly','Quarterly'),
                                             ('yearly','Yearly')],string='Frequency of Payment')
    currency_id = fields.Many2one('res.currency', default=lambda o:o.partner_id.currency_id)
    balance_due = fields.Monetary(string='Balance Due', currency_field='currency_id')
    appointed_auditors = fields.Many2one('res.partner',string='Appointed Auditors')
    comments = fields.Text(string='Other/Comments')
    document_id = fields.Many2one('documents.document',string='Document')
