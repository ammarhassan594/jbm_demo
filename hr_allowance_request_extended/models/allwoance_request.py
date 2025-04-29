import logging
from odoo import models, fields, api, _
from datetime import datetime
_logger = logging.getLogger(__name__)


class Allowances(models.Model):
    _name = 'allowance.request'
    _inherit = ['allowance.request', 'dynamic.approval.mixin']
    _state_field = "state"
    _state_from = ['confirmed', 'refused']
    _state_to = ['approved', 'paid']
    _cancel_state = "refused"


    def _action_final_approve(self):
        """ mark order as approved """
        self.ensure_one()
        self._run_final_approve_function()
        if self._name == 'allowance.request':
            # Todo : I hade to fix this Moahamed rabiea, please check it.
            self.write({
                self._state_field: self._state_to[0] if self.code in ['ticket', 'furniture', 'maintenance'] else self._state_to[1],
                'final_approve_date': fields.Date.today()
            })
            # self.action_server_approved_allowance()
            # create activity based on setting
            if self.dynamic_approval_id and self.dynamic_approval_id.default_notify_user_field_after_final_approve_id:
                self._create_done_approve_activity(
                    getattr(self, self.dynamic_approval_id.default_notify_user_field_after_final_approve_id.name))
            # send email to users
            if self.dynamic_approval_id and self.dynamic_approval_id.notify_user_field_after_final_approve_ids and \
                    self.dynamic_approval_id.email_template_after_final_approve_id:
                users_to_send = self.env['res.users']
                for user_field in self.dynamic_approval_id.notify_user_field_rejection_ids:
                    users_to_send |= getattr(self, user_field.name)
                # not send email for same user twice
                users_to_send = self.env['res.users'].browse(users_to_send.mapped('id'))
                for user in users_to_send:
                    if user != self.env.user and user.email:
                        email_values = {'email_to': user.email, 'email_from': self.env.user.email}
                        self.dynamic_approval_id.email_template_after_final_approve_id.with_context(
                            name_to=user.name, user_lang=user.lang).send_mail(self.id, email_values=email_values,
                                                                              force_send=True)

            if self.dynamic_approval_id and self.dynamic_approval_id.after_final_approve_server_action_id:

                action = self.dynamic_approval_id.after_final_approve_server_action_id.with_context(
                    active_model=self._name,
                    active_ids=[self.id],
                    active_id=self.id,
                    force_dynamic_validation=True,
                )

                try:
                    action.run()

                except Exception as e:
                    _logger.warning('Approval Rejection: record <%s> model <%s> encountered server action issue %s',
                                    self.id, self._name, str(e), exc_info=True)

        else:
            super(Allowances, self)._action_final_approve()



    def _action_reset_original_state(self, reason='', reset_type='reject'):
        """
        set record to original state and notify user or approvers
        :param reason: reason for reset
        :param reset_type: reject / recall
        :param notify_approver: notify users who approved before
        """
        if self._name == 'allowance.request':
            # Todo : I hade to fix this Moahamed rabiea, please check it.
            self.sudo().write({
                self._state_field: self._cancel_state,
                # 'final_approve_date': fields.Date.today()
            })
        return super(Allowances, self)._action_reset_original_state(reason='', reset_type='reject')



