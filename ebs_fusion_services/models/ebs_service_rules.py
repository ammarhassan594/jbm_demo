from odoo import api, fields, models, _

class ebsServiceRules(models.Model):
    _name = 'ebs.service.rules'
    _description = 'EBS Service Rules'

    name = fields.Char(string="Name")
    filter_ids = fields.One2many('ebs.service.rules.filters', 'rule_id', string="Filteres")
    err_msg = fields.Text('Error Message')
    server_action_id = fields.Many2one('ir.actions.server', string="Server Action")


class ebsServiceRulesFilters(models.Model):
    _name = 'ebs.service.rules.filters'
    _description = 'EBS Service Rules Filters'

    target_model = fields.Many2one('ir.model', string="Model")
    filter = fields.Char(string="Filter")
    rule_id = fields.Many2one('ebs.service.rules')
