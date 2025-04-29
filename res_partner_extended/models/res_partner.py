from odoo import api, fields, models, _


class ResPartnerExtended(models.Model):
    _inherit = 'res.partner'

    address_zone = fields.Char(
        string='Zone'
    )
    address_street = fields.Char(
        string='Street'
    )
    address_building = fields.Char(
        string='Building'
    )
