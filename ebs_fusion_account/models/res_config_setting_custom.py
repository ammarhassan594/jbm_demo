from odoo import api, fields, models, _


class Res_Config_Settings(models.TransientModel):

    _inherit = 'res.config.settings'

    tin_tax_id = fields.Many2one('account.tax', string="Tin Tax", related='company_id.tin_tax_id', readonly=False)
    withholding_tax_journal_id = fields.Many2one('account.journal', related='company_id.withholding_tax_journal_id', readonly=False, string='Withholding Tax Journal')
    proforma_sequence_id = fields.Many2one('ir.sequence', related='company_id.proforma_sequence_id', readonly=False, string='Proforma Invoice Sequence')

