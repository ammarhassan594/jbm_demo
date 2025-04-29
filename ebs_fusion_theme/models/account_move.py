from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'


    def get_invoice_chart_data(self, invoice_ids=[]):
        invoice_ids = self.sudo().browse(invoice_ids)
        label = []
        data = []
        for key, value in dict(self._fields['state'].selection).items():
            if key == 'posted':
                label.append('Paid')
                data.append(len(invoice_ids.filtered(lambda o: o.state == key and o.payment_state == 'paid').ids))
                label.append('Waiting for Payment')
                data.append(len(invoice_ids.filtered(lambda o: o.state == key and o.payment_state != 'paid').ids))
            if key == 'cancel':
                label.append(value)
                data.append(len(invoice_ids.filtered(lambda o: o.state == key).ids))

        return {
            'label': label,
            'data': data
        }


    def get_invoice_chart_amount_data(self, invoice_amount_ids=[]):
        invoice_ids = self.sudo().browse(invoice_amount_ids)
        label = []
        data = []
        for key, value in dict(self._fields['state'].selection).items():
            if key == 'posted':
                label.append('Paid')
                data.append(sum(invoice_ids.filtered(lambda o: o.state == key and o.payment_state == 'paid').mapped('amount_total')))
                label.append('Waiting for Payment')
                data.append(sum(invoice_ids.filtered(lambda o: o.state == key and o.payment_state != 'paid').mapped('amount_total')))
            if key == 'cancel':
                label.append(value)
                data.append(sum(invoice_ids.filtered(lambda o: o.state == key).mapped('amount_total')))

        return {
            'label': label,
            'data': data
        }