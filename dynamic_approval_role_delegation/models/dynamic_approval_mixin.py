from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging
from odoo import _, fields, models, api
from odoo.exceptions import UserError, ValidationError
from lxml import etree

_logger = logging.getLogger(__name__)

class InheritDynamicApprovalMixin(models.AbstractModel):
    _inherit = 'dynamic.approval.mixin'

    def action_under_approval(self, note=''):
        """
        change status of approval request to approved and trigger next approval level or change status to be approved
        :param note: approval notes that user will add and store it in approval requests and add it as activity feedback
        """
        for record in self:
            user = self.env.user
            if self.env.user.has_group('base_dynamic_approval.dynamic_approval_user_group'):
                pending_approval = record.dynamic_approve_request_ids.filtered(
                    lambda request_approve: request_approve.status == 'pending')
                if pending_approval:
                    allowed_users = pending_approval.get_approve_user()
                    if allowed_users:
                        user = allowed_users[0]
            pending_approve_request_ids = record._get_pending_approvals(user)
            pending_approve_requests = self.env['dynamic.approval.request'].browse(pending_approve_request_ids)
            if pending_approve_requests:
                pending_approve_requests.write({
                    'approve_date': datetime.now(),
                    'approved_by': self.env.user.id,
                    'status': 'approved',
                })
                if pending_approve_requests[-1].approve_note == 'Role Delegation':
                    pending_approve_requests[-1].write({'approve_note': pending_approve_requests[-1].approve_note + '/' + str(note) if note else pending_approve_requests[-1].approve_note})
                else:
                    pending_approve_requests[-1].write({'approve_note': note})

            activity = record._get_user_approval_activities()
            if activity:
                activity.action_feedback(feedback=note)
            else:
                msg = _('Approved')
                if note:
                    msg += ' ' + note
                record.message_post(body=msg)
            if record.dynamic_approval_id.to_approve_server_action_id:
                action = record.dynamic_approval_id.to_approve_server_action_id.with_context(
                    active_model=self._name,
                    active_ids=[record.id],
                    active_id=record.id,
                    force_dynamic_validation=True,
                )
                try:
                    action.run()
                except Exception as e:
                    _logger.warning(
                        'Approval Recall: record <%s> model <%s> encountered server action issue %s',
                        record.id, record._name, str(e), exc_info=True)
            new_approve_requests = \
                record.dynamic_approve_request_ids.filtered(lambda approver: approver.status == 'new')
            if new_approve_requests:
                next_waiting_approval = new_approve_requests.sorted(lambda x: (x.sequence, x.id))[0]
                next_waiting_approval.status = 'pending'
                if next_waiting_approval.get_approve_user():
                    users = next_waiting_approval.get_approve_user()
                    for user in users:
                        number_of_deadline = next_waiting_approval.get_date_deadline_request()
                        date_deadline = fields.Date.context_today(record) + timedelta(days=number_of_deadline)
                        record._notify_next_approval_request(record.dynamic_approval_id, user, date_deadline=date_deadline)
            else:
                record._action_final_approve()