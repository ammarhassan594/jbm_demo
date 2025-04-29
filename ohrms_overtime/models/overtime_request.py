# -*- coding: utf-8 -*-
import datetime
from dateutil import relativedelta
# import pandas as pd
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.resource.models.resource import HOURS_PER_DAY
import datetime
from datetime import timedelta


class HrOverTime(models.Model):
    _name = 'hr.overtime'
    _description = "HR Overtime"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _get_employee_domain(self):
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.user.id)], limit=1)
        domain = [('id', '=', employee.id)]
        if self.env.user.has_group('hr.group_hr_user'):
            domain = []
        return domain

    def _default_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    @api.onchange('days_no_tmp')
    def _onchange_days_no_tmp(self):
        self.days_no = self.days_no_tmp

    name = fields.Char('Name', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  domain=_get_employee_domain, default=lambda self: self.env.user.employee_id.id,
                                  required=True)
    department_id = fields.Many2one('hr.department', string="Department",
                                    related="employee_id.department_id", required=True)
    job_id = fields.Many2one('hr.job', string="Job", related="employee_id.job_id")
    manager_id = fields.Many2one('res.users', string="Manager",
                                 related="employee_id.parent_id.user_id", store=True)
    current_user = fields.Many2one('res.users', string="Current User",
                                   related='employee_id.user_id',
                                   default=lambda self: self.env.uid,
                                   store=True)
    current_user_boolean = fields.Boolean()
    project_id = fields.Many2one('project.project', string="Project")
    project_manager_id = fields.Many2one('res.users', string="Project Manager")
    contract_id = fields.Many2one('hr.contract', string="Contract",
                                  related="employee_id.contract_id", required=True)
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date to')
    actual_date_from = fields.Date(string="Actual Date From", required=False, )
    actual_date_to = fields.Date(string="Actual Date To", required=False, )

    # Commented this field because we will get its value manually from the attendance sheet
    # days_no_tmp = fields.Float('Hours', compute="_get_days", store=True)
    days_no_tmp = fields.Float('Hours', compute="_get_total_hours", store=True)
    t_normal_hours = fields.Float('Normal Hours', compute="_get_total_normal_hours", store=True)
    t_special_hours = fields.Float('Special Hours', compute="_get_total_special_hours", store=True)
    days_no = fields.Float('No. of Days', store=True)
    desc = fields.Text('Description')
    state = fields.Selection([('draft', 'Draft'),
                              ('f_approve', 'Waiting'),
                              ('second_approve', 'Second Approval'),
                              ('third_approve', 'Third Approval'),
                              ('fourth_approve', 'Fourth Approval'),
                              ('fifth_approve', 'Fifth Approval'),
                              ('sixth_approve', 'Sixth Approval'),
                              ('approved', 'Approved'),
                              ('refused', 'Refused')], string="state",
                             default="draft")
    cancel_reason = fields.Text('Refuse Reason')
    leave_id = fields.Many2one('hr.leave.allocation', string="Leave ID")
    holiday_status_id = fields.Many2one(
        "hr.leave.type", string="Time Off Type", readonly=True,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]},
        domain=[('has_valid_allocation', '=', True), ('allocation_validation_type', '!=', 'no')])
    attchd_copy = fields.Binary('Attach A File')
    attchd_copy_name = fields.Char('File Name')
    type = fields.Selection([('cash', 'Cash'), ('leave', 'leave')], default="cash", required=True, string="Type")
    overtime_type_id = fields.Many2one('overtime.type', domain="[('type','=',type),('duration_type','=', "
                                                               "duration_type)]")
    public_holiday = fields.Char(string='Public Holiday', readonly=True)
    attendance_ids = fields.Many2many('hr.attendance', string='Attendance')
    work_schedule = fields.One2many(
        related='employee_id.resource_calendar_id.attendance_ids')
    global_leaves = fields.One2many(
        related='employee_id.resource_calendar_id.global_leave_ids')
    duration_type = fields.Selection([('hours', 'Hour'), ('days', 'Days')], string="Duration Type", default="hours",
                                     required=True)
    cash_hrs_amount = fields.Float(string='Overtime Amount', readonly=True)
    cash_day_amount = fields.Float(string='Overtime Amount', readonly=True)
    payslip_paid = fields.Boolean('Paid in Payslip', readonly=True)
    date_validated = fields.Datetime(string='Validated On', store=True)
    overtime_category = fields.Selection(related='employee_id.overtime_category', store=True,
                                         readonly=True)
    date_f_approve = fields.Datetime(string='First Approval Date', store=True)
    date_second_approve = fields.Datetime(string='Second Approval Date', store=True)
    date_third_approve = fields.Datetime(string='Third Approval Date', store=True)
    date_fourth_approve = fields.Datetime(string='Fourth Approval Date', store=True)
    date_fifth_approve = fields.Datetime(string='Fifth Approval Date', store=True)
    date_sixth_approve = fields.Datetime(string='Sixth Approval Date', store=True)
    last_approval_date = fields.Datetime(string='Last Approval Date', store=True)

    overtime_types = fields.Selection(string="OT Type", default="",
                                      selection=[('no', 'Normal Overtime'), ('sp', 'Special Overtime'), ],
                                      required=False)
    overtime_date = fields.Date(string="Date")
    ot_remarks = fields.Text(string="Remarks", default="", required=False)
    overtime_lines = fields.One2many('hr.overtime.line', 'overtime_id', string="Overtime Line", index=True)
    employee_number = fields.Char(related="employee_id.registration_number")

    # attendance_sheet_ids = fields.Many2one('attendance.sheet', string='Attendance')

    # @api.depends('current_user')
    # def check_current_user(self):
    # for i in self:
    # if self.env.user.id == self.employee_id.user_id.id:
    #     i.update({
    #         'current_user_boolean': True,
    #     })
    @api.depends('overtime_lines')
    def _get_total_hours(self):
        for rec in self:
            total_hours = 0.0
            if rec.overtime_lines:
                for line in rec.overtime_lines:
                    if line.paid:
                        total_hours += line.hours
                rec.days_no_tmp = total_hours

    @api.depends('overtime_lines')
    def _get_total_normal_hours(self):
        for rec in self:
            total_normal = 0.0
            if rec.overtime_lines:
                for line in rec.overtime_lines:
                    if line.paid and line.overtime_type == 'normal':
                        total_normal += line.hours
                rec.t_normal_hours = total_normal

    @api.depends('overtime_lines')
    def _get_total_special_hours(self):
        for rec in self:
            total_special = 0.0
            if rec.overtime_lines:
                for line in rec.overtime_lines:
                    if line.paid and line.overtime_type == 'special':
                        total_special += line.hours
                rec.t_special_hours = total_special

    @api.onchange('employee_id')
    def _get_defaults(self):
        for sheet in self:
            if sheet.employee_id:
                sheet.update({
                    'department_id': sheet.employee_id.department_id.id,
                    'job_id': sheet.employee_id.job_id.id,
                    'manager_id': sheet.sudo().employee_id.parent_id.user_id.id,
                })

    @api.depends('project_id')
    def _get_project_manager(self):
        for sheet in self:
            if sheet.project_id:
                sheet.update({
                    'project_manager_id': sheet.project_id.user_id.id,
                })

    # @api.depends('date_from', 'date_to')
    # def _get_days(self):
    #     for recd in self:
    #         if recd.date_from and recd.date_to:
    #             if recd.date_from > recd.date_to:
    #                 raise ValidationError('Start Date must be less than End Date')
    #     for sheet in self:
    #         if sheet.date_from and sheet.date_to:
    #             start_dt = fields.Datetime.from_string(sheet.date_from)
    #             finish_dt = fields.Datetime.from_string(sheet.date_to)
    #             s = finish_dt - start_dt
    #             difference = relativedelta.relativedelta(finish_dt, start_dt)
    #             hours = difference.hours
    #             minutes = difference.minutes
    #             days_in_mins = s.days * 24 * 60
    #             hours_in_mins = hours * 60
    #             days_no = ((days_in_mins + hours_in_mins + minutes) / (24 * 60))
    #
    #             diff = sheet.date_to - sheet.date_from
    #             days, seconds = diff.days, diff.seconds
    #             hours = days * 24 + seconds // 3600
    #             sheet.update({
    #                 'days_no_tmp': hours if sheet.duration_type == 'hours' else days_no,
    #             })

    @api.onchange('overtime_type_id')
    def _get_hour_amount(self):
        if self.overtime_type_id.rule_line_ids and self.duration_type == 'hours':
            for recd in self.overtime_type_id.rule_line_ids:
                if recd.from_hrs < self.days_no_tmp <= recd.to_hrs and self.contract_id:
                    if self.contract_id.over_hour:
                        cash_amount = self.contract_id.over_hour * recd.hrs_amount
                        self.cash_hrs_amount = cash_amount
                    else:
                        raise UserError(_("Hour Overtime Needs Hour Wage in Employee Contract."))
        elif self.overtime_type_id.rule_line_ids and self.duration_type == 'days':
            for recd in self.overtime_type_id.rule_line_ids:
                if recd.from_hrs < self.days_no_tmp <= recd.to_hrs and self.contract_id:
                    if self.contract_id.over_day:
                        cash_amount = self.contract_id.over_day * recd.hrs_amount
                        self.cash_day_amount = cash_amount
                    else:
                        raise UserError(_("Day Overtime Needs Day Wage in Employee Contract."))

    def submit_to_f(self):
        self.sudo().write({
            'state': 'f_approve',
            'date_f_approve': datetime.datetime.now(),
            'last_approval_date': datetime.datetime.now()
        })
    #     # notification to employee
    #     recipient_partners = [(4, self.current_user.partner_id.id)]
    #     body = "Your OverTime Request Waiting Finance Approve .."
    #     msg = _(body)
    #     # if self.current_user:
    #     #     self.message_post(body=msg, partner_ids=recipient_partners)
    #
    #     # notification to finance :
    #     group = self.env.ref('account.group_account_invoice', False)
    #     recipient_partners = []
    #     # for recipient in group.users:
    #     #     recipient_partners.append((4, recipient.partner_id.id))
    #
    #     body = "You Get New Time in Lieu Request From Employee : " + str(
    #         self.employee_id.name)
    #     msg = _(body)
    #     # self.message_post(body=msg, partner_ids=recipient_partners)
    #     # if self.env.user.has_group('ebs_manpower_transfer.group_site_fm_supervisor') and \
    #     #         self.overtime_category == 'fm_a9_a5':
    #     #     self.sudo().write({
    #     #         'state': 'f_approve',
    #     #         'date_f_approve': datetime.datetime.now(),
    #     #         'last_approval_date': datetime.datetime.now()
    #     #     })
    #     # elif self.env.user.has_group('ebs_manpower_transfer.group_section_head') and \
    #     #         self.overtime_category == 'technical':
    #         self.sudo().write({
    #             'state': 'f_approve',
    #             'date_f_approve': datetime.datetime.now(),
    #             'last_approval_date': datetime.datetime.now()
    #     #     })
    #     # elif self.env.user.has_group('ebs_manpower_transfer.group_pmAndFm_manger') and \
    #     #         self.overtime_category == 'pm':
    #     #     self.sudo().write({
    #     #         'state': 'f_approve',
    #     #         'date_f_approve': datetime.datetime.now(),
    #     #         'last_approval_date': datetime.datetime.now()
    #     #     })
    #     # elif self.overtime_category == 'fm_a4_a1':
    #     #     if self.env.user.has_group('ebs_manpower_transfer.group_site_fm_manager') or \
    #     #             self.env.user.has_group('ebs_manpower_transfer.group_fm_incharge'):
    #     #         self.sudo().write({
    #     #             'state': 'f_approve',
    #     #             'date_f_approve': datetime.datetime.now(),
    #     #             'last_approval_date': datetime.datetime.now()
    #     #         })
    #     #     else:
    #     #         raise ValidationError(_('You do not have authority to approve it.'))
    #     if self.env.user.has_group('ebs_manpower_transfer.group_site_fm_supervisor') and \
    #             self.overtime_category == 'fm_a9_a5':
    #         pass
    #     elif self.env.user.has_group('ebs_manpower_transfer.group_section_head') and \
    #             self.overtime_category == 'technical':
    #         pass
    #     elif self.env.user.has_group('ebs_manpower_transfer.group_pmAndFm_manger') and \
    #             self.overtime_category == 'pm':
    #         pass
    #     elif self.overtime_category == 'fm_a4_a1':
    #         if self.env.user.has_group('ebs_manpower_transfer.group_site_fm_manager') or \
    #                 self.env.user.has_group('ebs_manpower_transfer.group_fm_incharge'):
    #             pass
    #         else:
    #             raise ValidationError(_('You do not have authority to approve it.'))
    #     else:
    #         raise ValidationError(_('You do not have authority to approve it.'))
    #     project_list = []
    #     project_user_list = []
    #     for each_employee_project in self.env.user.employee_id.project_id:
    #         project_user_list.append(each_employee_project.project_id.id)
    #     project_list.append(self.project_id.id)
    #     lst3 = [value for value in project_list if value in project_user_list]
    #     for each_in_project in lst3:
    #         employee_project = self.env['employee.project.line'].search(
    #             [('project_id', '=', each_in_project),
    #              ('employee_id', '=',
    #               self.env.user.employee_id.id)])
    #         if employee_project.job_title.code in ['group_site_fm_supervisor', 'group_section_head',
    #                                                'group_pmAndFm_manger', 'group_site_fm_manager',
    #                                                'group_fm_incharge']:
    #             self.sudo().write({
    #                 'state': 'f_approve',
    #                 'date_f_approve': datetime.datetime.now(),
    #                 'last_approval_date': datetime.datetime.now()
    #             })
    #         else:
    #             raise ValidationError(_('You do not have authority to approve it.'))
    #     all_users = []
    #     employee_project_line = self.env['employee.project.line'].search(
    #         [('project_id', '=', self.project_id.id),
    #          ('job_title.code', 'in', ['group_portfolio_operation_leads', 'group_department_manager_head',
    #                                    'group_site_fm_manager', 'group_pm_opertion_specialist_officer',
    #                                    'group_fm_incharge']),
    #          ('employee_id', '!=', self.employee_id.id)])
    #     if employee_project_line:
    #         for each in employee_project_line:
    #             if self.env.user.has_group('ebs_manpower_transfer.group_portfolio_operation_leads') and \
    #                     self.overtime_category == 'fm_a4_a1':
    #                 all_users.append(each)
    #             elif self.env.user.has_group('ebs_manpower_transfer.group_department_manager_head') and \
    #                     self.overtime_category == 'technical':
    #                 all_users.append(each)
    #             elif self.env.user.has_group('ebs_manpower_transfer.group_pm_opertion_specialist_officer') and \
    #                     self.overtime_category == 'pm':
    #                 all_users.append(each)
    #             elif self.overtime_category == 'fm_a9_a5':
    #                 if self.env.user.has_group('ebs_manpower_transfer.group_site_fm_manager') or \
    #                         self.env.user.has_group('ebs_manpower_transfer.group_fm_incharge'):
    #                     all_users.append(each)
    #         self._create_activity(all_users)

    def approve(self):
        self.sudo().write({
            'state': 'second_approve',
            'date_third_approve': datetime.datetime.now(),
            'last_approval_date': datetime.datetime.now()
        })
        if self.overtime_type_id.type == 'leave':
            if self.duration_type == 'days':
                holiday_vals = {
                    'name': 'Overtime',
                    'holiday_status_id': self.overtime_type_id.leave_type.id,
                    'number_of_days': self.days_no_tmp,
                    'notes': self.desc,
                    'holiday_type': 'employee',
                    'employee_id': self.employee_id.id,
                    'state': 'validate',
                }
            else:
                day_hour = self.days_no_tmp / HOURS_PER_DAY
                holiday_vals = {
                    'name': 'Overtime',
                    'holiday_status_id': self.overtime_type_id.leave_type.id,
                    'number_of_days': day_hour,
                    'notes': self.desc,
                    'holiday_type': 'employee',
                    'employee_id': self.employee_id.id,
                    'state': 'validate',
                }
            holiday = self.env['hr.leave.allocation'].sudo().create(
                holiday_vals)
            self.leave_id = holiday.id

        # notification to employee :
        # recipient_partners = [(4, self.current_user.partner_id.id)]
        # body = "Your Time In Lieu Request Has been Approved ..."
        # msg = _(body)
        # # self.message_post(body=msg, partner_ids=recipient_partners)
        if self.env.user.has_group('ohrms_overtime.group_portfolio_operation_leads') and \
                self.overtime_category == 'fm_a4_a1':
            pass
        elif self.env.user.has_group('ohrms_overtime.group_department_manager_head') and \
                self.overtime_category == 'technical':
            pass
        elif self.env.user.has_group('ohrms_overtime.group_pm_opertion_specialist_officer') and \
                self.overtime_category == 'pm':
            pass
        elif self.overtime_category == 'fm_a9_a5':
            if self.env.user.has_group('ohrms_overtime.group_site_fm_manager') or \
                    self.env.user.has_group('ohrms_overtime.group_fm_incharge'):
                pass
            else:
                raise ValidationError(_('You do not have authority to approve it.'))
        else:
            raise ValidationError(_('You do not have authority to approve it.'))
        # project_list = []
        # project_user_list = []
        # for each_employee_project in self.env.user.employee_id.project_id:
        #     project_user_list.append(each_employee_project.project_id.id)
        # project_list.append(self.project_id.id)
        # lst3 = [value for value in project_list if value in project_user_list]
        # for each_in_project in lst3:
        #     employee_project = self.env['employee.project.line'].search(
        #         [('project_id', '=', each_in_project),
        #          ('employee_id', '=',
        #           self.env.user.employee_id.id)])
        #     if employee_project.job_title.code in ['group_portfolio_operation_leads', 'group_site_fm_manager',
        #                                            'group_department_manager_head', 'group_fm_incharge',
        #                                            'group_pm_opertion_specialist_officer']:
        #         self.sudo().write({
        #             'state': 'second_approve',
        #             'date_second_approve': datetime.datetime.now(),
        #             'last_approval_date': datetime.datetime.now()
        #         })
        #     else:
        #         raise ValidationError(_('You do not have authority to approve it.'))
        # all_users = []
        # employee_project_line = self.env['employee.project.line'].search(
        #     [('project_id', '=', self.project_id.id),
        #      ('job_title.code', 'in', ['group_portfolio_operation_leads', 'group_manager_of_pmAndFm',
        #                                'group_director_of_operation']),
        #      ('employee_id', '!=', self.employee_id.id)])
        # if employee_project_line:
        #     for each in employee_project_line:
        #         if self.env.user.has_group('ebs_manpower_transfer.group_manager_of_pmAndFm') and \
        #                 self.overtime_category == 'fm_a4_a1':
        #             all_users.append(each)
        #         elif self.env.user.has_group('ebs_manpower_transfer.group_director_of_operation') and \
        #                 self.overtime_category == 'technical':
        #             all_users.append(each)
        #         elif self.env.user.has_group('ebs_manpower_transfer.group_manager_of_pmAndFm') and \
        #                 self.overtime_category == 'pm':
        #             all_users.append(each)
        #         elif self.env.user.has_group('ebs_manpower_transfer.group_portfolio_operation_leads') and \
        #                 self.overtime_category == 'fm_a9_a5':
        #             all_users.append(each)
        #     self._create_activity(all_users)

    def second_approve(self):
        if self.env.user.has_group('ohrms_overtime.group_manager_of_pmAndFm') and \
                self.overtime_category == 'fm_a4_a1':
            pass
        elif self.env.user.has_group('ohrms_overtime.group_director_of_operation') and \
                self.overtime_category == 'technical':
            pass
        elif self.env.user.has_group('ohrms_overtime.group_manager_of_pmAndFm') and \
                self.overtime_category == 'pm':
            pass
        elif self.env.user.has_group('ohrms_overtime.group_portfolio_operation_leads') and \
                self.overtime_category == 'fm_a9_a5':
            pass
        else:
            raise ValidationError(_('You do not have authority to approve it.'))
        self.sudo().write({
            'state': 'third_approve',
            'date_third_approve': datetime.datetime.now(),
            'last_approval_date': datetime.datetime.now()
        })

    #     project_list = []
    #     project_user_list = []
    #     for each_employee_project in self.env.user.employee_id.project_id:
    #         project_user_list.append(each_employee_project.project_id.id)
    #     project_list.append(self.project_id.id)
    #     lst3 = [value for value in project_list if value in project_user_list]
    #     for each_in_project in lst3:
    #         employee_project = self.env['employee.project.line'].search(
    #             [('project_id', '=', each_in_project),
    #              ('employee_id', '=',
    #               self.env.user.employee_id.id)])
    #         if employee_project.job_title.code in ['group_manager_of_pmAndFm', 'group_director_of_operation',
    #                                                'group_manager_of_pmAndFm', 'group_portfolio_operation_leads']:
    #             self.sudo().write({
    #                 'state': 'third_approve',
    #                 'date_third_approve': datetime.datetime.now(),
    #                 'last_approval_date': datetime.datetime.now()
    #             })
    #         else:
    #             raise ValidationError(_('You do not have authority to approve it.'))
    #     all_users = []
    #     employee_project_line = self.env['employee.project.line'].search(
    #         [('project_id', '=', self.project_id.id),
    #          ('job_title.code', 'in', ['group_portfolio_manger', 'group_ceo', 'group_manager_of_pmAndFm']),
    #          ('employee_id', '!=', self.employee_id.id)])
    #     if employee_project_line:
    #         for each in employee_project_line:
    #             if self.env.user.has_group('ebs_manpower_transfer.group_portfolio_manger') and \
    #                     self.overtime_category == 'fm_a4_a1':
    #                 all_users.append(each)
    #             elif self.env.user.has_group('ebs_manpower_transfer.group_ceo') and \
    #                     self.overtime_category == 'technical':
    #                 all_users.append(each)
    #             elif self.env.user.has_group('ebs_manpower_transfer.group_portfolio_manger') and \
    #                     self.overtime_category == 'pm':
    #                 all_users.append(each)
    #             elif self.env.user.has_group('ebs_manpower_transfer.group_manager_of_pmAndFm') and \
    #                     self.overtime_category == 'fm_a9_a5':
    #                 all_users.append(each)
    #         self._create_activity(all_users)

    def third_approve(self):
        if self.env.user.has_group('ohrms_overtime.group_portfolio_manger') and \
                self.overtime_category == 'fm_a4_a1':
            pass
        elif self.env.user.has_group('ohrms_overtime.group_ceo') and \
                self.overtime_category == 'technical':
            pass
        elif self.env.user.has_group('ohrms_overtime.group_portfolio_manger') and \
                self.overtime_category == 'pm':
            pass
        elif self.env.user.has_group('ohrms_overtime.group_manager_of_pmAndFm') and \
                self.overtime_category == 'fm_a9_a5':
            pass
        else:
            raise ValidationError(_('You do not have authority to approve it.'))
        self.sudo().write({
            'state': 'fourth_approve',
            'date_fourth_approve': datetime.datetime.now(),
            'last_approval_date': datetime.datetime.now()
        })
        project_list = []

    #     project_user_list = []
    #     for each_employee_project in self.env.user.employee_id.project_id:
    #         project_user_list.append(each_employee_project.project_id.id)
    #     project_list.append(self.project_id.id)
    #     lst3 = [value for value in project_list if value in project_user_list]
    #     for each_in_project in lst3:
    #         employee_project = self.env['employee.project.line'].search(
    #             [('project_id', '=', each_in_project),
    #              ('employee_id', '=',
    #               self.env.user.employee_id.id)])
    #         if employee_project.job_title.code in ['group_portfolio_manger', 'group_ceo',
    #                                                'group_manager_of_pmAndFm']:
    #             self.sudo().write({
    #                 'state': 'fourth_approve',
    #                 'date_fourth_approve': datetime.datetime.now(),
    #                 'last_approval_date': datetime.datetime.now()
    #             })
    #         else:
    #             raise ValidationError(_('You do not have authority to approve it.'))
    #     all_users = []
    #     employee_project_line = self.env['employee.project.line'].search(
    #         [('project_id', '=', self.project_id.id),
    #          ('job_title.code', 'in', ['group_portfolio_manger', 'group_director_of_operation',
    #                                    'group_hr_department_user']),
    #          ('employee_id', '!=', self.employee_id.id)])
    #     if employee_project_line:
    #         for each in employee_project_line:
    #             if self.env.user.has_group('ebs_manpower_transfer.group_portfolio_manger') and \
    #                     self.overtime_category == 'fm_a9_a5':
    #                 all_users.append(each)
    #             elif self.env.user.has_group('ebs_manpower_transfer.group_director_of_operation') and \
    #                     self.overtime_category == 'fm_a4_a1':
    #                 all_users.append(each)
    #             elif self.env.user.has_group('ebs_manpower_transfer.group_director_of_operation') and \
    #                     self.overtime_category == 'pm':
    #                 all_users.append(each)
    #             elif self.env.user.has_group('ebs_manpower_transfer.group_hr_department_user') and \
    #                     self.overtime_category == 'technical':
    #                 all_users.append(each)
    #         self._create_activity(all_users)
    #
    def fourth_approve(self):
        if self.env.user.has_group('ohrms_overtime.group_portfolio_manger') and \
                self.overtime_category == 'fm_a9_a5':
            pass
        elif self.env.user.has_group('ohrms_overtime.group_director_of_operation') and \
                self.overtime_category == 'fm_a4_a1':
            pass
        elif self.env.user.has_group('ohrms_overtime.group_director_of_operation') and \
                self.overtime_category == 'pm':
            pass
        elif self.env.user.has_group('ohrms_overtime.group_hr_department_user') and \
                self.overtime_category == 'technical':
            pass
        else:
            raise ValidationError(_('You do not have authority to approve it.'))
        self.sudo().write({
            'state': 'fifth_approve',
            'date_fifth_approve': datetime.datetime.now(),
            'last_approval_date': datetime.datetime.now()
        })

    #     project_list = []
    #     project_user_list = []
    #     for each_employee_project in self.env.user.employee_id.project_id:
    #         project_user_list.append(each_employee_project.project_id.id)
    #     project_list.append(self.project_id.id)
    #     lst3 = [value for value in project_list if value in project_user_list]
    #     for each_in_project in lst3:
    #         employee_project = self.env['employee.project.line'].search(
    #             [('project_id', '=', each_in_project),
    #              ('employee_id', '=',
    #               self.env.user.employee_id.id)])
    #         if employee_project.job_title.code in ['group_portfolio_manger', 'group_director_of_operation']:
    #             self.sudo().write({
    #                 'state': 'fifth_approve',
    #                 'date_fifth_approve': datetime.datetime.now(),
    #                 'last_approval_date': datetime.datetime.now()
    #             })
    #         elif employee_project.job_title.code in ['group_hr_department_user']:
    #             self.sudo().write({
    #                 'state': 'approved',
    #                 'date_validated': datetime.datetime.now()
    #             })
    #         else:
    #             raise ValidationError(_('You do not have authority to approve it.'))
    #     all_users = []
    #     employee_project_line = self.env['employee.project.line'].search(
    #         [('project_id', '=', self.project_id.id),
    #          ('job_title.code', 'in', ['group_director_of_operation', 'group_ceo']),
    #          ('employee_id', '!=', self.employee_id.id)])
    #     if employee_project_line:
    #         for each in employee_project_line:
    #             if self.env.user.has_group('ebs_manpower_transfer.group_director_of_operation') and \
    #                     self.overtime_category == 'fm_a9_a5':
    #                 all_users.append(each)
    #             elif self.env.user.has_group('ebs_manpower_transfer.group_ceo') and \
    #                     self.overtime_category == 'fm_a4_a1':
    #                 all_users.append(each)
    #             elif self.env.user.has_group('ebs_manpower_transfer.group_ceo') and \
    #                     self.overtime_category == 'pm':
    #                 all_users.append(each)
    #         self._create_activity(all_users)

    def fifth_approve(self):
        if self.env.user.has_group('ohrms_overtime.group_director_of_operation') and \
                self.overtime_category == 'fm_a9_a5':
            pass
        elif self.env.user.has_group('ohrms_overtime.group_ceo') and \
                self.overtime_category == 'fm_a4_a1':
            pass
        elif self.env.user.has_group('ohrms_overtime.group_ceo') and \
                self.overtime_category == 'pm':
            pass
        else:
            raise ValidationError(_('You do not have authority to approve it.'))
        self.sudo().write({
            'state': 'sixth_approve',
            'date_sixth_approve': datetime.datetime.now(),
            'last_approval_date': datetime.datetime.now()
        })
        # project_list = []
        # project_user_list = []
        # for each_employee_project in self.env.user.employee_id.project_id:
        #     project_user_list.append(each_employee_project.project_id.id)
        # project_list.append(self.project_id.id)
        # lst3 = [value for value in project_list if value in project_user_list]
        # for each_in_project in lst3:
        #     employee_project = self.env['employee.project.line'].search(
        #         [('project_id', '=', each_in_project),
        #          ('employee_id', '=',
        #           self.env.user.employee_id.id)])
        #     if employee_project.job_title.code in ['group_director_of_operation', 'group_ceo']:
        #         self.sudo().write({
        #             'state': 'sixth_approve',
        #             'date_sixth_approve': datetime.datetime.now(),
        #             'last_approval_date': datetime.datetime.now()
        #         })
        #     else:
        #         raise ValidationError(_('You do not have authority to approve it.'))
        # all_users = []
        # employee_project_line = self.env['employee.project.line'].search(
        #     [('project_id', '=', self.project_id.id),
        #      ('job_title.code', '=', 'group_hr_department_user'),
        #      ('employee_id', '!=', self.employee_id.id)])
        # if employee_project_line:
        #     for each in employee_project_line:
        #         if self.env.user.has_group('ebs_manpower_transfer.group_hr_department_user') and \
        #                 self.overtime_category == 'fm_a9_a5':
        #             all_users.append(each)
        #         elif self.env.user.has_group('ebs_manpower_transfer.group_hr_department_user') and \
        #                 self.overtime_category == 'fm_a4_a1':
        #             all_users.append(each)
        #         elif self.env.user.has_group('ebs_manpower_transfer.group_hr_department_user') and \
        #                 self.overtime_category == 'pm':
        #             all_users.append(each)
        #     self._create_activity(all_users)

    def sixth_approve(self):
        if self.type == 'leave':
            if self.duration_type == 'days':
                holiday_vals = {
                    'name': 'Overtime',
                    'holiday_status_id': self.holiday_status_id.id,
                    'number_of_days': self.days_no_tmp,
                    'notes': self.desc,
                    'holiday_type': 'employee',
                    'employee_id': self.employee_id.id,
                    'state': 'validate',
                }
            else:
                day_hour = self.days_no_tmp / 5
                holiday_vals = {
                    'name': 'Overtime',
                    'holiday_status_id': self.holiday_status_id.id,
                    'number_of_days': day_hour,
                    'notes': self.desc,
                    'holiday_type': 'employee',
                    'employee_id': self.employee_id.id,
                    'state': 'validate',
                    'year': datetime.datetime.now().year,
                }
            holiday = self.env['hr.leave.allocation'].sudo().create(
                holiday_vals)
            self.leave_id = holiday.id

        if self.env.user.has_group('ohrms_overtime.group_hr_department_user') and \
                self.overtime_category == 'fm_a9_a5':
            pass
        elif self.env.user.has_group('ohrms_overtime.group_hr_department_user') and \
                self.overtime_category == 'fm_a4_a1':
            pass
        elif self.env.user.has_group('ohrms_overtime.group_hr_department_user') and \
                self.overtime_category == 'pm':
            pass
        else:
            raise ValidationError(_('You do not have authority to approve it.'))
        self.sudo().write({
            'state': 'approved',
            'date_validated': datetime.datetime.now()
        })
        # project_list = []
        # project_user_list = []
        # for each_employee_project in self.env.user.employee_id.project_id:
        #     project_user_list.append(each_employee_project.project_id.id)
        # project_list.append(self.project_id.id)
        # lst3 = [value for value in project_list if value in project_user_list]
        # for each_in_project in lst3:
        #     employee_project = self.env['employee.project.line'].search(
        #         [('project_id', '=', each_in_project),
        #          ('employee_id', '=',
        #           self.env.user.employee_id.id)])
        #     if employee_project.job_title.code in ['group_hr_department_user']:
        #         self.sudo().write({
        #             'state': 'approved',
        #             'date_validated': datetime.now()
        #         })
        #     else:
        #         raise ValidationError(_('You do not have authority to approve it.'))

        # return {
        #     'name': _('Leave Adjust'),
        #     'context': {'default_til_id': self.id},
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'leave.adjust',
        #     'view_id': self.env.ref('leave_management.leave_adjust_wizard_view',
        #                             False).id,
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'target': 'new',
        # }

    def reject(self):

        self.state = 'refused'
        # return {
        #     'name': _('Refuse Business Trip'),
        #     'context': {'default_overtime_id': self.id},
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'refuse.wzrd',
        #     'view_id': self.env.ref('leave_management.refuse_wzrd_view',
        #                             False).id,
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'target': 'new',
        # }

    @api.constrains('date_from', 'date_to')
    def _check_date(self):
        for req in self:
            domain = [
                ('date_from', '<=', req.date_to),
                ('date_to', '>=', req.date_from),
                ('employee_id', '=', req.employee_id.id),
                ('id', '!=', req.id),
                ('state', 'not in', ['refused']),
            ]
            # nholidays = self.search_count(domain)
            # if nholidays:
            #     raise ValidationError(_(
            #         'You can not have 2 Overtime requests that overlaps on same day!'))

    @api.model
    def create(self, values):
        seq = self.env['ir.sequence'].next_by_code('hr.overtime') or '/'
        values['name'] = seq
        res = super(HrOverTime, self.sudo()).create(values)
        # all_users = []
        # employee_project_line = self.env['employee.project.line'].search(
        #     [('project_id', '=', self.project_id.id),
        #      ('job_title.code', 'in', ['group_site_fm_supervisor', 'group_section_head', 'group_pmAndFm_manger',
        #                                'group_site_fm_manager', 'group_fm_incharge']),
        #      ('employee_id', '!=', self.employee_id.id)])
        # if employee_project_line:
        #     for each in employee_project_line:
        #         if each.employee_id.env.user.has_group('ebs_manpower_transfer.group_site_fm_supervisor') and \
        #                 self.overtime_category == 'fm_a9_a5':
        #             all_users.append(each)
        #         elif each.employee_id.env.user.has_group('ebs_manpower_transfer.group_section_head') and \
        #                 self.overtime_category == 'technical':
        #             all_users.append(each)
        #         elif each.employee_id.env.user.has_group('ebs_manpower_transfer.group_pmAndFm_manger') and \
        #                 self.overtime_category == 'pm':
        #             all_users.append(each)
        #         elif self.overtime_category == 'fm_a4_a1':
        #             if each.employee_id.env.user.has_group('ebs_manpower_transfer.group_site_fm_manager') or \
        #                     each.employee_id.env.user.has_group('ebs_manpower_transfer.group_fm_incharge'):
        #                 all_users.append(each)
        #     self._create_activity(all_users)
        return res

    def unlink(self):
        for overtime in self.filtered(
                lambda overtime: overtime.state != 'draft'):
            raise UserError(
                _('You cannot delete TIL request which is not in draft state.'))
        return super(HrOverTime, self).unlink()

    @api.onchange('date_from', 'date_to', 'employee_id')
    def _onchange_date(self):
        holiday = False
        if self.contract_id and self.date_from and self.date_to:
            for leaves in self.contract_id.resource_calendar_id.global_leave_ids:
                leave_dates = []
                if leaves.date_from and leaves.date_to:
                    leave_diff = leaves.date_to - leaves.date_from
                    leave_dates = [leaves.date_from + timedelta(days=i) for i in range(0, leave_diff.days + 1)]
                # leave_dates = pd.date_range(leaves.date_from, leaves.date_to).date
                # overtime_dates = pd.date_range(self.date_from, self.date_to).date
                diff = self.date_to - self.date_from
                overtime_dates = [self.date_from + timedelta(days=i) for i in range(0, diff.days + 1)]
                for over_time in overtime_dates:
                    for leave_date in leave_dates:
                        if leave_date.date() == over_time:
                            holiday = True
            if holiday:
                self.write({
                    'public_holiday': 'You have Public Holidays in your Overtime request.'})
            else:
                self.write({'public_holiday': ' '})
            hr_attendance = self.env['hr.attendance'].search(
                [('check_in', '>=', self.date_from),
                 ('check_in', '<=', self.date_to),
                 ('employee_id', '=', self.employee_id.id)])
            self.update({
                'attendance_ids': [(6, 0, hr_attendance.ids)]
            })

    def _create_activity(self, all_users):
        activity_to_do = self.env.ref('mail.mail_activity_data_todo').id
        model_id = self.env['ir.model']._get('hr.overtime').id
        activity = self.env['mail.activity']
        for user in all_users:
            if user:
                act_dct = {
                    'activity_type_id': activity_to_do,
                    'note': "kindly check this overtime Approval Request, it's awaiting your approval",
                    'user_id': user.employee_id.user_id.id,
                    'res_id': self.id,
                    'res_model_id': model_id,
                    'date_deadline': datetime.today().date()
                }
                activity.sudo().create(act_dct)


class HrOverTimeType(models.Model):
    _name = 'overtime.type'

    name = fields.Char('Name')
    type = fields.Selection([('cash', 'Cash'),
                             ('leave', 'Leave ')])

    duration_type = fields.Selection([('hours', 'Hour'), ('days', 'Days')], string="Duration Type", default="hours",
                                     required=True)
    leave_type = fields.Many2one('hr.leave.type', string='Leave Type', domain="[('id', 'in', leave_compute)]")
    leave_compute = fields.Many2many('hr.leave.type', compute="_get_leave_type")
    rule_line_ids = fields.One2many('overtime.type.rule', 'type_line_id')

    @api.onchange('duration_type')
    def _get_leave_type(self):
        dur = ''
        ids = []
        if self.duration_type:
            if self.duration_type == 'days':
                dur = 'day'
            else:
                dur = 'hour'
            leave_type = self.env['hr.leave.type'].search([('request_unit', '=', dur)])
            for recd in leave_type:
                ids.append(recd.id)
            self.leave_compute = ids


class HrOverTimeTypeRule(models.Model):
    _name = 'overtime.type.rule'

    type_line_id = fields.Many2one('overtime.type', string='Over Time Type')
    name = fields.Char('Name', required=True)
    from_hrs = fields.Float('From', required=True)
    to_hrs = fields.Float('To', required=True)
    hrs_amount = fields.Float('Rate', required=True)
