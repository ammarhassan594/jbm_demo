from odoo import models, fields, api, _


class InheritAllowanceType(models.Model):
    _inherit = 'allowance.type'

    condition_ids = fields.One2many('allowance.type.conditions', 'allowance_type_id', string="Conditions")
