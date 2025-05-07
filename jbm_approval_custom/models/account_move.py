from odoo import models, fields, api, _

class InheritAccountMove(models.Model):
    _inherit = 'account.move'

    approval_request_id = fields.Many2one('approval.request')