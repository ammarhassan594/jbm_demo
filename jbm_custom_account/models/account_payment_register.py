from odoo import models, fields, api, _

class InheritAccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    bill_id = fields.Many2one('account.move')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self._context.get('active_model') == 'account.move':
            res['bill_id'] = self.env['account.move'].browse(self._context.get('active_ids', []))
        return res

    def _create_payments(self):
        res = super(InheritAccountPaymentRegister, self)._create_payments()
        res.move_id.write({
            'bill_id': self.bill_id.id
        })
        return res
