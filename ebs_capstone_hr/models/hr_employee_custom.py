# -*- coding: utf-8 -*-
import base64
import os
from datetime import date
from datetime import datetime
from dateutil import relativedelta
from odoo import models, fields, api
from odoo.addons.hr_holidays.models.hr_employee import HrEmployeeBase


class HrEmployeeCustom(models.AbstractModel):
    _inherit = "hr.employee.base"

    is_manager = fields.Boolean(string='Is Manager')
    signatory = fields.Boolean(string='Signatory')
    # signatory_image = fields.Binary(string="Signatory Image")
    ikama = fields.Char(string='Residence Permit')
    joining_date = fields.Date(string='Joining Date')
    permit_expire = fields.Date(string='Permit Expire Date')
    work_permit = fields.Boolean(string='Work Permit')
    status = fields.Selection(
        [('active', 'Active'), ('on vacation', 'On Vacation'), ('suspended', 'Suspended'),
         ('terminated', 'Terminated'), ('terminated_w_reason', 'Terminated with Reason'), ('resigned', 'Resigned')],
        string='Status')
    sponsorship_type = fields.Selection([('on the company', 'On the company'), ('on the familly', 'On the familly')],
                                        string='Sponsorship Type')
    contract_duration = fields.Selection(
        [('one', 'One'), ('two', 'Two'), ('three', 'Three'), ('four', 'Four'), ('five', 'Five'),
         ('open-ended', 'Unlimited')], string='Contract Duration', default='open-ended')
    # annual_leave = fields.Float(string='Annual Leave')
    health_card = fields.Char(string='Health Card #')
    # driving_license = fields.Char(string="Driving License")
    owns_car = fields.Boolean(string='Owns a car')
    sim_card = fields.Char(string=' SIM Card #')
    # bank_name = fields.Char(string='Bank Name')
    bank_account_nb = fields.Char(string='Bank #')
    extension = fields.Char(string='Ext')

    probation = fields.Selection([('90d', '3 Months'), ('180d', '6 Months')], string="Probation", default='180d')
    probation_date = fields.Date("Probation Date", compute='_get_probation_date')

    is_end_probation_period = fields.Boolean(string='End Probation Period')

    @api.onchange('joining_date', 'probation')
    def _get_probation_date(self):
        for rec in self:
            pro_date = 0
            if rec.probation == '90d' and rec.joining_date:
                pro_date = rec.joining_date + relativedelta.relativedelta(days=+90)
            elif rec.probation == '180d' and rec.joining_date:
                pro_date = rec.joining_date + relativedelta.relativedelta(days=+180)
            rec.probation_date = pro_date

    @api.model
    def create(self, values):
        # Override the default behaviour
        # to stop adding group hr responsible to users
        if 'parent_id' in values:
            manager = self.env['hr.employee'].browse(values['parent_id']).user_id
            values['leave_manager_id'] = values.get('leave_manager_id', manager.id)
        # if values.get('leave_manager_id', False):
        #     approver_group = self.env.ref('hr_holidays.group_hr_holidays_responsible', raise_if_not_found=False)
        #     if approver_group:
        #         approver_group.sudo().write({'users': [(4, values['leave_manager_id'])]})
        return super(HrEmployeeBase, self).create(values)

    def write(self, values):
        if 'parent_id' in values:
            manager = self.env['hr.employee'].browse(values['parent_id']).user_id
            if manager:
                to_change = self.filtered(lambda e: e.leave_manager_id == e.parent_id.user_id or not e.leave_manager_id)
                to_change.write({'leave_manager_id': values.get('leave_manager_id', manager.id)})
        # Override the default behaviour
        # to stop adding group hr responsible to portal users

        # old_managers = self.env['res.users']
        # if 'leave_manager_id' in values:
        #     old_managers = self.mapped('leave_manager_id')
        #     if values['leave_manager_id']:
        #         old_managers -= self.env['res.users'].browse(values['leave_manager_id'])
        #         approver_group = self.env.ref('hr_holidays.group_hr_holidays_responsible', raise_if_not_found=False)
        #         if approver_group:
        #             approver_group.sudo().write({'users': [(4, values['leave_manager_id'])]})

        res = super(HrEmployeeBase, self).write(values)
        # remove users from the Responsible group if they are no longer leave managers
        # old_managers._clean_leave_responsible_users()

        if 'parent_id' in values or 'department_id' in values:
            today_date = fields.Datetime.now()
            hr_vals = {}
            if values.get('parent_id') is not None:
                hr_vals['manager_id'] = values['parent_id']
            if values.get('department_id') is not None:
                hr_vals['department_id'] = values['department_id']
            holidays = self.env['hr.leave'].sudo().search(
                ['|', ('state', 'in', ['draft', 'confirm']), ('date_from', '>', today_date),
                 ('employee_id', 'in', self.ids)])
            holidays.write(hr_vals)
            allocations = self.env['hr.leave.allocation'].sudo().search(
                [('state', 'in', ['draft', 'confirm']), ('employee_id', 'in', self.ids)])
            allocations.write(hr_vals)
        return res


class HREmployee(models.Model):
    _inherit = "hr.employee"
    _order = 'registration_number'

    # seq_number = fields.Char(string="sequence NO.", required=True, copy=False, index=True, default='')
    signatory_image = fields.Binary(string="Signatory Image")
    # letter_ids = fields.One2many('ebs.hr.letter.request', 'employee_id', string='Letter Requests', readonly=True)
    waseef_document_count = fields.Integer(string='Document', compute='get_document_count')
    # letter_count = fields.Integer(compute='_compute_letter_count', string='Letters Count',
    #                               groups="base.group_user")
    payslip_count = fields.Integer(groups="base.group_user")
    # marital = fields.Selection(groups="base.group_user")
    barcode = fields.Char(groups="base.group_user")
    address_home_id = fields.Many2one(groups="base.group_user")
    spouse_complete_name = fields.Char(groups="base.group_user")
    spouse_birthdate = fields.Date(groups="base.group_user")
    children = fields.Integer(groups="base.group_user")
    place_of_birth = fields.Char(groups="base.group_user")
    country_of_birth = fields.Many2one(groups="base.group_user")
    birthday = fields.Date(groups="base.group_user")
    ssnid = fields.Char(groups="base.group_user")
    sinid = fields.Char(groups="base.group_user")
    identification_id = fields.Char(groups="base.group_user")
    passport_id = fields.Char(groups="base.group_user")
    bank_account_id = fields.Many2one(groups="base.group_user")
    bank_name = fields.Char(related="bank_account_id.bank_id.name", string='Bank Name')
    permit_no = fields.Char(groups="base.group_user")
    additional_note = fields.Text(groups="base.group_user")
    certificate = fields.Selection(groups="base.group_user")
    study_field = fields.Char(groups="base.group_user")
    study_school = fields.Char(groups="base.group_user")
    emergency_contact = fields.Char(groups="base.group_user")
    emergency_phone = fields.Char(groups="base.group_user")
    km_home_work = fields.Integer(groups="base.group_user")
    phone = fields.Char(groups="base.group_user")
    waseef_sponsor = fields.Many2one(comodel_name="hr.employee.sponsor", string="Waseef Sponsor", required=False, )
    bank_account_type = fields.Selection(string="Bank Account Type", default="", selection=[('personal', 'Personal'),
                                                                                            ('card', 'PayCard')],
                                         required=False, )
    number_of_years_work = fields.Char("Yrs w/ Waseef", compute="_get_number_of_days_work")
    sim_card = fields.Char(string=' SIM Card #')

    @api.depends('joining_date')
    def _get_number_of_days_work(self):
        today = fields.Date.today()
        for rec in self:
            if rec.joining_date and today > rec.joining_date:
                diff = relativedelta.relativedelta(today, rec.joining_date)
                rec.number_of_years_work = f'{diff.years} y, {diff.months} m'
            else:
                rec.number_of_years_work = 0

    # def _compute_letter_count(self):
    #     for employee in self:
    #         employee.letter_count = len(employee.letter_ids)

    # def print_letters(self):
    #     doc = None
    #     name = ""
    #     if self._context.get('report_type') == 'letter_to_embassy':
    #         name = 'Letter To Embassy.docx'
    #         doc = self.letter_to_embassy()
    #
    #     elif self._context.get('report_type') == 'salary_breakdown':
    #         name = 'Salary Breakdown.docx'
    #         doc = self.salary_breakdown()
    #
    #     elif self._context.get('report_type') == 'open_bank_account':
    #         name = 'Salary certificate open bank account.docx'
    #         doc = self.open_bank_account()
    #
    #     elif self._context.get('report_type') == 'salary_certificate':
    #         name = 'Salary Certificate.docx'
    #         doc = self.employment_and_salary_certificate()
    #
    #     elif self._context.get('report_type') == 'salary_transfer_letter':
    #         name = 'Salary Transfer Letter.docx'
    #         doc = self.salary_transfer_letter()
    #
    # elif self._context.get('report_type') == 'bank_account_certificate':
    #     name = 'Bank Account Certificate.docx'
    #     doc = self.employment_and_salary_certificate()
    #
    # elif self._context.get('report_type') == 'bank_account_letter':
    #     name = 'Bank Account Letter.docx'
    #     doc = self.open_bank_account()
    #
    # elif self._context.get('report_type') == 'memo':
    #     name = 'Memo.docx'
    #     doc = self.memo_template()
    #
    # elif self._context.get('report_type') == 'liquor_permit':
    #     name = 'Liquor Permit.docx'
    #     doc = self.liquor_permit()
    #
    # elif self._context.get('report_type') == 'receipt_labour_contract':
    #     name = 'Receipt LabourContract.docx'
    #     doc = self.receipt_labour_contract()
    #
    # elif self._context.get('report_type') == 'joining_form':
    #     name = 'Joining Form.docx'
    #     doc = self.joining_form()
    #
    # elif self._context.get('report_type') == 'employee_emergency_contacts':
    #     name = 'Employee Emergency Contacts.docx'
    #     doc = self.employee_emergency_contacts()
    #
    # elif self._context.get('report_type') == 'leave_request_form':
    #     name = 'Leave Request Form.docx'
    #     doc = self.leave_request_form()
    #
    # elif self._context.get('report_type') == 'rider_drivers_company_assets':
    #     name = 'Rider Drivers Company Assets.docx'
    #     doc = self.rider_drivers_company_assets()

    # doc.save(name)
    #
    # binary_doc = open(name, 'rb')
    # doc_data = base64.b64encode(binary_doc.read())
    # record = self.env['ebs.hr.letters.model'].create({
    #     'name': name,
    #     'datas': doc_data
    # })
    #
    # binary_doc.close()
    # os.remove(name)
    # # self.ensure_one()
    # action = {
    #     'type': "ir.actions.act_url",
    #     'target': "_blank",
    #     'url': '/documents/content/download/%s' % record.id
    # }
    #
    # return action

    def get_document_count(self):
        for data in self:
            data.waseef_document_count = self.env['ebs.hr.document'].search_count([('employee_id', '=', data.id)])

    def custom_open_document(self):
        self.ensure_one()
        # print(self)
        # for doc in self:

        return {
            'name': 'Documents',
            'domain': [('employee_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'ebs.hr.document',
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
            'context': {
                'default_employee_id': self.id
            }

        }

    def get_email(self):
        emails = self.env['hr.employee'].search([('work_email', '!=', False)]).mapped('work_email')
        return emails

    def check_employee_birthday(self):
        template_id = self.env.ref('ebs_capstone_hr.email_template_birthday').id
        template = self.env['mail.template'].browse(template_id)
        # today_date = date.today().strftime('%m-%d')
        today_date = date.today()
        for rec in self.env['hr.employee'].search([('active', '=', True), ('birthday', '!=', False)]):
            # email_list = []
            # birth_date = rec.birthday.strftime('%m-%d')
            if rec.birthday.month == today_date.month and today_date.day == rec.birthday.day:
                email_list = self.env['hr.employee'].search([('work_email', '!=', False)]).mapped('work_email')
                # for employee in self.env['hr.employee'].search([]):
                #     if employee.:
                #         email_list.append(employee.work_email)
                template.write({'email_to': rec.work_email})
                template.write({'email_cc': email_list})
                template.send_mail(rec.id, force_send=True)

    def check_employee_birthday_event_preparation(self):
        template_id = self.env.ref('ebs_capstone_hr.email_template_birthday_event_preparation').id
        template = self.env['mail.template'].browse(template_id)

        for rec in self.env['hr.employee'].search([('active', '=', True)]):
            email_list = []
            if rec.birthday:
                birth_date = rec.birthday.month
                today_date = date.today().month

                # today_date = date.today().strftime('%m-%d')

                if birth_date == today_date:
                    for employee in self.env['hr.employee'].search([]):
                        email_list.append(employee.work_email)
                    template.write({'email_to': rec.work_email})
                    template.send_mail(rec.id, force_send=True)

    def check_employee_birthday_event_reminder(self):
        template_id = self.env.ref('ebs_capstone_hr.email_template_birthday_event_reminder').id
        template = self.env['mail.template'].browse(template_id)
        for rec in self.env['hr.employee'].search([('active', '=', True)]):
            email_list = []
            if rec.birthday:
                birth_date = rec.birthday.month
                today_date = date.today().month

                # today_date = date.today().strftime('%m-%d')

                if birth_date - today_date == -1:
                    for employee in self.env['hr.employee'].search([]):
                        email_list.append(employee.work_email)
                    template.write({'email_to': rec.work_email})
                    template.send_mail(rec.id, force_send=True)



class InheritHREmployee(models.Model):
    _inherit = 'hr.employee.public'

    is_manager = fields.Boolean(string='Is Manager')
