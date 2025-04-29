from odoo import fields, models, api


class PaymentInstallment(models.Model):
    _name = 'payment.installment'

    installment_amount = fields.Float(string="Installment amount")
    is_paid = fields.Boolean(string="Is Paid")
    approval_request_id = fields.Many2one('approval.request',string="Approval Request")