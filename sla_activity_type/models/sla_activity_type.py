from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SlaActivityType(models.Model):
    _name = 'sla.activity.type'

    code = fields.Char(string="Code")
    name = fields.Char(string="Name")
    description = fields.Char(string="Description")
    default = fields.Boolean(string="Default")
    global_activity_multiplier = fields.Float(string="Global Activity Multiplier")
    model_ids = fields.Many2many('ir.model', string="Model Selector")

    @api.constrains('default')
    def _check_default(self):
        for record in self:
            if record.default == True:
                default = self.env['sla.activity.type'].search([
                    ('id', '!=', record.id),
                    ('default', '=', True)
                ])
                if default:
                    raise ValidationError('Only 1 SLA type can be a default at a time ')
