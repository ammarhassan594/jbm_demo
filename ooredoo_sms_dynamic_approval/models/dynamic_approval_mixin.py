from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging
from odoo import _, fields, models, api
from odoo.exceptions import UserError, ValidationError
from lxml import etree

_logger = logging.getLogger(__name__)


class InheritDynamicApprovalMixin(models.AbstractModel):
    _inherit = 'dynamic.approval.mixin'

    def _action_final_approve(self):
        object = super(InheritDynamicApprovalMixin, self)._action_final_approve()
        if self.dynamic_approval_id and self.dynamic_approval_id.model_id and self.dynamic_approval_id.model_id.sms_receiver_id:
            message = "تم إعتماد طلبكم"
            sms_configuration = self.env['dynamic.integration.configuration'].search([
                ('model_id.model', '=', 'hr.employee')
            ])
            if sms_configuration:
                if self.dynamic_approval_id.model_id.sms_receiver_id.relation == 'hr.employee':
                    receiver = getattr(self, self.dynamic_approval_id.model_id.sms_receiver_id.name, None)
                    if receiver:
                        receiver.sudo().with_context(message=message).send_sms_message()

                elif self.dynamic_approval_id.model_id.sms_receiver_id.relation == 'res.users':
                    user = getattr(self, self.dynamic_approval_id.model_id.sms_receiver_id.name, None)
                    if user:
                        employee = self.env['hr.employee'].sudo().search([
                            ('user_id', '=', user.id)
                        ], limit=1)
                        if employee:
                            employee.sudo().with_context(message=message).send_sms_message()

                elif self.dynamic_approval_id.model_id.sms_receiver_id.relation == 'res.partner':
                    partner = getattr(self, self.dynamic_approval_id.model_id.sms_receiver_id.name, None)
                    if partner:
                        user = self.env['res.users'].search([
                            ('partner_id', '=', partner.id)
                        ], limit=1)
                        if user:
                            employee = self.env['hr.employee'].sudo().search([
                                ('user_id', '=', user.id)
                            ], limit=1)
                            if employee:
                                employee.sudo().with_context(message=message).send_sms_message()

        return object
