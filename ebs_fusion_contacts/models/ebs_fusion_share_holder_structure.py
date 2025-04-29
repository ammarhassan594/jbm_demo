from odoo import api, fields, models, _


class Share_Holder_Structure(models.Model):
    _name = 'share.holder.structure'
    _description = "name"

    partner_id = fields.Many2one('res.partner',"Name")
    percentage = fields.Float("Percentage")