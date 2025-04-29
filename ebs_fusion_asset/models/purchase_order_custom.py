# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class PurchaseOrderCustom(models.Model):
    _inherit = 'purchase.order'

    asset_number = fields.Integer(
        string='Asset Number',
        compute="get_asset_number",
        required=False)

    def get_asset_number(self):
        for rec in self:
            rec.asset_number = len(self.env['account.asset'].sudo().search([('po_id', '=', rec.id)]))

    def open_create_asset_wiz(self):
        wiz = self.env['ebs.asset.po'].create({
            'asset_type': 'purchase',
            'po_id': self.id
        })
        for line in self.order_line:
            asset_to_create = int(line.qty_received) - line.asset_created_nb
            for x in range(asset_to_create):
                if line.product_id.product_tmpl_id.is_asset:
                    self.env['ebs.asset.po.line'].create({
                        'parent_id': wiz.id,
                        'po_line_id': line.id,
                        'name': line.product_id.name,
                        'asset_model': line.product_id.product_tmpl_id.asset_id and line.product_id.product_tmpl_id.asset_id.id,
                    })

        view_form_id = self.env.ref('ebs_fusion_asset.create_asset_po_view_form').id
        return {
            'name': _('Create Asset'),
            'res_model': 'ebs.asset.po',
            'type': 'ir.actions.act_window',
            'views': [(view_form_id, 'form')],
            'view_mode': 'form',
            'res_id': wiz.id,
            'target': 'new',
        }

    def action_see_asset(self):
        self.ensure_one()
        view_tree_id = self.env.ref('account_asset.view_account_asset_purchase_tree').id
        view_form_id = self.env.ref('account_asset.view_account_asset_form').id

        return {
            'name': _('Assets'),
            'res_model': 'account.asset',
            'type': 'ir.actions.act_window',
            'views': [(view_tree_id, 'tree'), (view_form_id, 'form')],
            'view_mode': 'tree',
            'domain': [('po_id', '=', self.id)],

            'context': {
                "default_po_id": self.id,
            },
        }
