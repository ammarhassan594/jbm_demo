import logging
import datetime
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.safe_eval import safe_eval, time

_logger = logging.getLogger(__name__)


def evaluate_python_code(record=None, python_code=''):
    """Return the value of python expression

    @param record: The object to evaluate expression from it
    @param python_code: Python expression

    @return: The value of python expression if found, else False and error message
    @retype: float, str
    """
    if not python_code or not record:
        return False
    record_sudo = record.sudo()
    try:
        localdict = {
            'time': time,
            'context_today': datetime.datetime.now,
            'user': record_sudo.env.user,
            'record': record_sudo,
            'env': record_sudo.env
        }
        # result = env['ir.config_parameter'].sudo().get_param('attendance_api_token')
        safe_eval(python_code, localdict, mode="exec", nocopy=True)
        test = None
        message = ''
        if "result" in localdict:
            test = localdict.get('result', False)
        else:
            message = 'Please check expression as mentioned before must be write result'
    except Exception as e:
        _logger.warning(e)
        message = str(e)
        test = None
    return test, message


class SlaActivityWizard(models.TransientModel):
    _name = 'sla.activity.wizard'
    _description = 'SLA Activity Wizard'

    @api.model
    def _get_sla_activity_type_domain(self):
        model_id = self.env['ir.model'].search([
            ('model', '=', self._context.get('default_res_model', False))
        ])
        return [('default', '!=', True), '|', ('model_ids', 'in', model_id.ids), ('model_ids', '=', False)]

    sla_activity_type_id = fields.Many2one('sla.activity.type', required=True,
                                           domain=_get_sla_activity_type_domain)

    def action_apply(self):
        model_id = self.env['ir.model'].search([
            ('model', '=', self._context.get('default_res_model', False))
        ])
        if not model_id:
            _logger.info("No model found on context")
            return {'type': 'ir.actions.act_window_close'}
        current_record = self.env[model_id.model].browse(self._context.get('default_res_id', False))
        if not current_record:
            _logger.info("Can not fetch record from context")
            return {'type': 'ir.actions.act_window_close'}

        if not model_id.manager_expression:
            raise ValidationError(
                _('No manager to send activity to it, please set manager on model %s,' % model_id.name))

        user, message = evaluate_python_code(current_record,
                                             python_code=model_id.manager_expression)

        if user is None and message:
            raise ValidationError(_('Wrong Python expression\n'
                                    f'{message}'))

        activity_type_id = self.env['mail.activity.type'].search([
            ('sla_type_id', '=', self.sla_activity_type_id.id)
        ], limit=1)
        if not activity_type_id:
            raise ValidationError(_('The selected SLA Type does not have an activity type'))

        current_record.with_context(mail_activity_quick_update=True).activity_schedule(
            activity_type_id=activity_type_id.id,
            user_id=user.id,
            summary='Approval needed for {}'.format(current_record.display_name),
        )
