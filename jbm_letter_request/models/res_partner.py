from odoo import models, fields, api


class InheritResPartner(models.Model):
    _inherit = 'res.partner'

    show_in_letter_request = fields.Boolean()