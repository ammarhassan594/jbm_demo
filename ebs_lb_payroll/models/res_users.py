from odoo import fields, models, api, _


class ResUsers(models.Model):
    _inherit = 'res.users'

    sign_signature = fields.Binary(string="Digital Signature", groups="base.group_user")
