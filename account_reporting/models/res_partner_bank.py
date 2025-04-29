from odoo import models, fields, api, _


class InheritResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    account_type_id = fields.Many2one("account.type", string="Account Type")

