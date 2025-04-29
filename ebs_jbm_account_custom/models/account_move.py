from odoo import models, fields, api, _


class InheritAccountMove(models.Model):
    _inherit = 'account.move'
    legacy_reference = fields.Char(string="Legacy Reference")
    legacy_journal_number = fields.Char(string="Legacy Journal Number ")
    legacy_posting_type = fields.Char(string="Legacy Posting Type")
