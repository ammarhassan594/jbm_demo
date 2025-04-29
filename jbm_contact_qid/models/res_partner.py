from odoo import api, fields, models, _


class Contacts(models.Model):
    _inherit = 'res.partner'

    qid_ref_no = fields.Char("QID Reference Number", translate=False, related='qid_residency_id.document_number')

