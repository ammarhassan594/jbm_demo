from odoo import models, fields, api, _


class PurchaseOrderEvaluation(models.Model):
    _name = 'purchase.order.evaluation'
    _description = 'Purchase Order evaluation'

    type = fields.Char(string='Type')
    total_score = fields.Integer(string="Total Score")
    min_score = fields.Integer(string="Minimum Score")
    descriptions = fields.Char(string="Description")
    purchase_order_id = fields.Many2one('purchase.order', string="Purchase order")
