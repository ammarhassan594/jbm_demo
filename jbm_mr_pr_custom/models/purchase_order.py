from odoo import models, fields, api, _

class InheritApprovals(models.Model):

    _inherit = 'purchase.order'

    mr_request_id = fields.Many2one('approval.request')
    mr_user_id = fields.Many2one('res.users')

