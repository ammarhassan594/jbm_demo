from odoo import models, fields, api


class InheritApprovalCategoryApprover(models.Model):
    _inherit = 'approval.category.approver'

    activity_type_id = fields.Many2one('mail.activity.type', string="Activity Type")
