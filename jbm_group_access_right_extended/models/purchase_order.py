from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _create_picking(self):
        if self.env.user.has_group('jbm_group_access_right_extended.custom_accountant_role_manager'):
            raise ValidationError('you have no access for create picking')
        elif self.env.user.has_group('jbm_group_access_right_extended.custom_accounting_auditor_manager'):
            raise ValidationError('you have no access for create picking')
        elif self.env.user.has_group('jbm_group_access_right_extended.custom_general_manager_representative'):
            raise ValidationError('you have no access for create picking')
        elif self.env.user.has_group('jbm_group_access_right_extended.custom_financial_manager'):
            raise ValidationError('you have no access for create picking')
        elif self.env.user.has_group('jbm_group_access_right_extended.custom_general_manager'):
            raise ValidationError('you have no access for create picking')
        StockPicking = self.env['stock.picking']
        for order in self.filtered(lambda po: po.state in ('purchase', 'done')):
            if any(product.type in ['product', 'consu'] for product in order.order_line.product_id):
                order = order.with_company(order.company_id)
                pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
                if not pickings:
                    res = order._prepare_picking()
                    picking = StockPicking.with_user(SUPERUSER_ID).create(res)
                else:
                    picking = pickings[0]
                moves = order.order_line._create_stock_moves(picking)
                moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
                seq = 0
                for move in sorted(moves, key=lambda move: move.date):
                    seq += 5
                    move.sequence = seq
                moves._action_assign()
                picking.message_post_with_view('mail.message_origin_link',
                                               values={'self': picking, 'origin': order},
                                               subtype_id=self.env.ref('mail.mt_note').id)
        return True
