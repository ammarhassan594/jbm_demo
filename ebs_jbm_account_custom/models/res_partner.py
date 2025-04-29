from odoo import models, fields, api, _


class InheritResPartner(models.Model):
    _inherit = 'res.partner'

    is_legacy_account = fields.Boolean(string="Legacy Account")
