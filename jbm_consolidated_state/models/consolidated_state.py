from odoo import models, fields, api


class ConsolidatedState(models.Model):
    _name = 'consolidated.state'
    _rec_name = 'model_id'

    model_id = fields.Many2one('ir.model', string="Model")
    consolidated_state_line_ids = fields.One2many('consolidated.state.line', 'consolidated_id', copy=True)
    consolidated_state_condition_ids = fields.One2many('consolidated.model.condition', 'consolidated_configuration_id', copy=True)
    record_identifier_api = fields.Many2one('ir.model.fields', string="Identifier Api", copy=True)
    requestor_field_id = fields.Many2one('ir.model.fields', string="Requestor Field", copy=True)


