from datetime import date
from odoo import models, fields, api
import json


class HrDocument(models.Model):
    _name = 'ebs.hr.document'
    _description = 'Hr Document'

    @api.depends('employee_id')
    def _document_type_passport_domain(self):
        for rec in self:
            if rec.employee_id:
                rec.employee_id_domain = json.dumps(
                    [('document_type.id', '=', self.env.ref('ebs_capstone_hr.hr_document_type_passport').id),
                     ('employee_id', '=', self.employee_id.id)])
            else:
                rec.employee_id_domain = json.dumps(
                    [('document_type.id', '=', self.env.ref('ebs_capstone_hr.hr_document_type_passport').id)])

    def _default_employee(self):
        return self.env.context.get('default_employee_id') or self.env.user.employee_id

    def _default_user(self):
        return self.env.user

    def _compute_current_user(self):
        for rec in self:
            rec.current_user = self.env.user

    name = fields.Char(string='Document Number')
    document_type = fields.Many2one('ebs.hr.document.type', string='Document Type', groups="base.group_user")
    state = fields.Selection([('active', 'Active'), ('expired', 'Expired')], string='Status', default='active')
    issue_date = fields.Date(string='Issue Date')
    expiration_date = fields.Date(string='Expiry Date')
    employee_id = fields.Many2one('hr.employee', string='Employee', default=_default_employee)
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)
    issue_place = fields.Char(string='Issue Place')
    child_id = fields.Many2one('ebs.hr.document', string='Passport')
    hide = fields.Boolean('Hide', compute="_compute_hide", default=False, store=True)

    # emp_projects = fields.Text(string='Projects', compute='')

    # # @api.depends('employee_id')
    # @api.onchange('employee_id')
    # def get_emp_projects(self):
    #     projects = ''
    #     employee_projects = self.env['hr.employee'].browse(self.employee_id.id).mapped('project_id')
    #     for rec in self:
    #         for project in employee_projects:
    #             if project.active:
    #                 projects += ' - ' + project.project_id.name
    #         rec.emp_projects = projects

    current_user = fields.Many2one('res.users', default=_default_user, compute="_compute_current_user")
    is_hr_user = fields.Boolean('Is hr user', compute="_compute_is_hr_user")
    employee_id_domain = fields.Char("Employee Domain", compute="_document_type_passport_domain")

    @api.depends('current_user')
    def _compute_is_hr_user(self):
        has_hr_group = self.current_user.has_group('hr.group_hr_user') or \
                       self.current_user.has_group('hr.group_hr_manager')

        for rec in self:
            if has_hr_group:
                rec.is_hr_user = True
            else:
                rec.is_hr_user = False

    # emp_projects = fields.Text(string='Projects', readonly=True)

    # @api.depends('employee_id')
    # @api.onchange('employee_id')
    # def get_emp_projects(self):
    #     employee_projects = self.env['hr.employee'].sudo().browse(self.employee_id.id).mapped('project_id')
    #     for rec in self:
    #         rec.emp_projects = ' - '.join([project.project_id.name for project in employee_projects if project])

    @api.depends('document_type')
    def _compute_hide(self):
        for rec in self:
            qid = rec.sudo().env.ref('ebs_capstone_hr.hr_document_type_qid').id
            visa = rec.sudo().env.ref('ebs_capstone_hr.hr_document_type_Visa').id
            health_card = rec.sudo().env.ref('ebs_capstone_hr.hr_document_type_healthcard').id
            if rec.document_type:
                if rec.document_type.id not in [qid, visa, health_card]:
                    rec.hide = True
                    rec.employee_id.depend_qid = True
                    rec.employee_id.depend_passport = True
                    rec.employee_id.depend_visa = True
                else:
                    rec.hide = False
                    rec.employee_id.depend_qid = False
                    rec.employee_id.depend_passport = False
                    rec.employee_id.depend_visa = False

    # has_reminder = fields.Boolean(string='Has Reminder', related='document_type.has_reminder')
    # days = fields.Integer(string='Reminder Days', related='document_type.days')

    def check_document_type_duration(self):
        for document in self.env['ebs.hr.document'].sudo().search([('state', '=', 'active')]):
            if document.document_type.has_reminder and document.expiration_date:
                template_id = document.document_type.template_id.id
                template = self.env['mail.template'].browse(template_id)
                end_date = document.expiration_date
                today_date = date.today()
                diff = today_date - end_date
                result = abs(diff.days)
                email_list = []
                if result == document.document_type.days:

                    for employee in self.env['hr.employee'].sudo().search(
                            [('department_id.is_human_resource', '=', True)]):
                        email_list.append(employee.work_email)

                    if 'Passport' in template.name:
                        email_list.append(document.employee_id.work_email)

                    if email_list:
                        template.write({'email_to': email_list})
                        template.send_mail(document.id, force_send=True)
