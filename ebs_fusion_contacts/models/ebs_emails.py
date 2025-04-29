from odoo import api, fields, models, _


class email_addresses(models.Model):
    _name = 'email.addresses'
    _description = 'Email Address'

    partner_id = fields.Many2one('res.partner')
    email = fields.Char("")
    type = fields.Selection([('personal','Personal'),('business','Business')],string="Type")
