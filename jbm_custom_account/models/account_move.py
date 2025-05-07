from odoo import models, fields, api, _

class InheritAccountMove(models.Model):
    _inherit = 'account.move'

    payment_count = fields.Integer(compute="_get_payments")
    secrecy_level = fields.Selection([
        ('normal', 'Normal'),
        ('confidential', 'Confidential'),
        ('very_confidential', 'Very Confidential'),
    ],default='normal')

    bill_id = fields.Many2one('account.move')





    def _get_payments(self):
        payments = []
        if self.payment_reference:
            payments = self.env['account.move'].sudo().search([
                ('bill_id', '=', self.id)]).mapped('payment_id')
            if not payments:
                payments = self.env['account.move'].sudo().search([
                    ('move_type', '=', 'entry'),
                    ('name', '=', '/'),
                    ('ref', '=', self.payment_reference),
                ]).mapped('payment_id')

        elif self.ref:
            payments = self.env['account.move'].sudo().search([
                ('bill_id', '=', self.id)]).mapped('payment_id')
            if not payments:
                payments = self.env['account.move'].sudo().search([
                    ('move_type', '=', 'entry'),
                    ('name', '=', '/'),
                    ('ref', '=', self.ref),
                ]).mapped('payment_id')
        else:
            payments = self.env['account.move'].sudo().search([
                ('bill_id', '=', self.id)]).mapped('payment_id')
            if not payments:
                payments = self.env['account.move'].sudo().search([
                    ('move_type', '=', 'entry'),
                    ('name', '=', '/'),
                    ('ref', '=', self.name),
                ]).mapped('payment_id')

        if payments:
            self.payment_count = len(payments)
        else:
            self.payment_count = 0



    def action_get_payments(self):
        payments = []
        if self.payment_reference:
            payments = self.env['account.move'].sudo().search([
                ('bill_id', '=', self.id)]).mapped('payment_id')
            if not payments:
                payments = self.env['account.move'].sudo().search([
                    ('move_type', '=', 'entry'),
                    ('name', '=', '/'),
                    ('ref', '=', self.payment_reference),
                ]).mapped('payment_id')

        elif self.ref:
            payments = self.env['account.move'].sudo().search([
                ('bill_id', '=', self.id)]).mapped('payment_id')
            if not payments:
                payments = self.env['account.move'].sudo().search([
                    ('move_type', '=', 'entry'),
                    ('name', '=', '/'),
                    ('ref', '=', self.ref),
                ]).mapped('payment_id')
        else:
            payments = self.env['account.move'].sudo().search([
                ('bill_id', '=', self.id)]).mapped('payment_id')
            if not payments:
                payments = self.env['account.move'].sudo().search([
                    ('move_type', '=', 'entry'),
                    ('name', '=', '/'),
                    ('ref', '=', self.name),
                ]).mapped('payment_id')
        if payments:
            return {
                'name': _('Payments'),
                'view_mode': 'tree,form',
                'res_model': 'account.payment',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', list(set(payments.ids)))],
            }