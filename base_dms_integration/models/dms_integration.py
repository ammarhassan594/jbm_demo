from logging import getLogger
from odoo import fields, models, api

_logger = getLogger(__name__)
import json
import re


class DmsIntegration(models.Model):
    _name = 'dms.integration'
    _description = 'DMS Integration'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _get_status_domain(self):
        """Get the status values form field state on model"""
        if self.field_state_id and self.model_id:
            res = self.env[self.model_id.model].sudo()
            if hasattr(res, self.field_state_id.name) and \
                    isinstance(res._fields[self.field_state_id.name], fields.Selection):
                status_values_sudo = self.env['status.values'].sudo()
                status_values = status_values_sudo.get_status_values(self.model_id.id, self.field_state_id.id)
                if status_values:
                    return {
                        'domain': {
                            'state_value_id': [('id', 'in', status_values)]
                        },
                    }
                else:
                    list_vals = [
                        {
                            "state_value_db": key,
                            "state_value_ui": val,
                            "model_id": self.model_id.id,
                            "state_field_id": self.field_state_id.id,
                        } for (key, val)
                        in dict(self.env[self.model_id.model].
                                fields_get([self.field_state_id.name])
                                [self.field_state_id.name][
                                    'selection']).items()
                    ]
                    status_values = status_values_sudo.create_status_values(list_vals)
                    return {
                        'domain': {
                            'state_value_id': [('id', 'in', status_values)]
                        },

                    }
            else:
                return {
                    'domain': {
                        'state_value_id': [('id', '=', False)]
                    },
                }

    model_id = fields.Many2one('ir.model', string='Model',
                               tracking=True, index=True, ondelete='cascade')
    report_id = fields.Many2one('ir.actions.report')

    field_state_id = fields.Many2one('ir.model.fields', string='State', help='Select State Field')
    state_value_id = fields.Many2one('status.values', string='Value Of Status')

    content_type_id = fields.Many2one('dms.content.type',
                                      string='Content type')

    api_method = fields.Selection([
        ('put', 'PUT'),
        ('post', 'POST')
    ], string='API Type', default='post')
    url = fields.Char('URl')
    send_attachments = fields.Boolean('Send Attachments')
    use_odoo_name = fields.Boolean('Use Odoo Name', default=True)
    file_name = fields.Char('Default File Name')
    send_datetime = fields.Boolean('Send Datetime',
                                   help='Select can be sending datetime or not ')

    dms_field_ids = fields.One2many('dms.fields', 'dms_api_id')

    dms_temporary_ids = fields.One2many('dms.temporary', 'dms_api_id')

    dms_condition_ids = fields.One2many('dms.model.condition', 'dms_configuration_id')

    @api.onchange('model_id')
    def _onchange_model_id(self):
        self.report_id = None
        if self.model_id is not None:
            _logger.info('model_id changed {}'.format(self.model_id))
            model_name = self.model_id.model
            return \
                {
                    'domain': {
                        'report_id': ['|', ('model', '=', model_name), ('model_id', '=', self.model_id.id)]
                    },
                }
        else:
            return \
                {
                    'domain': {
                        'report_id': [('id', '=', False)],
                    },
                }

    @api.onchange('field_state_id', 'model_id')
    def _onchange_model_field_state(self):
        return self._get_status_domain()

    def is_matched_dms(self, res):
        """ return True / False based on the DMS configuration match record condition """
        self.ensure_one()
        for condition in self.dms_condition_ids:
            if not condition.is_condition_matched(res=res):
                return False
        return True

    def delete_unsuccessful_requests(self):
        self.dms_temporary_ids.write({'request': False})

    def dms_temporary_old_data(self):
        for line in self.dms_temporary_ids:
            try:
                text = re.compile('<.*?>')
                message = re.sub(text, '', line.response)
                line_response = json.loads(message)
                if line_response.get('UploadSingleFileResult') and \
                        line_response.get('UploadSingleFileResult').get('Code') == 'OK':
                    line.request = False
            except Exception as e:
                continue


class DmsContentType(models.Model):
    _name = 'dms.content.type'

    name = fields.Char(required=True)


class StatusValues(models.Model):
    _name = 'status.values'
    _description = 'Status Values for saving the status of the state field in the model'
    _rec_name = 'state_value_ui'

    state_value_db = fields.Char('Value on DB', help='Value which save on DB')
    state_value_ui = fields.Char('Value on UI', help='Value which display on UI')
    state_field_id = fields.Many2one('ir.model.fields', string='Field State',
                                     help='Field State', ondelete='cascade')
    model_id = fields.Many2one('ir.model', ondelete='cascade')

    def create_status_values(self, val_list: list):
        """Create a list of status values for the status field on model.
        @param val_list: list must be a list of values like
            [
                {
                    'model_id': model_id,
                    'state_value_db': value_db,
                    'state_value_ui': value_ui,
                    'state_field_id': field_id,
                },
            ]

        """
        assert isinstance(val_list, list)
        status_value_sudo = self.sudo()
        status_values = status_value_sudo.create(val_list)
        return status_values.ids

    def get_status_values(self, model_id: int, state_field_id: int):
        """Get a list of status values which added to model_id
        @param model_id is an id of model
        @param state_field_id is an id of state field on a model
        """
        assert isinstance(model_id, int)
        assert isinstance(state_field_id, int)
        status_value_sudo = self.sudo()
        status_value_sudo._cr.execute(
            "SELECT id FROM status_values WHERE model_id = %s AND state_field_id = %s"
            % (model_id, state_field_id)
        )
        return [r[0] for r in status_value_sudo._cr.fetchall()]
