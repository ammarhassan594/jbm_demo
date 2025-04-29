from odoo import models


class AllowanceRequest(models.Model):
    _name = 'allowance.request'
    _inherit = ['allowance.request', 'dms.integration.mix']
