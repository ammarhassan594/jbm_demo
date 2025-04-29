from odoo import models, fields, api, _
from datetime import datetime, date
from dateutil.relativedelta import relativedelta


class Payments(models.Model):
    _inherit = "account.payment"

    type = fields.Selection(string="Scheduled ?", default="not_scheduled",
                            selection=[('not_scheduled', 'Not Scheduled'), ('scheduled', 'Scheduled')])

    @api.model
    def _create_scheduled_payment(self):
        vals_list = []
        payment_obj = self.env['account.payment']
        today = date.today()
        scheduled_payments = payment_obj.search(
            [('type', '=', 'scheduled'), ('recurring', '=', True), ('end_date', '>=', today),
             ('state', '=', 'recurring_approved')])
        for payment in scheduled_payments:
            if payment.recurring_every and \
                    ((today.year - payment.date.year) * 12 + \
                     (today.month - payment.date.month)) % payment.recurring_every == 0:
                next_recurring_no = (today.month - payment.date.month) / payment.recurring_every
                next_payment_date = payment.date + relativedelta(months=(next_recurring_no * payment.recurring_every))
                if next_payment_date == today:
                    vals_list.append({
                        'is_internal_transfer': payment.is_internal_transfer,
                        'payment_type': payment.payment_type,
                        'partner_id': payment.partner_id.id if payment.partner_id else None,
                        'amount': payment.amount,
                        'journal_id': payment.journal_id.id,
                        'payment_method_line_id': payment.payment_method_line_id.id if payment.payment_method_line_id else None,
                        'date': date.today(),
                        'ref': payment.ref,
                        'is_post_dated_check': payment.is_post_dated_check,
                        'recurring_payment_id': payment.id,
                        'case_number': payment.case_number,
                        'purpose_of_transfer': payment.purpose_of_transfer,
                        'iban_number': payment.iban_number,
                        'qid_number': payment.qid_number,
                        'case_name': payment.case_name,
                        'partner_bank_id': payment.partner_bank_id.id if payment.partner_bank_id else None,

                    })

        self.env['account.payment'].create(vals_list)


def _create_activity_for_accountant(self, users, payment):
    for user in users:
        payment.with_context(mail_activity_quick_update=True).activity_schedule(
            date_deadline=fields.Date.today(),
            activity_type_id=self.env.ref('mail.mail_activity_data_todo',
                                          raise_if_not_found=False).id,
            summary='تم إنشاء دفعة مجدولة في نظام موارد.', user_id=user.id)


def _create_activity_for_accounting_mangers(self, users, payment):
    for user in users:
        payment.with_context(mail_activity_quick_update=True).activity_schedule(
            date_deadline=fields.Date.today(),
            activity_type_id=self.env.ref('mail.mail_activity_data_todo',
                                          raise_if_not_found=False).id,
            summary='تم انشاء رقم للسجل المذكور.', user_id=user.id)


@api.model_create_multi
def create(self, vals_list):
    obj = super(Payments, self).create(vals_list)
    # accountant_role_users = self.env.ref('jbm_group_access_right_extended.custom_accountant_role_manager').users
    # if accountant_role_users:
    #     obj._create_activity_for_accountant(accountant_role_users, obj)
    old_case_number = obj.search([('id', '!=', obj.id)])
    if old_case_number:
        check_case_number_existence = old_case_number.filtered(
            lambda x: x.case_number and x.case_number == obj.case_number)
        if check_case_number_existence:
            accounting_manager_role_users = self.env.ref(
                'jbm_group_access_right_extended.custom_accounting_manager').users
            if accounting_manager_role_users:
                obj._create_activity_for_accounting_mangers(accounting_manager_role_users, obj)
    return obj
