from odoo import fields, models, api


class DMSAccountMove(models.Model):
    _name = 'account.move'

    _inherit = ['account.move', 'dms.integration.mix']
