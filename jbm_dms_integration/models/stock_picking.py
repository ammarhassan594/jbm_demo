from odoo import fields, models, api


class DmsStockPicking(models.Model):
    _name = 'stock.picking'

    _inherit = ['stock.picking', 'dms.integration.mix']
