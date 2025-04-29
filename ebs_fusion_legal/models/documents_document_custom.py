from odoo import api, fields, models, _

class DocumentsCustom(models.Model):
    _inherit = 'documents.document'

    case_id = fields.Many2one('ebs.legal.case',string='Legal Case')

