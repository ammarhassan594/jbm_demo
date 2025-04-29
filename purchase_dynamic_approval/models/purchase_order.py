# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _


class PurchaseOrder(models.Model):
    _name = 'purchase.order'
    _inherit = ['purchase.order', 'dynamic.approval.mixin']
    _state_from = ['sent']
    _state_to = ['purchase']
    _cancel_state = "rejected"



    def _action_final_approve(self):
        """ mark order as approved """
        self.ensure_one()
        self._run_final_approve_function()
        if self._name == 'purchase.order':
            seq_date = None
            if self.date_approve:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(self.date_approve))
            self.approval_sequence = self.env['ir.sequence'].next_by_code('approved.purchase.order', sequence_date=seq_date) or '/'
            related_orders = [
                order for order in self.approval_request_id.purchase_order_ids
                if order != self
            ]
            if self.approval_request_id.approval_request_id:
                self.approval_request_id.approval_request_id.approved_purchase_order_id = self.id
                self.approval_request_id.approval_request_id.approved_po_number = self.approval_sequence
            for order in related_orders:
                order.write({'state': 'rejected'})
                activity = order._get_user_approval_activities()
                reason = ''
                if activity:
                    activity.action_feedback(feedback=_('Rejected, Reason ') + reason)

            self.button_confirm()
        return super(PurchaseOrder, self)._action_final_approve()
        # else:
        #     super(PurchaseOrder, self)._action_final_approve()


    def _action_reset_original_state(self, reason='', reset_type='reject'):
        if self._name == 'purchase.order':
            self.sudo().write({
                self._state_field: self._cancel_state,
                # 'final_approve_date': fields.Date.today()
            })
        return super(PurchaseOrder, self)._action_reset_original_state(reason='', reset_type='reject')
