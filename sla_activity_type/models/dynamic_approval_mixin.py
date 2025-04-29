from datetime import datetime, timedelta
import logging
from odoo import _, fields, models, api
from odoo.exceptions import UserError, ValidationError
from lxml import etree

_logger = logging.getLogger(__name__)


class InheritDynamicApprovalMixin(models.AbstractModel):
    _inherit = 'dynamic.approval.mixin'

    def action_dynamic_approval_request(self):
        """
        search for advanced approvals that match current record and add approvals
        if record does not match then appear wizard to confirm order without approval
        """
        for record in self:
            company = getattr(record, self._company_field) if self._company_field else False
            if getattr(record, record._state_field) in self._state_from:
                if record.dynamic_approve_request_ids:
                    record.remove_approval_requests()
                    # mark any old activity as done to allow create new activity
                    activity = record._get_user_approval_activities()
                    if activity:
                        activity.action_feedback()
                matched_approval = self.env['dynamic.approval'].action_set_approver(model=self._name, res=record,
                                                                                    company=company)
                if matched_approval:
                    vals = {
                        'approve_requester_id': self.env.user.id,
                        'dynamic_approval_id': matched_approval.id,
                        'state_from_name': getattr(record, record._state_field),
                    }
                    if matched_approval.state_under_approval:
                        vals.update({
                            'state': matched_approval.state_under_approval
                        })
                    record.with_context(force_dynamic_validation=True).write(vals)
                    next_waiting_approval = record.dynamic_approve_request_ids.sorted(lambda x: (x.sequence, x.id))[0]
                    next_waiting_approval.status = 'pending'
                    for user in next_waiting_approval.get_approve_user():
                        number_of_deadline = next_waiting_approval.get_date_deadline_request()
                        date_deadline = fields.Date.context_today(record) + timedelta(days=number_of_deadline)
                        activity_type = next_waiting_approval.get_activity_type_request()
                        record._notify_next_approval_request(matched_approval, user, date_deadline=date_deadline,
                                                             activity_type=activity_type)
                    # if next_waiting_approval and self.approve_requester_id:
                    #     val = {'user_id': self.env.uid,
                    #            'status': 'request_approval',
                    #            'action_date': datetime.now(),
                    #            'sale_id': self.id,
                    #            'sale_order_status': self.state,
                    #            }
                    #     self.approval_history_ids.create(val)
                else:
                    if self._not_matched_action_xml_id:
                        action_id = self._not_matched_action_xml_id
                        action = self.env["ir.actions.act_window"]._for_xml_id(action_id)
                        return action
            else:
                raise UserError(_('This status is not allowed to request approval'))

    def _notify_next_approval_request(self, matched_approval, user, **kwargs):
        """ notify next approval """
        self.ensure_one()
        if matched_approval.need_create_activity_to_approve:
            date_deadline = kwargs.get('date_deadline')
            activity_type = kwargs.get('activity_type')
            self._create_approve_activity(user, date_deadline=date_deadline, activity_type=activity_type)
        if matched_approval.email_template_to_approve_id and user != self.env.user:
            email_values = {'email_to': user.email, 'email_from': self.env.user.email}
            self.dynamic_approval_id.email_template_to_approve_id.with_context(
                name_to=user.name, user_lang=user.lang).send_mail(
                self.id, email_values=email_values, force_send=True)

    def _create_approve_activity(self, user, **kwargs):
        """ create activity based on next user """

        activity_type = kwargs.get('activity_type')
        if not activity_type:
            activity_type = self.env.ref('base_dynamic_approval.mail_activity_type_waiting_approval',
                                         raise_if_not_found=False)
        if activity_type:
            for record in self:
                try:
                    date_deadline = kwargs.get('date_deadline')
                    if date_deadline:
                        record.with_context(mail_activity_quick_update=True).activity_schedule(
                            activity_type_id=activity_type.id,
                            user_id=user.id,
                            summary='للتكرم بمراجعة طلب الموافقة على نظام موارد.',
                            date_deadline=date_deadline
                        )
                    else:
                        record.with_context(mail_activity_quick_update=True).activity_schedule(
                            activity_type_id=activity_type.id,
                            user_id=user.id,
                            summary='للتكرم بمراجعة طلب الموافقة على نظام موارد.'
                        )

                except Exception as error_message:
                    _logger.exception(
                        'Cannot create activity for user %s. error: %s' % (user.name or '', error_message))
