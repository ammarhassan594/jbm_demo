from odoo import models, fields, api


class InheritDynamicApprovalLevel(models.Model):
    _inherit = 'dynamic.approval.level'

    activity_type_id = fields.Many2one('mail.activity.type', string="Activity Type")
