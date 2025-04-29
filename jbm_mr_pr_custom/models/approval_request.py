from odoo import models, fields, api, _

class InheritApprovals(models.Model):
    _inherit = 'approval.request'

    approval_request_id = fields.Many2one('approval.request')
    requester_id = fields.Many2one('res.users')
    approved_purchase_order_id = fields.Many2one('purchase.order')
    approved_po_number = fields.Char()



    @api.model
    def create(self, vals_list):
        res = super(InheritApprovals, self).create(vals_list)
        if self._context.get('default_approval_request_id'):
            res.approval_request_id.approval_request_id = res.id
        return res



    def open_purchase_request(self):
        self.ensure_one()
        # If category uses sequence, set next sequence as name
        # (if not, set category name as default name).
        return {
            "type": "ir.actions.act_window",
            "res_model": "approval.request",
            "views": [[False, "form"]],
            "context": {
                'form_view_initial_mode': 'edit',
                'default_name': _('New') if self.automated_sequence else self.name,
                'default_category_id': self.env['approval.category'].search([('approval_type', '=', 'purchase'), ('sequence_code', '=', 'PR')]).id,
                'default_request_owner_id': self.env.user.id,
                'default_approval_request_id': self.id,
                'default_requester_id': self.create_uid.id,
                'default_reason': self.reason,
                'default_date': self.date,
                'default_request_status': 'new'
            },
        }