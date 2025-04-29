from odoo import models, fields, api, _


class InheritAccountMove(models.Model):
    _inherit = "account.move"

    purchase_count = fields.Integer(compute="_get_purchase_count")

    def _get_purchase_count(self):
        self.ensure_one
        purchase_ids = self.env['purchase.order'].search([
            ('invoice_ids', '=', self.id)
        ])
        self.purchase_count = len(purchase_ids)
        self.purchase_id = purchase_ids.id
    def action_view_purchase(self):
        self.ensure_one()
        purchase_ids = self.env['purchase.order'].search([
            ('invoice_ids', '=', self.id)
        ])
        result = {
            "type": "ir.actions.act_window",
            "res_model": "purchase.order",
            "domain": [('id', 'in', purchase_ids.ids)],
            "context": {"create": False},
            "name": _("Requests for Quotation"),
            'view_mode': 'tree,form',
        }
        return result
