from odoo import fields, models, api


class DmsResPartner(models.Model):
    _name = 'res.partner'

    _inherit = ['res.partner', 'dms.integration.mix']
