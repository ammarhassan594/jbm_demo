from odoo import models, fields, api, _


class InheritAccountMove(models.Model):
    _inherit = 'account.move'

    closing_entry = fields.Boolean(string="Closing Entry")
