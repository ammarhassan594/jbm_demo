from odoo import models, fields, api, _


class InheritAccountPayment(models.Model):
    _inherit = 'account.payment'

    bill_count = fields.Integer(compute="_get_bills")
    secrecy_level = fields.Selection([
        ('normal', 'Normal'),
        ('confidential', 'Confidential'),
        ('very_confidential', 'Very Confidential'),
    ], default='normal')

    def _get_bills(self):
        bills = []
        if self.ref:
            bills = self.env['account.move'].sudo().search([
                ('id', '=', self.move_id.bill_id.id),
            ])
            if not bills:
                bills = self.env['account.move'].sudo().search([
                    ('move_type', '=', 'in_invoice'),
                    '|', '|',
                    ('ref', '=', self.move_id.ref),
                    ('name', '=', self.move_id.ref),
                    ('payment_reference', '=', self.move_id.ref),
                ])
        if bills and len(bills) == 1:
            self.bill_count = len(bills)
        else:
            self.bill_count = 0



    def action_get_bills(self):
        bills = []
        if self.ref:
            bills = self.env['account.move'].sudo().search([
                ('id', '=', self.move_id.bill_id.id),
            ])
            if not bills:
                bills = self.env['account.move'].sudo().search([
                    ('move_type', '=', 'in_invoice'),
                    '|', '|',
                    ('ref', '=', self.move_id.ref),
                    ('name', '=', self.move_id.ref),
                    ('payment_reference', '=', self.move_id.ref),
                ])
        if bills and len(bills) == 1:
            return {
                'name': _('Bills'),
                'view_mode': 'tree,form',
                'res_model': 'account.move',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', list(set(bills.ids)))],
            }