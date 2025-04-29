import logging
from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)

class HrPayslipRun(models.Model):
    _name = 'hr.payslip.run'
    _inherit = ['hr.payslip.run', 'mail.thread', 'mail.activity.mixin']


    state = fields.Selection(selection_add=[('approve', 'Approved by HR'),
                                            ('by_hr', 'Approved by HR'),
                                            ('by_finance', 'Approved By Finance'), ('close',)])
    employee_type = fields.Selection([('fos_employee', 'Outsourced Employee'),
                                      ('fusion_employee', 'Main Company Employee'),
                                      ], string="Employee Type")

    is_finance_approve = fields.Boolean("Is Finance Approve", copy=False)
    cust_off_date_from = fields.Date()
    cust_off_date_to = fields.Date()

    @api.constrains('cust_off_date_from', 'cust_off_date_to')
    def _check_start_end_date(self):
        for record in self:
            if record.cust_off_date_from and record.cust_off_date_to and record.cust_off_date_from > record.cust_off_date_to:
                raise ValidationError("Cut-off Start date Can't be greater than the end date")
            date_start = record.cust_off_date_from + relativedelta(months=1)
            date_end = date_start + relativedelta(days=-1)
            if record.cust_off_date_to != date_end:
                raise ValidationError(_("Cut-off day End Must be %s") % date_end)


    # def _action_final_approve(self):
    #     """ mark order as approved """
    #     self.ensure_one()
    #     self._run_final_approve_function()
    #     if self._name == 'hr.payslip.run':
    #         print('payslipssssss')
    #         self.action_finance_confirm()
    #         # Todo : I hade to fix this Moahamed rabiea, please check it.
    #         self.write({
    #             self._state_field: self._state_to[0]
    #         })
    #         # self.action_server_approved_allowance()
    #         # create activity based on setting
    #         if self.dynamic_approval_id and self.dynamic_approval_id.default_notify_user_field_after_final_approve_id:
    #             self._create_done_approve_activity(
    #                 getattr(self, self.dynamic_approval_id.default_notify_user_field_after_final_approve_id.name))
    #         # send email to users
    #         if self.dynamic_approval_id and self.dynamic_approval_id.notify_user_field_after_final_approve_ids and \
    #                 self.dynamic_approval_id.email_template_after_final_approve_id:
    #             users_to_send = self.env['res.users']
    #             for user_field in self.dynamic_approval_id.notify_user_field_rejection_ids:
    #                 users_to_send |= getattr(self, user_field.name)
    #             # not send email for same user twice
    #             users_to_send = self.env['res.users'].browse(users_to_send.mapped('id'))
    #             for user in users_to_send:
    #                 if user != self.env.user and user.email:
    #                     email_values = {'email_to': user.email, 'email_from': self.env.user.email}
    #                     self.dynamic_approval_id.email_template_after_final_approve_id.with_context(
    #                         name_to=user.name, user_lang=user.lang).send_mail(self.id, email_values=email_values,
    #                                                                           force_send=True)
    #
    #         if self.dynamic_approval_id and self.dynamic_approval_id.after_final_approve_server_action_id:
    #
    #             action = self.dynamic_approval_id.after_final_approve_server_action_id.with_context(
    #                 active_model=self._name,
    #                 active_ids=[self.id],
    #                 active_id=self.id,
    #                 force_dynamic_validation=True,
    #             )
    #
    #             try:
    #                 action.run()
    #
    #             except Exception as e:
    #                 _logger.warning('Approval Rejection: record <%s> model <%s> encountered server action issue %s',
    #                                 self.id, self._name, str(e), exc_info=True)
    #
    #     else:
    #         super(HrPayslipRun, self)._action_final_approve()
    #
    #
    #
    # def action_validate(self):
    #     res = super(HrPayslipRun, self).action_validate()
    #     self.state = 'by_finance'
    #     return res

    # def compute_sheet(self):
    #     # res = super(HrPayslipInherit, self).compute_sheet()
    #     if self.employee_type == 'fos_employee':
    #         users = []
    #         activity_to_do = self.env.ref('taqat_payroll.mail_act_payroll').id
    #         model_id = self.env['ir.model']._get('hr.payslip.run').id
    #         activity = self.env['mail.activity']
    #         users += self.env.ref('taqat_groups_access_rights_extended.group_operational_manager').users
    #         for user in users:
    #             if user.id != self.env.ref('base.user_admin').id:
    #                 act_dct = {
    #                     'activity_type_id': activity_to_do,
    #                     'note': "kindly check this Employee Payslip.",
    #                     'user_id': user.id,
    #                     'res_id': self.id,
    #                     'res_model': 'hr.payslip.run',
    #                     'res_model_id': model_id,
    #                     'date_deadline': datetime.today().date()
    #                 }
    #                 activity.sudo().create(act_dct)
    #         self.state = 'draft'
    #     elif self.employee_type == 'fusion_employee':
    #         activity_to_do = self.env.ref('taqat_payroll.mail_act_payroll').id
    #         model_id = self.env['ir.model']._get('hr.payslip.run').id
    #         activity = self.env['mail.activity']
    #         users = self.env['res.users'].search([])
    #         for user in users:
    #             if user.has_group('account.group_account_manager') and \
    #                     user.has_group('ebs_lb_payroll.group_finance_payroll_confirm') and \
    #                     not  user.id != self.env.ref('base.user_admin').id:
    #                 act_dct = {
    #                     'activity_type_id': activity_to_do,
    #                     'note': "kindly check this Employee Payslip.",
    #                     'user_id': user.id,
    #                     'res_id': self.id,
    #                     'res_model': 'hr.payslip.run',
    #                     'res_model_id': model_id,
    #                     'date_deadline': datetime.today().date()
    #                 }
    #                 activity.sudo().create(act_dct)
    #         self.direct_approved()
    #         self.action_hr_confirm()
    #
    #     # return res

    def direct_approved(self):
        if self.employee_type == 'fos_employee':
            users = []
            activity_to_do = self.env.ref('taqat_payroll.mail_act_payroll').id
            previous_activity_users = []
            previous_activity_users += self.env.ref(
                'taqat_groups_access_rights_extended.group_operational_manager').users.ids
            activity_id = self.env['mail.activity'].search(
                [('res_id', '=', self.id), ('user_id', 'in', previous_activity_users),
                 ('activity_type_id', '=', activity_to_do)])
            activity_id.action_feedback(feedback='Approved')

            model_id = self.env['ir.model']._get('hr.payslip.run').id
            activity = self.env['mail.activity']
            users += self.env.ref('taqat_groups_access_rights_extended.group_employability_manager').users
            for user in users:
                if user.id != self.env.ref('base.user_admin').id:
                    act_dct = {
                        'activity_type_id': activity_to_do,
                        'note': "kindly check this Employee Payslip.",
                        'user_id': user.id,
                        'res_id': self.id,
                        'res_model': 'hr.payslip.run',
                        'res_model_id': model_id,
                        'date_deadline': datetime.today().date()
                    }
                    activity.sudo().create(act_dct)
            self.state = 'approve'
            self.is_finance_approve = False

    def action_finance_confirm(self):
        if self.employee_type == 'fos_employee':
            users = []
            activity_to_do = self.env.ref('taqat_payroll.mail_act_payroll').id
            previous_activity_all_users = self.env['res.users'].search([])
            previous_activity_users = []
            for user in previous_activity_all_users:
                if user.has_group('account.group_account_manager') and user.has_group(
                        'ebs_lb_payroll.group_finance_payroll_confirm'):
                    previous_activity_users.append(user.id)
            activity_id = self.env['mail.activity'].search(
                [('res_id', '=', self.id), ('user_id', 'in', previous_activity_users),
                 ('activity_type_id', '=', activity_to_do)])
            activity_id.action_feedback(feedback='Approved')
            model_id = self.env['ir.model']._get('hr.payslip.run').id
            activity = self.env['mail.activity']
            users += self.env.ref('ebs_lb_payroll.group_director_payroll_confirm').users
            for user in users:
                if user.id != self.env.ref('base.user_admin').id:
                    act_dct = {
                        'activity_type_id': activity_to_do,
                        'note': "kindly check this Employee Payslip.",
                        'user_id': user.id,
                        'res_id': self.id,
                        'res_model': 'hr.payslip.run',
                        'res_model_id': model_id,
                        'date_deadline': datetime.today().date()
                    }
                    activity.sudo().create(act_dct)
            self.state = 'by_finance'
            self.action_validate()
            self.is_finance_approve = False

        elif self.employee_type == 'fusion_employee':
            users = []
            activity_to_do = self.env.ref('taqat_payroll.mail_act_payroll').id
            previous_activity_all_users = self.env['res.users'].search([])
            previous_activity_users = []
            for user in previous_activity_all_users:
                if user.has_group('account.group_account_manager') and user.has_group(
                        'ebs_lb_payroll.group_finance_payroll_confirm'):
                    previous_activity_users.append(user.id)
            activity_id = self.env['mail.activity'].search(
                [('res_id', '=', self.id), ('user_id', 'in', previous_activity_users),
                 ('activity_type_id', '=', activity_to_do)])
            activity_id.action_feedback(feedback='Approved')
            model_id = self.env['ir.model']._get('hr.payslip.run').id
            activity = self.env['mail.activity']
            users += self.env.ref('ebs_lb_payroll.group_director_payroll_confirm').users
            for user in users:
                if user.id != self.env.ref('base.user_admin').id:
                    act_dct = {
                        'activity_type_id': activity_to_do,
                        'note': "kindly check this Employee Payslip.",
                        'user_id': user.id,
                        'res_id': self.id,
                        'res_model': 'hr.payslip.run',
                        'res_model_id': model_id,
                        'date_deadline': datetime.today().date()
                    }
                    activity.sudo().create(act_dct)
            self.state = 'by_finance'
            self.action_validate()
            self.is_finance_approve = False

    def action_hr_confirm(self):
        if self.employee_type == 'fos_employee':
            activity_to_do = self.env.ref('taqat_payroll.mail_act_payroll').id
            previous_activity_users = []
            previous_activity_users += self.env.ref(
                'taqat_groups_access_rights_extended.group_employability_manager').users.ids
            activity_id = self.env['mail.activity'].search(
                [('res_id', '=', self.id), ('user_id', 'in', previous_activity_users),
                 ('activity_type_id', '=', activity_to_do)])
            activity_id.action_feedback(feedback='Approved')
            model_id = self.env['ir.model']._get('hr.payslip.run').id
            activity = self.env['mail.activity']
            users = self.env['res.users'].search([])
            for user in users:
                if user.has_group('account.group_account_manager') and user.has_group(
                        'ebs_lb_payroll.group_finance_payroll_confirm') and user.id != self.env.ref(
                    'base.user_admin').id:
                    act_dct = {
                        'activity_type_id': activity_to_do,
                        'note': "kindly check this Employee Payslip.",
                        'user_id': user.id,
                        'res_id': self.id,
                        'res_model': 'hr.payslip.run',
                        'res_model_id': model_id,
                        'date_deadline': datetime.today().date()
                    }
                    activity.sudo().create(act_dct)
            self.state = 'by_hr'
            self.is_finance_approve = True
        elif self.employee_type == 'fusion_employee':
            activity_to_do = self.env.ref('taqat_payroll.mail_act_payroll').id
            previous_activity_users = []
            previous_activity_users += self.env.ref(
                'taqat_groups_access_rights_extended.group_employability_manager').users.ids
            activity_id = self.env['mail.activity'].search(
                [('res_id', '=', self.id), ('user_id', 'in', previous_activity_users),
                 ('activity_type_id', '=', activity_to_do)])
            activity_id.action_feedback(feedback='Approved')
            model_id = self.env['ir.model']._get('hr.payslip.run').id
            activity = self.env['mail.activity']
            users = self.env['res.users'].search([])
            for user in users:
                if user.has_group('account.group_account_manager') and user.has_group(
                        'ebs_lb_payroll.group_finance_payroll_confirm') and user.id != self.env.ref(
                    'base.user_admin').id:
                    act_dct = {
                        'activity_type_id': activity_to_do,
                        'note': "kindly check this Employee Payslip.",
                        'user_id': user.id,
                        'res_id': self.id,
                        'res_model': 'hr.payslip.run',
                        'res_model_id': model_id,
                        'date_deadline': datetime.today().date()
                    }
                    activity.sudo().create(act_dct)
            self.state = 'by_hr'
            self.is_finance_approve = True

        # return res

    def director_approved(self):
        # res = super(HrPayslipInherit, self).director_approved()
        if self.employee_type == 'fos_employee':
            activity_to_do = self.env.ref('taqat_payroll.mail_act_payroll').id
            previous_activity_users = []
            previous_activity_users += self.env.ref('ebs_lb_payroll.group_director_payroll_confirm').users.ids
            activity_id = self.env['mail.activity'].search(
                [('res_id', '=', self.id), ('user_id', 'in', previous_activity_users),
                 ('activity_type_id', '=', activity_to_do)])
            activity_id.action_feedback(feedback='Approved')

            model_id = self.env['ir.model']._get('hr.payslip.run').id
            activity = self.env['mail.activity']
            users = self.env['res.users'].search([])
            for user in users:
                if user.has_group('account.group_account_manager') and user.has_group(
                        'ebs_lb_payroll.group_finance_payroll_confirm') and user.id != self.env.ref(
                    'base.user_admin').id:
                    act_dct = {
                        'activity_type_id': activity_to_do,
                        'note': "kindly Mark as paid to this Employee.",
                        'user_id': user.id,
                        'res_id': self.id,
                        'res_model': 'hr.payslip.run',
                        'res_model_id': model_id,
                        'date_deadline': datetime.today().date()
                    }
                    activity.sudo().create(act_dct)
            self.state = 'close'
            self.is_finance_approve = False
        elif self.employee_type == 'fusion_employee':
            activity_to_do = self.env.ref('taqat_payroll.mail_act_payroll').id
            previous_activity_users = []
            previous_activity_users += self.env.ref('ebs_lb_payroll.group_director_payroll_confirm').users.ids
            activity_id = self.env['mail.activity'].search(
                [('res_id', '=', self.id), ('user_id', 'in', previous_activity_users),
                 ('activity_type_id', '=', activity_to_do)])
            activity_id.action_feedback(feedback='Approved')

            model_id = self.env['ir.model']._get('hr.payslip.run').id
            activity = self.env['mail.activity']
            users = self.env['res.users'].search([])
            for user in users:
                if user.has_group('account.group_account_manager') and user.has_group(
                        'ebs_lb_payroll.group_finance_payroll_confirm') and user.id != self.env.ref(
                    'base.user_admin').id:
                    act_dct = {
                        'activity_type_id': activity_to_do,
                        'note': "kindly Mark as paid to this Employee.",
                        'user_id': user.id,
                        'res_id': self.id,
                        'res_model': 'hr.payslip.run',
                        'res_model_id': model_id,
                        'date_deadline': datetime.today().date()
                    }
                    activity.sudo().create(act_dct)
            self.state = 'close'
            self.is_finance_approve = False
        # return res

    def action_payslip_paid(self):
        res = super(HrPayslipRun, self).action_payslip_paid()
        if self.employee_id.employee_type == 'fos_employee':
            activity_to_do = self.env.ref('taqat_payroll.mail_act_payroll').id
            previous_activity_all_users = self.env['res.users'].search([])
            previous_activity_users = []
            for user in previous_activity_all_users:
                if user.has_group('account.group_account_manager') and user.has_group(
                        'ebs_lb_payroll.group_finance_payroll_confirm'):
                    previous_activity_users.append(user.id)
            activity_id = self.env['mail.activity'].search(
                [('res_id', '=', self.id), ('user_id', 'in', previous_activity_users),
                 ('activity_type_id', '=', activity_to_do)])
            activity_id.action_feedback(feedback='Approved')
        elif self.employee_id.employee_type == 'fusion_employee':
            activity_to_do = self.env.ref('taqat_payroll.mail_act_payroll').id
            previous_activity_all_users = self.env['res.users'].search([])
            previous_activity_users = []
            for user in previous_activity_all_users:
                if user.has_group('account.group_account_manager') and user.has_group(
                        'ebs_lb_payroll.group_finance_payroll_confirm'):
                    previous_activity_users.append(user.id)
            activity_id = self.env['mail.activity'].search(
                [('res_id', '=', self.id), ('user_id', 'in', previous_activity_users),
                 ('activity_type_id', '=', activity_to_do)])
            activity_id.action_feedback(feedback='Approved')
        return res


class HrPayslipemployeesInherit(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    def compute_sheet(self):
        res = super(HrPayslipemployeesInherit, self).compute_sheet()
        payslip_run = self.env['hr.payslip.run'].browse(self._context.get('active_id'))
        if payslip_run.employee_type == 'fos_employee':
            users = []
            activity_to_do = self.env.ref('taqat_payroll.mail_act_payroll').id
            model_id = self.env['ir.model']._get('hr.payslip.run').id
            activity = self.env['mail.activity']
            users += self.env.ref('taqat_groups_access_rights_extended.group_operational_manager').users
            for user in users:
                if user.id != self.env.ref('base.user_admin').id:
                    act_dct = {
                        'activity_type_id': activity_to_do,
                        'note': "kindly check this Employee Payslip.",
                        'user_id': user.id,
                        'res_id': payslip_run.id,
                        'res_model': 'hr.payslip.run',
                        'res_model_id': model_id,
                        'date_deadline': datetime.today().date()
                    }
                    activity.sudo().create(act_dct)
            # self.state = 'confirm'
        elif payslip_run.employee_type == 'fusion_employee':
            activity_to_do = self.env.ref('taqat_payroll.mail_act_payroll').id
            model_id = self.env['ir.model']._get('hr.payslip.run').id
            activity = self.env['mail.activity']
            users = self.env['res.users'].search([])
            for user in users:
                if user.has_group('account.group_account_manager') and \
                        user.has_group('ebs_lb_payroll.group_finance_payroll_confirm') and \
                        not user.id != self.env.ref('base.user_admin').id:
                    act_dct = {
                        'activity_type_id': activity_to_do,
                        'note': "kindly check this Employee Payslip.",
                        'user_id': user.id,
                        'res_id': payslip_run.id,
                        'res_model': 'hr.payslip.run',
                        'res_model_id': model_id,
                        'date_deadline': datetime.today().date()
                    }
                    activity.sudo().create(act_dct)
            payslip_run.direct_approved()
            payslip_run.action_hr_confirm()

        return res
