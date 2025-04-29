# -*- coding: utf-8 -*-
import pytz
import ast
import logging
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.addons.hr_holidays.models.hr_leave import HolidaysRequest
from odoo.exceptions import ValidationError, UserError
from datetime import date, datetime, time, timedelta
import datetime as dt
from odoo.addons.resource.models.resource_mixin import timezone_datetime
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class HRLeaveCustom(models.Model):
    _inherit = 'hr.leave'
    _description = 'Leave'

    # Author : bhavesh parmar
    # call from scheduled action
    def change_label_time_off_to_leave(self):
        leave_approval_actitvity_type = self.env.ref('hr_holidays.mail_act_leave_approval')
        leave_second_approval_actitvity_type = self.env.ref('hr_holidays.mail_act_leave_second_approval')
        if leave_approval_actitvity_type:
            leave_approval_actitvity_type.sudo().write({'name': 'Leave Approval'})
        if leave_second_approval_actitvity_type:
            leave_second_approval_actitvity_type.sudo().write({'name': 'Leave Second Approve'})
        leave_mail_message_subtype = self.env.ref('hr_holidays.mt_leave')
        if leave_mail_message_subtype:
            leave_mail_message_subtype.sudo().write({'name': 'Leave'})
        leave_task_for_timesheet = self.env.company.leave_timesheet_task_id
        if leave_task_for_timesheet.name == "Time Off":
            leave_task_for_timesheet.write({'name': 'Leave'})

    # onchange date validate remaining days of leave
    # @api.model
    # def create(self, vals):
    #     res = super(HRLeaveCustom, self).create(vals)
    #     holiday_status_id = self.env['hr.leave.type'].search([('id', '=', vals.get('holiday_status_id'))])
    #     from_date = datetime.strptime(str(vals.get('date_from')), '%Y-%m-%d %H:%M:%S')
    #     to_date = datetime.strptime(str(vals.get('date_to')), '%Y-%m-%d %H:%M:%S')
    #     total_days = 0.0
    #     if vals.get('employee_id'):
    #         employee = self.env['hr.employee'].browse(vals.get('employee_id'))
    #         total_days = employee._get_work_days_data_batch(from_date, to_date)[employee.id]
    #
    #     if holiday_status_id.request_unit == 'day':
    #         if total_days['days'] and holiday_status_id.virtual_remaining_leaves:
    #             if total_days['days'] > holiday_status_id.virtual_remaining_leaves and holiday_status_id.virtual_remaining_leaves < 0:
    #                 raise UserError(_("You can't apply leave more than balance."))
    #
    #     if self.env.user.has_group('hr.group_hr_manager'):
    #         res.action_manager1_approve()
    #     return res

    @api.model_create_multi
    def create(self, vals_list):
        """ Override to avoid automatic logging of creation """
        if not self._context.get('leave_fast_create'):
            leave_types = self.env['hr.leave.type'].browse(
                [values.get('holiday_status_id') for values in vals_list if values.get('holiday_status_id')])
            mapped_validation_type = {leave_type.id: leave_type.leave_validation_type for leave_type in leave_types}

            for values in vals_list:
                employee_id = values.get('employee_id', False)
                leave_type_id = values.get('holiday_status_id')
                # Handle automatic department_id
                if not values.get('department_id'):
                    values.update({'department_id': self.env['hr.employee'].browse(employee_id).department_id.id})

                # Handle no_validation
                if mapped_validation_type[leave_type_id] == 'no_validation':
                    values.update({'state': 'confirm'})

                # Handle double validation
                if mapped_validation_type[leave_type_id] == 'both':
                    self._check_double_validation_rules(employee_id, values.get('state', False))

                holiday_status_id = self.env['hr.leave.type'].search([('id', '=', values.get('holiday_status_id'))])
                from_date = datetime.strptime(str(values.get('date_from')), '%Y-%m-%d %H:%M:%S')
                to_date = datetime.strptime(str(values.get('date_to')), '%Y-%m-%d %H:%M:%S')
                total_days = 0.0
                if values.get('employee_id'):
                    employee = self.env['hr.employee'].browse(values.get('employee_id'))
                    total_days = employee._get_work_days_data_batch(from_date, to_date)[employee.id]

                if holiday_status_id.request_unit == 'day':
                    leave_days = holiday_status_id.get_days(values.get('employee_id'))[holiday_status_id.id]
                    if total_days['days']:
                        if total_days['days'] > round(leave_days['remaining_leaves']):
                            raise UserError(_("You can't apply leave more than balance."))

        holidays = super(HolidaysRequest, self.with_context(mail_create_nosubscribe=True)).create(vals_list)
        print('holidays', holidays)
        for holiday in holidays:
            time_now = datetime.now()
            holiday.date_validated = time_now
            if self._context.get('import_file'):
                holiday._onchange_leave_dates()
            if not self._context.get('leave_fast_create'):
                # FIXME remove these, as they should not be needed
                # if employee_id:
                #     holiday.with_user(SUPERUSER_ID)._sync_employee_details()
                if 'number_of_days' not in values and ('date_from' in values or 'date_to' in values):
                    holiday.with_user(SUPERUSER_ID)._onchange_leave_dates()

                # Everything that is done here must be done using sudo because we might
                # have different create and write rights
                # eg : holidays_user can create a leave request with validation_type = 'manager' for someone else
                # but they can only write on it if they are leave_manager_id
                holiday_sudo = holiday.sudo()
                partner_list = []
                ctx = {}
                is_employee = holiday.employee_id == self.env.user.employee_id
                if self.env.user.has_group('hr.group_hr_manager') and not is_employee:
                    if holiday.employee_id and holiday.employee_id.work_email:
                        partner_list.append(holiday.employee_id)
                    if holiday.employee_id and holiday.employee_id.parent_id and holiday.employee_id.parent_id.work_email \
                            and not (
                            holiday.holiday_status_id.is_sick_leave or holiday.holiday_status_id.request_unit == 'hour'):
                        partner_list.append(holiday.employee_id.parent_id)
                    if partner_list:
                        mail_template = self.env.ref('ebs_hr_leave_custom.new_leave_create_hr_email_template')
                        # ctx['email_from'] = 'hr@waseef.qa'
                        ctx['email_to'] = ','.join([user.work_email for user in partner_list if user.work_email])
                        ctx['name'] = holiday.employee_id.name if holiday.employee_id else ''
                        ctx['send_email'] = True
                        # ctx['url'] = '/mail/view?model=%s&res_id=%s' % ('hr.leave', holiday.id)
                        template = mail_template.sudo().with_context(ctx)
                        template.send_mail(holiday.id, force_send=True)
                        holiday_sudo.with_context(self.env.context).action_manager1_approve()
                if not self._context.get('import_file'):
                    holiday_sudo.activity_update()
        return holidays

    @api.onchange('date_from', 'date_to', 'employee_id', 'holiday_status_id')
    def _onchange_leave_dates(self):
        if self.date_from and self.date_to:
            total_days = (self.date_to.date() - self.date_from.date()).days + 1
            contract = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)], limit=1)
            if not self.holiday_status_id.is_in_calendar_days and contract.type_leave == 'working_days' or (
                    self.employee_id.employee_type == 'perm_in_house' and
                    self.holiday_status_id.code == 'SL'):
                if self.date_from and self.date_to:
                    self.number_of_days = self._get_number_of_days(self.date_from, self.date_to, self.employee_id.id)[
                        'days']
            else:
                self.number_of_days = total_days

    def action_first_approval(self):
        current_employee = self.env.user.employee_id
        # for rec in self:
        if self.holiday_status_id.name == 'Annual':
            if self.env.user.has_group(
                    'ohrms_overtime.group_department_manager_head') or self.env.user.has_group(
                'ohrms_overtime.group_pmAndFm_manger') or self.env.user.has_group(
                'ohrms_overtime.group_ceo') or self.env.user.has_group(
                'ohrms_overtime.group_director'):
                self.write({'state': 'validate1', 'second_approver_id': current_employee.id,
                            'date_second_approve': datetime.now(),
                            'last_approval_date': datetime.now()})
            else:
                raise ValidationError(_('You do not have authority to approve it.'))
        else:
            self.write({'state': 'validate1', 'second_approver_id': current_employee.id,
                        'date_second_approve': datetime.now(),
                        'last_approval_date': datetime.now()})
        # all_users = []
        # if self.unit == 'support_services' or self.unit == 'business_support' or self.unit == 'portfolio' or \
        #         self.unit == 'directors':
        #     for each_project in self.employee_id.project_id:
        #         employee_project_line = self.env['employee.project.line'].search(
        #             [('project_id', '=', each_project.project_id.id),
        #              ('job_title.code', '=', 'group_hr_department_user'),
        #              ('employee_id', '!=', self.employee_id.id)])
        #         if employee_project_line.env.user.has_group('ebs_manpower_transfer.group_hr_department_user'):
        #             all_users.append(employee_project_line)
        #     self._create_activity(all_users)
        # elif self.unit == 'operation':
        #     if self.sub_unit in ['FM_manager', 'PM_manager', 'department_staff', 'technician', 'FM_site_staff',
        #                          'PM_site_staff']:
        #         for each_project in self.employee_id.project_id:
        #             employee_project_line = self.env['employee.project.line'].search(
        #                 [('project_id', '=', each_project.project_id.id),
        #                  ('job_title.code', 'in', 'group_hr_department_user'),
        #                  ('employee_id', '!=', self.employee_id.id)])
        #             if employee_project_line.env.user.has_group('ebs_manpower_transfer.group_hr_department_user'):
        #                 all_users.append(employee_project_line)
        #         self._create_activity(all_users)

    state = fields.Selection([
        ('draft', 'To Submit'),
        ('cancel', 'Cancelled'),
        ('confirm', 'To Approve'),
        ('refuse', 'Refused'),
        ('first_approval', 'First Approval'),
        ('validate1', 'Second Approval'),
        ('validate', 'Approved')
    ], string='Status', readonly=True, copy=False, default='draft',
        help="The status is set to 'To Submit', when a time off request is created." +
             "\nThe status is 'To Approve', when time off request is confirmed by user." +
             "\nThe status is 'Refused', when time off request is refused by manager." +
             "\nThe status is 'Approved', when time off request is approved by manager.")
    third_approver_id = fields.Many2one('hr.employee', string='Third Approval', readonly=True, copy=False,
                                        help='This area is automatically filled by the user who validate the allocation with third level (If allocation type need third validation)')
    unit = fields.Selection(related='employee_id.unit', string="Unit", store=True, readonly=True)
    sub_unit = fields.Selection(related='employee_id.sub_unit', string="Sub Unit", store=True, readonly=True)
    manager_user_id = fields.Many2one(related='manager_id.user_id', readonly=True)
    date_validated = fields.Datetime(string='Validated On', store=True)
    date_f_approve = fields.Datetime(string='Fifth Approval Date', store=True)
    date_second_approve = fields.Datetime(string='Sixth Approval Date', store=True)
    last_approval_date = fields.Datetime(string='Last Approval Date', store=True)
    employee_number = fields.Char(string="Employee Number", related="employee_id.registration_number")
    doc_required = fields.Boolean(related="holiday_status_id.is_doc_required")
    attachment_id = fields.Binary(string='Attachment', store=True)
    file_name_attachment = fields.Char(string='File Name')
    user_approval_id = fields.Many2one('res.users')
    approved_by_manager1 = fields.Boolean(default=False)
    approved_by_manager2 = fields.Boolean(default=False)
    approved_by_time_off_manager = fields.Boolean(default=False)
    is_manager = fields.Boolean(compute='_compute_button_visible')
    permission_leave_type = fields.Selection([
        ('site_permission', 'Site Permission'),
        ('business_permission', 'Business Permission'),
        ('personal_permission', 'Personal Permission')
    ], string='Permission Type', default="personal_permission")
    is_permission = fields.Boolean(related='holiday_status_id.is_permission')
    leave_planning_id = fields.Many2one('hr.leave.planning')

    def _compute_button_visible(self):
        for rec in self:
            managers = self.env.ref('hr_holidays.group_hr_holidays_manager').users
            managers = managers.filtered(lambda user: user.employee_id)
            if rec.user_approval_id and rec.user_approval_id.id == self._uid or self.user_has_groups(
                    'hr_holidays.group_hr_holidays_manager') or self._uid in managers.ids:
                rec.is_manager = True
            else:
                rec.is_manager = False

    # def _get_responsible_for_approval(self):
    #     """ Override to add those requirements:
    #     1- Annual and permission leave approved by manager 1 and manager 2
    #     2- All types of leave except permission and annual approved by manager 1,
    #         manager 2 and Time Off Admin
    #     """
    #     self.ensure_one()
    #     responsible = self.env['res.users'].browse(SUPERUSER_ID)
    #     if self.holiday_status_id and self.holiday_status_id.is_sick_leave:
    #         if self.employee_id.parent_id.user_id or self.employee_id.leave_manager_id:
    #             responsible = self.employee_id.parent_id.user_id or self.employee_id.leave_manager_id
    #     else:
    #         if self.validation_type == 'manager' or (self.validation_type == 'both' and self.state == 'confirm'):
    #             if self.employee_id.leave_manager_id:
    #                 responsible = self.employee_id.leave_manager_id
    #             elif self.employee_id.parent_id.user_id:
    #                 responsible = self.employee_id.parent_id.user_id
    #         elif self.validation_type == 'hr' or (self.validation_type == 'both' and self.state == 'validate1'):
    #             if self.employee_id.parent_id.user_id:
    #                 responsible = self.employee_id.parent_id.user_id
    #     self.user_approval_id = responsible
    #     return responsible

    first_manager_id = fields.Many2one('res.users', string='Line 1 Manager')
    second_manager_id = fields.Many2one('res.users', string='Line 2 Manager')

    # @api.depends('employee_id', 'employee_id_2')
    # def _get_first_manager(self):
    #     for record in self:
    #         if record.employee_id_2:
    #             record.first_manager_id = record.employee_id_2.parent_id.user_id
    #         elif record.employee_id:
    #             record.first_manager_id = record.employee_id.parent_id.user_id
    #         else:
    #             record.first_manager_id = record.employee_id_2.parent_id.user_id
    #
    # @api.depends('employee_id', 'employee_id_2')
    # def _get_second_manager(self):
    #     for record in self:
    #         if record.employee_id_2:
    #             record.second_manager_id = record.employee_id_2.line_manager_id.user_id
    #         elif record.employee_id:
    #             record.second_manager_id = record.employee_id.line_manager_id.user_id
    #         else:
    #             record.second_manager_id = record.employee_id_2.line_manager_id.user_id

    @api.constrains('request_date_from')
    def _check_request_date_from(self):
        today = date.today()
        check_date = date(today.year, 12, 31)
        # print("check_date ", check_date)
        for leave in self:
            if leave.employee_id and leave.request_date_from and leave.holiday_status_id \
                    and leave.holiday_status_id.is_annual and \
                    leave.employee_id.wassef_employee_type == 'perm_staff' and leave.request_date_from > check_date:
                raise ValidationError(_(f'You can not request an annual leave started after {check_date}'))

    def action_confirm(self):
        if self.filtered(lambda holiday: holiday.state != 'draft'):
            raise UserError(_('Time off request must be in Draft state ("To Submit") in order to confirm it.'))
        if self.holiday_status_id.is_sick_leave or self.holiday_status_id.request_unit == 'hour':
            self.user_approval_id = self.holiday_status_id.responsible_id
            self._create_activity(self.holiday_status_id.responsible_id)
            activity_obj = self.env['mail.activity']
            activities = activity_obj.search([('res_id', '=', self.id), ('user_id', '=', self.env.user.id)])
            activities.action_done()
            self.write({'state': 'confirm'})
        else:
            if self.employee_id and self.employee_id.parent_id:
                self.user_approval_id = self.employee_id.parent_id.user_id
                self._create_activity(self.employee_id.parent_id.user_id)
                activity_obj = self.env['mail.activity']
                activities = activity_obj.search([('res_id', '=', self.id), ('user_id', '=', self.env.user.id)])
                activities.action_done()
                self.write({'state': 'confirm'})
            else:
                raise UserError(_('Line manager is not set.'))

    def action_manager1_approve(self):
        # can not approve leave which create from hr planning
        if not self._context.get('from_hr_planning'):
            if not self._context.get('from_hr_planning') and \
                    (self.holiday_status_id.request_unit == 'hour' or \
                     self.user_has_groups(
                         'hr_holidays.group_hr_holidays_manager,hr.group_hr_manager')):
                self.with_context(self.env.context).action_manager2_approve()
            else:
                if self.employee_id and self.employee_id.line_manager_id:
                    manager_id = self.employee_id.line_manager_id.sudo().user_id
                    self._create_activity(manager_id)
                    activity_obj = self.env['mail.activity']
                    activities = activity_obj.sudo().search(
                        [('res_id', '=', self.id), ('user_id', '=', self.env.user.id)])
                    activities.action_done()
                    self.user_approval_id = self.employee_id.line_manager_id.sudo().user_id
                    self.approved_by_manager1 = True
                else:
                    raise UserError(_('Line manager 2 is not set.'))
            time_now = datetime.now()
            self.date_validated = time_now

    # def action_manager2_approve(self):
    #     # if not self.holiday_status_id.is_sick_leave or self.holiday_status_id.request_unit != 'hour':
    #     self.approved_by_manager2 = True
    #     self.user_approval_id = False
    #     self.with_context(self.env.context).action_approve()
    #     activity_obj = self.env['mail.activity']
    #     activities = activity_obj.search([('res_id', '=', self.id), ('user_id', '=', self.env.user.id)])
    #     activities.action_done()

    def action_manager2_approve(self):
        # if not self.holiday_status_id.is_sick_leave or self.holiday_status_id.request_unit != 'hour':
        # can not approve leave which create from hr planning
        if not self._context.get('from_hr_planning'):
            if self.holiday_status_id.is_annual or \
                    self.holiday_status_id.request_unit == 'hour' or \
                    self.user_has_groups('hr_holidays.group_hr_holidays_manager,'
                                         'hr.group_hr_manager'):
                # print("In Approve Second Manager, approve ")
                self.approved_by_manager2 = True
                self.user_approval_id = False
                self.with_context(self.env.context).action_approve()
            else:
                # print("In Approve Second Manager, approve by time off manager")
                # self.approved_by_time_off_manager = True
                users = self.env.ref('hr_holidays.group_hr_holidays_manager').users
                users = users.filtered(lambda user: user.employee_id)
                self._create_activity(users)
                self.user_approval_id = False
                self.approved_by_manager2 = True
                self.approved_by_time_off_manager = True
                activity_obj = self.env['mail.activity']
                activities = activity_obj.search([('res_id', '=', self.id), ('user_id', '=', self.env.user.id)])
                activities.action_done()

    def action_time_off_manager_approve(self):
        # if not self.holiday_status_id.is_sick_leave or self.holiday_status_id.request_unit != 'hour':
        # print("Approve by time off manager")
        # can not approve leave which create from hr planning
        if not self._context.get('from_hr_planning'):
            self.approved_by_time_off_manager = False
            self.user_approval_id = False
            self.with_context(self.env.context).action_approve()
            activity_obj = self.env['mail.activity']
            activities = activity_obj.search([('res_id', '=', self.id), ('user_id', '=', self.env.user.id)])
            activities.action_done()

    @api.model
    def _automatic_leave_approve(self):
        allow_leaves = self.env['ir.config_parameter']. \
            get_param('ebs_hr_leave_custom.allow_leave_ids')
        number_of_hours = self.env['ir.config_parameter'].sudo(). \
            get_param('ebs_hr_leave_custom.number_of_hours_approval')
        if allow_leaves and number_of_hours:
            date_now = datetime.now()
            allow_leaves = self.env['hr.leave.type'].browse(ast.literal_eval(allow_leaves))
            tz_c = pytz.timezone("Asia/Qatar")
            date_now = date_now.astimezone(tz_c)
            leaves = self.search([
                ('state', '=', 'confirm'),
                ('holiday_status_id', 'in', allow_leaves.ids), ('date_validated', '!=', False)
            ]).filtered(
                lambda x: (x.date_validated + timedelta(hours=int(number_of_hours))) < date_now.replace(tzinfo=None))
            # print("leaves ", leaves)
            # print("Date Now ", date_now)
            for leave in leaves:
                # print("leaves ", leave)
                # print("Leave approved_by_manager1 ", leave.approved_by_manager1)
                # print("Leave approved_by_manager2 ", leave.approved_by_manager2)
                # print("date + ", leave.date_validated + timedelta(hours=int(number_of_hours)))
                # print("date now ", date_now)
                # print("date leave.date_validated ", leave.date_validated)
                # if (leave.date_validated + timedelta(hours=int(number_of_hours))) < date_now:
                if not leave.approved_by_manager1:
                    first_manager = leave.employee_id.parent_id or leave.employee_id_2.parent_id
                    if first_manager.user_id:
                        leave.with_user(first_manager.user_id.id).action_manager1_approve()
                        leave.with_user(first_manager.user_id.id).message_post(body=_(
                            f"The leave first approved by a cron job on place manager {first_manager.name}"))
                        # print("Leave ", leave, 'First Approved')
                    else:
                        _logger.info('Can not approve leave %s browse there are first manager'
                                     % leave.name)
                elif not leave.approved_by_manager2 and leave.approved_by_manager1:
                    second_manager = leave.employee_id.line_manager_id or leave.employee_id_2.line_manager_id
                    if second_manager:
                        leave.with_user(second_manager.user_id.id).action_manager2_approve()
                        leave.with_user(second_manager.user_id.id).message_post(
                            body=_(f"The leave approved by a cron job on place manager {second_manager.name}"))
                        # print("Leave ", leave, "Second Approved")
                    else:
                        _logger.info('Can not approve leave %s browse there are second manager'
                                     % leave.name)
        else:
            _logger.info('Can not run automatic approval because no configuration of it')

    # def action_confirm(self):
    #     if self.filtered(lambda holiday: holiday.state != 'draft'):
    #         raise UserError(_('Time off request must be in Draft state ("To Submit") in order to confirm it.'))
    #     self.write({'state': 'confirm'})
    #     all_users = []
    #     if self.unit == 'support_services' or self.unit == 'business_support':
    #         for each_project in self.employee_id.project_id:
    #             employee_project_line = self.env['employee.project.line'].search(
    #                 [('project_id', '=', each_project.project_id.id),
    #                  ('job_title.code', '=', 'group_department_manager_head'),
    #                  ('employee_id', '!=', self.employee_id.id)])
    #             if employee_project_line.env.user.has_group('ebs_manpower_transfer.group_department_manager_head'):
    #                 all_users.append(employee_project_line)
    #         self._create_activity(all_users)
    #     elif self.unit == 'portfolio':
    #         for each_project in self.employee_id.project_id:
    #             employee_project_line = self.env['employee.project.line'].search(
    #                 [('project_id', '=', each_project.project_id.id),
    #                  ('job_title.code', '=', 'group_portfolio_manger'),
    #                  ('employee_id', '!=', self.employee_id.id)])
    #             if employee_project_line.env.user.has_group('ebs_manpower_transfer.group_portfolio_manger'):
    #                 all_users.append(employee_project_line)
    #         self._create_activity(all_users)
    #     elif self.unit == 'directors':
    #         for each_project in self.employee_id.project_id:
    #             employee_project_line = self.env['employee.project.line'].search(
    #                 [('project_id', '=', each_project.project_id.id),
    #                  ('job_title.code', '=', 'group_director'),
    #                  ('employee_id', '!=', self.employee_id.id)])
    #             if employee_project_line.env.user.has_group('ebs_manpower_transfer.group_director'):
    #                 all_users.append(employee_project_line)
    #         self._create_activity(all_users)
    #     elif self.unit == 'operation':
    #         if self.sub_unit == 'technician':
    #             for each_project in self.employee_id.project_id:
    #                 employee_project_line = self.env['employee.project.line'].search(
    #                     [('project_id', '=', each_project.project_id.id),
    #                      ('job_title.code', 'in', ['group_pmAndFm_manger', 'group_department_supervisor_engineer']),
    #                      ('employee_id', '!=', self.employee_id.id)])
    #                 if employee_project_line.env.user.has_group('ebs_manpower_transfer.group_pmAndFm_manger') or \
    #                         employee_project_line.env.user.has_group(
    #                             'ebs_manpower_transfer.group_department_supervisor_engineer'):
    #                     all_users.append(employee_project_line)
    #             self._create_activity(all_users)
    #         elif self.sub_unit == 'FM_site_staff' or self.sub_unit == 'PM_site_staff':
    #             for each_project in self.employee_id.project_id:
    #                 employee_project_line = self.env['employee.project.line'].search(
    #                     [('project_id', '=', each_project.project_id.id),
    #                      ('job_title.code', '=', 'group_pmAndFm_manger'),
    #                      ('employee_id', '!=', self.employee_id.id)])
    #                 if employee_project_line.env.user.has_group('ebs_manpower_transfer.group_pmAndFm_manger'):
    #                     all_users.append(employee_project_line)
    #             self._create_activity(all_users)
    #         elif self.sub_unit == 'PM_FM_manager':
    #             for each_project in self.employee_id.project_id:
    #                 employee_project_line = self.env['employee.project.line'].search(
    #                     [('project_id', '=', each_project.project_id.id),
    #                      ('job_title.code', '=', 'group_manager_of_pmAndFm'),
    #                      ('employee_id', '!=', self.employee_id.id)])
    #                 if employee_project_line.env.user.has_group('ebs_manpower_transfer.group_manager_of_pmAndFm'):
    #                     all_users.append(employee_project_line)
    #             self._create_activity(all_users)
    #         elif self.sub_unit == 'department_staff':
    #             for each_project in self.employee_id.project_id:
    #                 employee_project_line = self.env['employee.project.line'].search(
    #                     [('project_id', '=', each_project.project_id.id),
    #                      ('job_title.code', '=', 'group_department_manager_head'),
    #                      ('employee_id', '!=', self.employee_id.id)])
    #                 if employee_project_line.env.user.has_group('ebs_manpower_transfer.group_department_manager_head'):
    #                     all_users.append(employee_project_line)
    #             self._create_activity(all_users)
    #     # if not self.env.context.get('leave_fast_create'):
    #     # self.activity_update()
    #     return True

    def action_refuse(self):
        res = super(HRLeaveCustom, self).action_refuse()
        # delete all activities on leave record
        self.sudo().activity_ids.action_done()
        for rec in self:
            ctx = {}
            ctx['email_to'] = rec.employee_id.work_email
            ctx['email_from'] = self.env.user.company_id.email
            ctx['send_email'] = True
            # base_url = self.env['ir.config_parameter'].get_param('web.base.url')
            # url = base_url + '/web#id={id}&action={action_id}&model=hr.leave&view_type=form'.format(
            #     id=rec.id, action_id=self.env.ref('hr_holidays.hr_leave_action_action_approve_department').id)
            # # ctx['url'] = '/mail/view?model=%s&res_id=%s' % ('hr.leave', rec.id)
            # ctx['url'] = url
            template = self.env.ref('ebs_hr_leave_custom.send_refuse_leave_mail_employee')
            template.with_context(ctx).send_mail(rec.id, force_send=True, raise_exception=False)

    def get_create_leave_url(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        url = base_url + '/web#id={id}&action={action_id}&model=hr.leave&view_type=form'.format(
            id=self.id, action_id=self.env.ref('hr_holidays.hr_leave_action_action_approve_department').id)
        return url

    # def action_approve(self):
    #     if any(holiday.state != 'confirm' for holiday in self):
    #         raise UserError(_('Time off request must be confirmed ("To Approve") in order to approve it.'))
    #
    #     current_employee = self.env.user.employee_id
    #     # self.filtered(lambda hol: hol.validation_type == 'both').write(
    #     #     {'state': 'validate1', 'first_approver_id': current_employee.id,
    #     #      'date_f_approve': datetime.now(),
    #     #      'last_approval_date': datetime.now()})
    #
    #     # Post a second message, more verbose than the tracking message
    #     for holiday in self.filtered(lambda holiday: holiday.employee_id.user_id):
    #         holiday.message_post(
    #             body=_('Your %s planned on %s has been accepted' % (
    #                 holiday.holiday_status_id.display_name, holiday.date_from)),
    #             partner_ids=holiday.employee_id.user_id.partner_id.ids)
    #
    #     # self.filtered(lambda hol: not hol.validation_type == 'both').action_validate()
    #     if self.holiday_status_id.name == 'Annual':
    #         if self.env.user.has_group(
    #                 'ebs_manpower_transfer.group_department_manager_head') or self.env.user.has_group(
    #             'ebs_manpower_transfer.group_portfolio_manger') or self.env.user.has_group(
    #             'ebs_manpower_transfer.group_pmAndFm_manger') or self.env.user.has_group(
    #             'ebs_manpower_transfer.group_manager_of_pmAndFm') or self.env.user.has_group(
    #             'ebs_manpower_transfer.group_department_supervisor_engineer') or self.env.user.has_group(
    #             'ebs_manpower_transfer.group_director'):
    #             project_list = []
    #             project_user_list = []
    #             for each_project in self.employee_id.project_id:
    #                 for each_employee_project in self.env.user.employee_id.project_id:
    #                     project_user_list.append(each_employee_project.project_id.id)
    #                 project_list.append(each_project.project_id.id)
    #             lst3 = [value for value in project_list if value in project_user_list]
    #             can_approve = False
    #             for each_in_project in lst3:
    #                 employee_project = self.env['employee.project.line'].search([('project_id', '=', each_in_project),
    #                                                                              ('employee_id', '=',
    #                                                                               self.env.user.employee_id.id)])
    #                 if employee_project.job_title.code in ['group_portfolio_manger', 'group_department_manager_head',
    #                                                        'group_pmAndFm_manger', 'group_manager_of_pmAndFm',
    #                                                        'group_department_supervisor_engineer', 'group_director']:
    #                     can_approve = True
    #                 if can_approve:
    #                     break
    #                 else:
    #                     continue
    #             if can_approve:
    #                 self.write({'state': 'first_approval', 'first_approver_id': current_employee.id,
    #                             'date_f_approve': datetime.now(),
    #                             'last_approval_date': datetime.now()})
    #             else:
    #                 raise ValidationError(_('You do not have authority to approve it.'))
    #         else:
    #             raise ValidationError(_('You do not have authority to approve it.'))
    #     else:
    #         self.write({'state': 'first_approval', 'first_approver_id': current_employee.id,
    #                     'date_f_approve': datetime.now(),
    #                     'last_approval_date': datetime.now()})
    #     all_users = []
    #     if self.unit == 'support_services' or self.unit == 'business_support' or self.unit == 'portfolio':
    #         for each_project in self.employee_id.project_id:
    #             employee_project_line = self.env['employee.project.line'].search(
    #                 [('project_id', '=', each_project.project_id.id),
    #                  ('job_title.code', '=', 'group_director'),
    #                  ('employee_id', '!=', self.employee_id.id)])
    #             if employee_project_line.env.user.has_group('ebs_manpower_transfer.group_director'):
    #                 all_users.append(employee_project_line)
    #         self._create_activity(all_users)
    #     elif self.unit == 'directors':
    #         for each_project in self.employee_id.project_id:
    #             employee_project_line = self.env['employee.project.line'].search(
    #                 [('project_id', '=', each_project.project_id.id),
    #                  ('job_title.code', '=', 'group_ceo'),
    #                  ('employee_id', '!=', self.employee_id.id)])
    #             if employee_project_line.env.user.has_group('ebs_manpower_transfer.group_ceo'):
    #                 all_users.append(employee_project_line)
    #         self._create_activity(all_users)
    #     elif self.unit == 'operation':
    #         if self.sub_unit == 'technician':
    #             for each_project in self.employee_id.project_id:
    #                 employee_project_line = self.env['employee.project.line'].search(
    #                     [('project_id', '=', each_project.project_id.id),
    #                      ('job_title.code', 'in', ['group_pmAndFm_manger', 'group_department_manager_head']),
    #                      ('employee_id', '!=', self.employee_id.id)])
    #                 if employee_project_line.env.user.has_group('ebs_manpower_transfer.group_pmAndFm_manger') or \
    #                         employee_project_line.env.user.has_group(
    #                             'ebs_manpower_transfer.group_department_manager_head'):
    #                     all_users.append(employee_project_line)
    #             self._create_activity(all_users)
    #         elif self.sub_unit == 'PM_FM_manager' or self.sub_unit == 'department_staff':
    #             for each_project in self.employee_id.project_id:
    #                 employee_project_line = self.env['employee.project.line'].search(
    #                     [('project_id', '=', each_project.project_id.id),
    #                      ('job_title.code', '=', 'group_director'),
    #                      ('employee_id', '!=', self.employee_id.id)])
    #                 if employee_project_line.env.user.has_group('ebs_manpower_transfer.group_director'):
    #                     all_users.append(employee_project_line)
    #             self._create_activity(all_users)
    #
    #     # send email for employee managers
    #     if self.employee_id.parent_id:
    #         base = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
    #         hr_leave_object = base + "/web" + "/#id=%s&view_type=form&model=hr.leave" % (self.id)
    #         employee_object = base + "/web" + "/#id=%s&view_type=form&model=hr.employee" % self.employee_id.id
    #         if self.employee_id.parent_id.work_email:
    #             ctx = {
    #                 'email_to': self.employee_id.parent_id.work_email,
    #                 'email_from': self.env.user.company_id.email,
    #                 'send_email': True,
    #                 'leave_obj': hr_leave_object,
    #                 'employee_obj': employee_object,
    #             }
    #             template = self.env.ref('ebs_hr_leave_custom.hr_leave_send_approve_managers')
    #             template.with_context(ctx).send_mail(self.id, force_send=True, raise_exception=False)
    #
    #     # if not self.env.context.get('leave_fast_create'):
    #     #     self.activity_update()
    #     return True
    #
    # def action_validate(self):
    #     super(HRLeaveCustom, self).action_validate()
    #     current_employee = self.env.user.employee_id
    #     if self.holiday_status_id.name == 'Annual':
    #         if self.env.user.has_group('ebs_manpower_transfer.group_hr_department_user'):
    #             project_list = []
    #             project_user_list = []
    #             for each_project in self.employee_id.project_id:
    #                 for each_employee_project in self.env.user.employee_id.project_id:
    #                     project_user_list.append(each_employee_project.project_id.id)
    #                 project_list.append(each_project.project_id.id)
    #             lst3 = [value for value in project_list if value in project_user_list]
    #             for each_in_project in lst3:
    #                 employee_project = self.env['employee.project.line'].search([('project_id', '=', each_in_project),
    #                                                                              ('employee_id', '=',
    #                                                                               self.env.user.employee_id.id)])
    #                 if employee_project.job_title.code in ['group_hr_department_user']:
    #                     self.write({'state': 'validate', 'third_approver_id': current_employee.id,
    #                                 'date_validated': datetime.now()})
    #                 else:
    #                     raise ValidationError(_('You do not have authority to approve it.'))
    #         else:
    #             raise ValidationError(_('You do not have authority to approve it.'))
    #     else:
    #         self.write({'state': 'validate', 'third_approver_id': current_employee.id,
    #                     'date_validated': datetime.now()})

    # def activity_update(self):
    #     to_clean, to_do = self.env['hr.leave'], self.env['hr.leave']
    #     for holiday in self:
    #         note = _('New %s Request created by %s from %s to %s') % (holiday.holiday_status_id.name, holiday.create_uid.name, fields.Datetime.to_string(holiday.date_from), fields.Datetime.to_string(holiday.date_to))
    #         if holiday.state == 'draft':
    #             to_clean |= holiday
    #         elif holiday.state == 'confirm':
    #             holiday.activity_schedule(
    #                 'hr_holidays.mail_act_leave_approval',
    #                 note=note,
    #                 user_id=holiday.sudo()._get_responsible_for_approval().id or self.env.user.id)
    #         elif holiday.state == 'validate1':
    #             holiday.activity_feedback(['hr_holidays.mail_act_leave_approval'])
    #             holiday.activity_schedule(
    #                 'hr_holidays.mail_act_leave_second_approval',
    #                 note=note,
    #                 user_id=holiday.sudo()._get_responsible_for_approval().id or self.env.user.id)
    #         elif holiday.state == 'validate':
    #             to_do |= holiday
    #         elif holiday.state == 'refuse':
    #             to_clean |= holiday
    #     if to_clean:
    #         to_clean.activity_unlink(['hr_holidays.mail_act_leave_approval', 'hr_holidays.mail_act_leave_second_approval'])
    #     if to_do:
    #         to_do.activity_feedback(['hr_holidays.mail_act_leave_approval', 'hr_holidays.mail_act_leave_second_approval'])

    def _create_activity(self, all_users):
        all_users = all_users.sudo()
        activity_to_do = self.env.ref('mail.mail_activity_data_todo').id
        model_id = self.env['ir.model']._get('hr.leave').id
        activity = self.env['mail.activity']
        for user in all_users:
            if user:
                act_dct = {
                    'activity_type_id': activity_to_do,
                    'note': "kindly check this leave Approval Request, it's awaiting your approval",
                    'user_id': user.sudo().employee_id.sudo().user_id.id,
                    'res_id': self.id,
                    'res_model_id': model_id,
                    'date_deadline': datetime.today().date()
                }
                activity.sudo().create(act_dct)

    # @api.model
    # def create(self, values):
    #     if not self._context.get('leave_fast_create'):
    #         employee_id = values.get('employee_id', False)
    #         leave_type_id = values.get('holiday_status_id')
    #         leave_type = self.env['hr.leave.type'].browse(leave_type_id)
    #         # Handle automatic department_id
    #         if not values.get('department_id'):
    #             values.update({'department_id': self.env['hr.employee'].browse(employee_id).department_id.id})
    #
    #         # Handle no_validation
    #         if leave_type.validation_type == 'no_validation':
    #             values.update({'state': 'confirm'})
    #
    #         # Handle double validation
    #         if leave_type.validation_type == 'both':
    #             self._check_double_validation_rules(employee_id, values.get('state', False))
    #         if not leave_type.emergency and not leave_type.request_unit == 'hour':
    #             date_from = datetime.strptime(values['date_from'], "%Y-%m-%d %H:%M:%S")
    #             difference_days = date_from.date() - date.today()
    #             # if difference_days.days <= 45:
    #             #     raise ValidationError(
    #             #         _('You can not request a leave in 45 Days.'))
    #     holiday = super(HRLeaveCustom, self.with_context(mail_create_nosubscribe=True)).create(values)
    #     if self._context.get('import_file'):
    #         holiday._onchange_leave_dates()
    #     if not self._context.get('leave_fast_create'):
    #         # FIXME remove these, as they should not be needed
    #         if employee_id:
    #             holiday.with_user(SUPERUSER_ID)._sync_employee_details()
    #         if 'number_of_days' not in values and ('date_from' in values or 'date_to' in values):
    #             holiday.with_user(SUPERUSER_ID)._onchange_leave_dates()
    #
    #         # Everything that is done here must be done using sudo because we might
    #         # have different create and write rights
    #         # eg : holidays_user can create a leave request with validation_type = 'manager' for someone else
    #         # but they can only write on it if they are leave_manager_id
    #         holiday_sudo = holiday.sudo()
    #         holiday_sudo.add_follower(employee_id)
    #         if holiday.validation_type == 'manager':
    #             holiday_sudo.message_subscribe(partner_ids=holiday.employee_id.leave_manager_id.partner_id.ids)
    #         if leave_type.validation_type == 'no_validation':
    #             # Automatic validation should be done in sudo, because user might not have the rights to do it by himself
    #             holiday_sudo.action_validate()
    #             holiday_sudo.message_subscribe(partner_ids=[holiday._get_responsible_for_approval().partner_id.id])
    #             holiday_sudo.message_post(body=_("The time off has been automatically approved"), subtype="mt_comment")
    #         elif not self._context.get('import_file'):
    #             holiday_sudo.activity_update()
    #     return holiday

    # def action_employees_time_off(self):
    #     emp_manager = self.env['hr.employee'].search([
    #         ('project_id.project_id.user_id.id', '=', self.env.user.id), ('project_id.active', '=', True)
    #     ])
    #     return {
    #         'name': _('Employees Leaves'),
    #         'domain': [('employee_id', 'in', emp_manager.ids)],
    #         'view_type': 'form',
    #         'res_model': 'hr.leave',
    #         'view_id': False,
    #         'view_mode': 'calendar,tree',
    #         'type': 'ir.actions.act_window',
    #     }

    @api.constrains('request_unit_hours', 'request_unit_half', 'request_hour_from', 'request_hour_to')
    def validate_permission_leave(self):
        for rec in self:
            if rec.holiday_status_id.is_permission and any((rec.request_unit_half, rec.request_unit_hours)):
                permission_type = rec.permission_leave_type
                if permission_type:
                    max_hours = rec.holiday_status_id.permission_config_ids.filtered(
                        lambda x: x.permission_leave_type == permission_type).max_hours
                    if rec.number_of_hours_display > max_hours:
                        raise ValidationError(f'Max hours can be taken for this permission type is {max_hours}')

    @api.model
    def _delete_inactive_activity_leave(self):
        holidays = self.search([
            ('state', 'in', ['refuse', 'cancel', 'validate']),
            ('activity_ids', '!=', False)
        ])
        holidays.activity_ids.action_done()
