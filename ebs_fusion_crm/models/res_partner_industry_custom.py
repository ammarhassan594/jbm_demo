from odoo import api, fields, models, _


class Partner_Industry(models.Model):
    _inherit = 'res.partner.industry'

    parent_id = fields.Many2one('res.partner.industry', string="Parent")

