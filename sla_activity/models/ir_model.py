from odoo import models, fields, api, _


class InheritIrModel(models.Model):
    _inherit = 'ir.model'
    record_identifier_api = fields.Many2one('ir.model.fields', string="Identifier Api")
    requestor_field_id = fields.Many2one('ir.model.fields', string="Requestor Field")
    subject_field_id = fields.Many2one('ir.model.fields', string="Subject Field")
    model_type = fields.Selection([
        ('internal', 'Internal'),
        ('self_service', 'Self-Service'),
    ], string="Model Type")
    state_field_id = fields.Many2one('ir.model.fields', string="State Field")
    value_state_field = fields.Many2one('ir.model.fields.selection', domain=[('id', '=', False)])

    @api.onchange('state_field_id')
    @api.depends('state_field_id')
    def _get_value_state_field(self):
        for record in self:
            if record.state_field_id and record.state_field_id.selection_ids:
                return {
                    'domain': {
                        'value_state_field': [('id', 'in', record.state_field_id.selection_ids.ids)]
                    },
                }
            else:
                return {
                    'domain': {
                        'value_state_field': [('id', '=', False)]
                    },
                }
