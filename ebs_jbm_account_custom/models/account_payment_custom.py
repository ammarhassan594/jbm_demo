# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import logging
from dateutil.relativedelta import relativedelta
from odoo import _, fields, models, api
from odoo.addons.test_convert.tests.test_env import field
from odoo.addons.test_impex.tests.test_load import message
from odoo.exceptions import UserError, ValidationError
from odoo.tools import consteq, format_amount, ustr


_logger = logging.getLogger(__name__)


class AccountPaymentCustom(models.Model):
    _name = 'account.payment'
    _inherit = ['account.payment', 'dynamic.approval.mixin', 'mail.thread', 'mail.activity.mixin']
    _state_from = ['draft']
    _state_to = ['posted']

    case_number = fields.Char(string="Case Number")

    def _notify_next_approval_request(self, matched_approval, user, **kwargs):
        """ notify next approval """
        self.ensure_one()
        if matched_approval.need_create_activity_to_approve:
            date_deadline = kwargs.get('date_deadline')
            self._create_approve_activity(user, date_deadline=date_deadline)
        if matched_approval.email_template_to_approve_id and user != self.env.user:
            email_values = {'email_to': user.email, 'email_from': self.env.user.email}
            self.dynamic_approval_id.email_template_to_approve_id.with_context(
                name_to=user.name, user_lang=user.lang).send_mail(
                self.id, email_values=email_values, force_send=True)
        if self._name == 'account.payment':
            currency = self.env.company.currency_id  # or use self.currency_id if available

            # Format the amount as currency
            formatted_amount = format_amount(self.env, self.amount, self.currency_id)
            message = "تم طلب اعتماد الدفعة المالية بمبلغ : ({}) للمستفيد : ({}), يرجى مراجعة الطلب في نظام موارد".format(formatted_amount, self.partner_id.with_context(lang='ar_001').name)
            employee = self.env['hr.employee'].search([('user_id', '=', user.id)])
            if employee:
                employee.sudo().with_context(message=message).send_sms_message()


    # def action_dynamic_approval_request(self):
    #     """
    #     Override this stop approval request on recurring payment
    #     """
    #     if self._name == 'account.payment':
    #         for record in self:
    #             company = getattr(record, self._company_field) if self._company_field else False
    #             if getattr(record, record._state_field) in self._state_from:
    #                 if record.recurring:
    #                     if record.env.context.get('lang') == 'ar_001':
    #                         raise ValidationError(_(f"  لا يمكن طلب موافقة على هذا الدفع لأنه متكرر "))
    #                     else:
    #                         raise ValidationError(_('You cannot request approval for '
    #                                                 'recurring payment'))
    #                 if record.dynamic_approve_request_ids:
    #                     record.remove_approval_requests()
    #                     # mark any old activity as done to allow create new activity
    #                     activity = record._get_user_approval_activities()
    #                     if activity:
    #                         activity.action_feedback()
    #                 matched_approval = self.env['dynamic.approval'].action_set_approver(model=self._name, res=record,
    #                                                                                     company=company)
    #                 if matched_approval:
    #                     vals = {
    #                         'approve_requester_id': self.env.user.id,
    #                         'dynamic_approval_id': matched_approval.id,
    #                         'state_from_name': getattr(record, record._state_field),
    #                     }
    #                     if matched_approval.state_under_approval:
    #                         vals.update({
    #                             'state': matched_approval.state_under_approval
    #                         })
    #                     record.with_context(force_dynamic_validation=True).write(vals)
    #                     next_waiting_approval = record.dynamic_approve_request_ids.sorted(lambda x: (x.sequence, x.id))[
    #                         0]
    #                     next_waiting_approval.status = 'pending'
    #                     if next_waiting_approval.get_approve_user():
    #                         user = next_waiting_approval.get_approve_user()[0]
    #                         number_of_deadline = next_waiting_approval.get_date_deadline_request()
    #                         # date_deadline = fields.Date.context_today(record) + timedelta(days=number_of_deadline)
    #                         date_deadline = fields.Date.context_today(record)
    #
    #                         employee = self.env['hr.employee'].sudo().search([
    #                             ('user_id', '=', user.id) if user else False
    #                         ])
    #                         if employee:
    #                             contract = employee.active_contract if employee.active_contract else False
    #                             if contract:
    #                                 for day in range(int(number_of_deadline)):
    #                                     date = date_deadline + relativedelta(days=1)
    #                                     weekend = str(date.weekday()) not in set(
    #                                         contract.resource_calendar_id.attendance_ids.mapped('dayofweek'))
    #
    #                                     public_holiday = contract.resource_calendar_id.global_leave_ids.filtered(
    #                                         lambda x: x.date_from.date() <= date <= x.date_to.date())
    #
    #                                     while weekend or public_holiday:
    #                                         date = date + relativedelta(days=1)
    #                                         weekend = str(date.weekday()) not in set(
    #                                             contract.resource_calendar_id.attendance_ids.mapped('dayofweek'))
    #                                         public_holiday = contract.resource_calendar_id.global_leave_ids.filtered(
    #                                             lambda x: x.date_from.date() <= date <= x.date_to.date())
    #
    #                                     if not weekend and not public_holiday:
    #                                         date_deadline = date
    #
    #                         record._notify_next_approval_request(matched_approval, user, date_deadline=date_deadline)
    #                 else:
    #                     if self._not_matched_action_xml_id:
    #                         action_id = self._not_matched_action_xml_id
    #                         action = self.env["ir.actions.act_window"]._for_xml_id(action_id)
    #                         return action
    #             else:
    #                 raise UserError(_('This status is not allowed to request approval'))
    #     else:
    #         super(AccountPaymentCustom, self).action_dynamic_approval_request()

    # @api.constrains('case_number')
    # def check_case_number(self):
    #     for record in self:
    #         if len(self.search([]).filtered(lambda s: s.case_number == record.case_number)) > 1:
    #             raise UserError('Case Number must be unique')
