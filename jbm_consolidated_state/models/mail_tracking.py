# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime

from odoo import api, fields, models


class MailTracking(models.Model):
    _inherit = 'mail.tracking.value'

    res_id = fields.Char('Res Id')
    model_name = fields.Char('Model')
    selection_old_value_key = fields.Text('Selection Old Key')
    selection_new_value_key = fields.Text('Selection New Key')
    created_on = fields.Datetime('Created On')

    @api.model
    def create_tracking_values(self, initial_value, new_value, col_name, col_info, tracking_sequence, model_name, res_id=False):
        tracked = True
        print('res_id', res_id)
        field = self.env['ir.model.fields']._get(model_name, col_name)
        if not field:
            return

        values = {'field': field.id, 'field_desc': col_info['string'], 'field_type': col_info['type'], 'tracking_sequence': tracking_sequence}

        if col_info['type'] in ['integer', 'float', 'char', 'text', 'datetime', 'monetary']:
            values.update({
                'old_value_%s' % col_info['type']: initial_value,
                'new_value_%s' % col_info['type']: new_value
            })
        elif col_info['type'] == 'date':
            values.update({
                'old_value_datetime': initial_value and fields.Datetime.to_string(datetime.combine(fields.Date.from_string(initial_value), datetime.min.time())) or False,
                'new_value_datetime': new_value and fields.Datetime.to_string(datetime.combine(fields.Date.from_string(new_value), datetime.min.time())) or False,
            })
        elif col_info['type'] == 'boolean':
            values.update({
                'old_value_integer': initial_value,
                'new_value_integer': new_value
            })
        elif col_info['type'] == 'selection':
            values.update({
                'old_value_char': initial_value and dict(col_info['selection']).get(initial_value, initial_value) or '',
                'new_value_char': new_value and dict(col_info['selection'])[new_value] or '',
                'selection_old_value_key':  initial_value or '',
                'selection_new_value_key': new_value or ''
            })
        elif col_info['type'] == 'many2one':
            values.update({
                'old_value_integer': initial_value and initial_value.id or 0,
                'new_value_integer': new_value and new_value.id or 0,
                'old_value_char': initial_value and initial_value.sudo().name_get()[0][1] or '',
                'new_value_char': new_value and new_value.sudo().name_get()[0][1] or ''
            })
        else:
            tracked = False

        if tracked:
            values.update({
                'res_id': res_id,
                'model_name': model_name,
                'created_on': datetime.now(),
            })
            return values
        return {}
