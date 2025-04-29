from odoo import fields, models, api


class ResCountry(models.Model):
    _inherit = 'res.country'

    arabic_name = fields.Char("Arabic Name")
