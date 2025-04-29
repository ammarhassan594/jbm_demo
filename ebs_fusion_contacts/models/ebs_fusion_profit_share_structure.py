from odoo import api, fields, models, _


class Profit_Share_Structure(models.Model):
    _name = 'profit.share.structure'
    _description = "name"

    partner_id = fields.Many2one('res.partner',"Name")
    percentage = fields.Float("Percentage")