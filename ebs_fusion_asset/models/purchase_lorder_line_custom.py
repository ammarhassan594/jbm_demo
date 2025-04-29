# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class PurchaseOrderLineCustom(models.Model):
    _inherit = 'purchase.order.line'

    asset_created_nb = fields.Integer(
        string='Assets',
        required=False, compute="get_created_assets")

    def get_created_assets(self):
        for rec in self:
            rec.asset_created_nb = len(self.env['account.asset'].sudo().search([('po_line_id', '=', rec.id)]))
