from odoo import models, fields, _


class PurchaseOrder(models.Model):
    _name = 'purchase.order'
    _inherit = ['purchase.order', 'dms.integration.mix']
