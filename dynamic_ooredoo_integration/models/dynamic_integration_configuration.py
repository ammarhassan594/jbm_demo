import os
import inspect
import subprocess


from odoo import models, fields, api, _

class DynamicIntegrationDocument(models.Model):
    _name = 'dynamic.integration.configuration'
    _description = 'Configuration of Dynamic Integration'
    _order = 'id'

    _message = """f'hello {self.name}'"""

    @api.model
    def _get_dynamic_integration_model_names(self):
        res = []
        return res

    model_id = fields.Many2one(comodel_name='ir.model',
                               string='Model',
                               required=True,
                               ondelete='cascade',
                               domain=lambda self: [('model', 'in', self._get_dynamic_integration_model_names())],)

    name = fields.Char(
        string='Description',
        required=True,
        translate=True,
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.company,
    )

    active = fields.Boolean(
        default=True
    )

    message_template = fields.Text(default=_message, store=True, string="Message Template")

    trigger_server_action_id = fields.Many2one(
        comodel_name='ir.actions.server',
    )

    model = fields.Char(
        related='model_id.model',
        index=True,
        store=True
    )

    field_ids = fields.Many2many('ir.model.fields')
    action_field = fields.Many2one('ir.model.fields')
    action_field_value = fields.Char(string="Value")
    http_proxy = fields.Char(string="HTTP Proxy")
    https_proxy = fields.Char(string="HTTPS Proxy")

    _sql_constraints = [
        ('dynamic_integration_model_unique', 'UNIQUE (model_id)',
         "Can't configure multiple dynamic integration on same target model!"),
    ]

    @api.onchange('model_id')
    @api.depends('model_id')
    def onchange_model(self):
        return {'domain': {
            'field_ids': [('model_id', '=', self.model_id.id)],
            'action_field': [('model_id', '=', self.model_id.id)]
        }}


#     @api.model
#     def create(self, vals):
#         current_path =inspect.getmodule(inspect.currentframe()).__file__
#         current_path = os.path.dirname(os.path.abspath(current_path))
#         model = self.env['ir.model'].search([
#             ('id', '=', vals['model_id'])
#         ]).model
#         content = '''
# from odoo import models, fields, api
#
# class DynamicModel(models.Model):
#     _name = '{model_name}'
#     _inherit = ['{model_name}', 'dynamic.integration.mix']
#             '''.format(model_name=model)
#         file_path = '/path/to/save/dynamic_model.py'
#         model = model.replace(".", "_")
#         module_path = current_path + '/' +str(model) + '.py'
#         print('current_path:::', module_path)
#         with open(module_path, 'w') as file:
#             file.write(content)
#         init_path = current_path + '/' + '__init__.py'
#         import_statement = 'from . import ' + str(model)
#
#         with open(init_path, 'a') as file:
#             file.write("\n")
#             file.write(import_statement)
#
#         command = "systemctl list-units | grep odoo"
#         result = subprocess.run(command, shell=True, capture_output=True, text=True)
#         output = result.stdout.strip()
#         print('output:::', result)
#         return super(DynamicIntegrationDocument, self).create(vals)

