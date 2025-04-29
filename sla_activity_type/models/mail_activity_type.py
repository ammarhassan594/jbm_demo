from odoo import models, fields, api
from odoo.exceptions import ValidationError


class InheritMailActivityType(models.Model):
    _inherit = 'mail.activity.type'

    sla_type_id = fields.Many2one('sla.activity.type', string="SLA Type", domain="[('default', '=', False)]")
    multiplier = fields.Float(string="Multiplier")
    code = fields.Char(string="Code")

    @api.constrains('multiplier')
    def _check_multiplier(self):
        for record in self:
            if record.multiplier < 0.0:
                raise ValidationError('Multiplier Must be Greater Than 0.0!')
