from odoo import fields, models, api


class DmsAccountPayment(models.Model):
    _name = 'account.payment'
    _inherit = ['account.payment', 'dms.integration.mix']

