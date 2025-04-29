from odoo import api, fields, models, _

class ResCompany(models.Model):
    _inherit = "res.company"

    tin_tax_id = fields.Many2one('account.tax', string="Tin Tax")
    withholding_tax_journal_id = fields.Many2one('account.journal', string="Withholding Tax Journal")
    proforma_sequence_id = fields.Many2one('ir.sequence', string='Proforma Invoice Sequence')
