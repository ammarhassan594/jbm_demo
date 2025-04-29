from odoo import fields, models, api


class DmsPurchaseRequisition(models.Model):
    _name = 'purchase.requisition'
    _inherit = ['purchase.requisition', 'dms.integration.mix']

