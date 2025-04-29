from odoo import api, fields, models, _


class ResUsers(models.Model):
    _inherit = 'res.users'

    hubspot_id = fields.Char("Hubspot ID")

    write_capability_ids = fields.Many2many('res.company',string="Write Capabilities CRM")
