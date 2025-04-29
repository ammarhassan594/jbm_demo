from odoo import api, fields, models, _


class ebsClientConversionRate(models.Model):
    _name = 'ebs.client.conversion.rate'
    _description = 'EBS Client Conversion Rate'

    partner_id = fields.Many2one('res.partner')
    currency_id = fields.Many2one('res.currency', string='Currency')
    rate = fields.Float(string='Rate', digits=(12, 6))
