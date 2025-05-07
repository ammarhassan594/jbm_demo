from odoo import models, fields, api

class InheritApprovalCategory(models.Model):
    _inherit = 'approval.category'

    create_bill = fields.Boolean(string="Create Bill")