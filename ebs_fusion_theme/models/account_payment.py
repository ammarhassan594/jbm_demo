from odoo import api, fields, models 


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    
    def get_account_payment_chart_data(self, payments_ids=[]):
        payments_ids = self.sudo().browse(payments_ids)
        label = []
        data = []
        for key, value in dict(self.env['account.move']._fields['state'].selection).items():

            label.append(value)
            data.append(len(payments_ids.filtered(lambda o: o.state == key).ids))
        return {
            'label': label,
            'data': data
        }


    def get_account_payment_amount_chart_data(self, payments_amount_ids=[]):
        payments_amount_ids = self.sudo().browse(payments_amount_ids)
        label = []
        data = []
        for key, value in dict(self.env['account.move']._fields['state'].selection).items():
            label.append(value)
            data.append(sum(payments_amount_ids.filtered(lambda o: o.state == key).mapped('amount')))
        return {
            'label': label,
            'data': data
        }