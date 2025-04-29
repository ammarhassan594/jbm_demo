from odoo import fields, models, api


class EventTypeCustom(models.Model):
    _inherit = 'sap.event.type'

    is_related_transfer = fields.Boolean(
        string='Is Related to Transfer',
        required=False, default=False)
