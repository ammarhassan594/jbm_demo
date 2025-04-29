from odoo import fields, models, api, _, Command
from odoo.exceptions import UserError, ValidationError
from lxml import etree
import json
from dateutil.relativedelta import relativedelta

import datetime


class HrResignation(models.Model):
    _inherit = 'hr.resignation'

    related_approval = fields.Many2one('approval.request', 'Approval Request')
    start_date = fields.Datetime(string='Effective Resignation Date')
    end_date = fields.Date(string='Last Working Date')


class HrResignationReason(models.Model):
    _name = 'hr.resignation.reason'
    _description = 'HR Registration Reason'

    name = fields.Char(
        string='Name',
        required=True)
    description = fields.Char(
        string='Description',
        required=False)


class HrTransferReason(models.Model):
    _name = 'hr.transfer.reason'
    _description = 'HR Transfer Reason'

    name = fields.Char(
        string='Name',
        required=True)
    description = fields.Char(
        string='Description',
        required=False)


class HrResignationExtensionReason(models.Model):
    _name = 'hr.resignation.extension.reason'
    _description = 'HR Registration Extension Reason'

    name = fields.Char(
        string='Name',
        required=True)
    description = fields.Char(
        string='Description',
        required=False)


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    def _get_default_employee(self):
        return self.env['hr.employee'].search([('user_id', '=',
                                                self.env.user.id)],
                                              limit=1)

    @api.onchange('related_resign_request')
    def get_related_request_domain(self):
        if self.env.user.has_group('security_rules.group_fusion_employee'):
            print([sub.user_id for sub in self.env.user.employee_ids.subordinate_ids])
            res_request = self.env['hr.resignation'].sudo().search(
                ['|', ('related_employee.user_id', '=', self.env.user.id), (
                    'related_employee', 'in',
                    [sub.id for sub in self.env.user.employee_ids.subordinate_ids])])
            return {'domain': {'related_resign_request': [('id', 'in', [re.id for re in res_request])]}}
        return {'domain': {'related_resign_request': []}}

    approver_ids = fields.One2many('approval.approver', 'request_id', string="Approvers", compute=False)
    vacancy_type = fields.Selection([('internal', 'Internal'), ('external', 'External')],
                                    string='Vacancy Process Type')
    job_desc = fields.Text('Job Description')
    replacement_employee_id = fields.Many2one('hr.employee', string='Replacing (Employee)')
    contract_type = fields.Selection([('open', 'Open'), ('contract', 'Contract')], string='Vacancy Type')
    requisition_type = fields.Selection([('replace', 'Replacement'), ('new', 'New Requirement')],
                                        string='Requisition Type')
    requisition_period_type = fields.Selection([('temporary', 'Temporary'), ('new', 'Permanent')],
                                               string='Requisition Period')
    # qty = fields.Integer("Quantity")
    start_date = fields.Date("Expected Starting Date")
    other_remarks = fields.Text("Other Remarks")
    can_create_job = fields.Boolean('Create Job', compute='_create_job', default=False, store=True)
    can_create_resign = fields.Boolean('Create Resign', compute='_create_resign', default=False, store=True)
    can_extend_resign = fields.Boolean('Extend Resign', compute='_extend_resign', default=False, store=True)
    can_create_transfer = fields.Boolean('Create Transfer', compute='_create_transfer', default=False, store=True)
    related_job = fields.One2many('hr.job', 'related_requisition', string='Related Jobs')
    is_head_department_approver = fields.Boolean(related="category_id.is_head_department_approver")

    related_resign_request = fields.Many2one('hr.resignation', string='Previous Resignation Request')
    related_resign_date = fields.Date(related='related_resign_request.end_date', string='Previous Last Working Date')
    extend_till = fields.Date('Extend Till')
    direct_employee_id = fields.Many2one('hr.employee', string='Related Employee',
                                         compute='_get_direct_employee', store=True)

    related_employee_id = fields.Many2one('hr.employee', string='Name of the hiring Subsidiary',
                                          default=_get_default_employee)
    request_type_id = fields.Many2one(comodel_name="approval.request.type", string="Type",
                                      domain="[('category_id', '=', category_id)]")

    holiday_type_id = fields.Many2one(comodel_name="hr.leave.type", string="Leave Type",
                                      domain="[('requires_allocation', '=', 'yes')]")
    holiday_request_unit = fields.Selection(string="Request Unit", related='holiday_type_id.request_unit', store=True)

    leave_request_date = fields.Date(string="Leave Request Date")
    request_date_from_period = fields.Selection([
        ('am', 'Morning'), ('pm', 'Afternoon')],
        string="Date Period Start", default='am')
    leave_request_amount = fields.Float(string="Duration", required=False, )

    related_fusion_id = fields.Char(related='related_employee_id.fusion_id')
    related_system_id = fields.Char(related='related_employee_id.system_id')
    related_employment_status = fields.Selection(related='related_employee_id.contract_id.employment_status')

    related_contract = fields.Many2one('hr.contract', "Related Contract")
    resignation_date = fields.Date('Last Working Date')
    grade = fields.Many2one('job.grade', 'Grade')
    related_manager = fields.Many2one('hr.employee', 'Related Manager')
    related_oc = fields.Many2one('hr.department', 'Related OC')
    related_time_hired = fields.Char('Related Tenure of Experience')
    related_warnings = fields.One2many(string='Related Warnings', related='related_employee_id.notice_ids')
    notice_period = fields.Integer(related='grade.notice_period')
    job_position = fields.Many2one('hr.job', 'Job Position')
    job_title = fields.Many2one('job.title', 'Job Title')
    group = fields.Many2one('hr.department', string='Group', domain=[('type', '=', 'BU')])
    department = fields.Many2one('hr.department', string='Department', domain=[('type', '=', 'BD')])
    section = fields.Many2one('hr.department', string='Section', domain=[('type', '=', 'BS')])
    subsection = fields.Many2one('hr.department', string='Subsection', domain=[('type', '=', 'SS')])
    approval_date = fields.Datetime(
        string='Approval Date',
        required=False,
        readonly=True)

    all_approved = fields.Boolean(string='All Approved', compute='_get_all_approved')
    resignations = fields.One2many(
        comodel_name='hr.resignation',
        inverse_name='related_approval',
        string='Resignations',
        required=False)
    jobs = fields.One2many(
        comodel_name='hr.job',
        inverse_name='related_requisition',
        string='Jobs',
        required=False)
    transfers = fields.One2many(
        comodel_name='hr.employee.event',
        inverse_name='related_requisition',
        string='Events',
        required=False)
    resignations_ext = fields.One2many(
        comodel_name='hr.resignation',
        inverse_name='related_approval',
        string='Resignations',
        required=False)
    cost_center = fields.Many2one('hr.cost.center', string='Cost Center')
    personal_phone_no = fields.Char(string='Personal Phone Number')
    personal_email = fields.Char(string='Personal Email')
    replacement_position = fields.Selection(
        string='Replacement of the Position',
        selection=[('yes', 'Yes'),
                   ('no', 'No'), ])

    resignation_reason = fields.Many2one('hr.resignation.reason', string='Resignation Reason')
    resignation_extension_reason = fields.Many2one('hr.resignation.extension.reason',
                                                   string='Resignation Extension Reason')
    resignation_extension_reason_text = fields.Char(string='Resignation Extension Reason')

    read_only_user = fields.Boolean(default=False, compute='_get_user_group')

    created_job_position = fields.Many2one(
        comodel_name='hr.job',
        string='Created Job Position',
        required=False,
        compute='_get_created_job', store=True)
    # read_only_approval = fields.Boolean(compute='get_read_only_approval')
    read_only_approval = fields.Boolean()

    reason = fields.Text(string="Justification")

    request_status = fields.Selection([
        ('new', 'To Submit'),
        ('pending', 'Submitted'),
        ('under_approval', 'Under Approval'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
        ('cancel', 'Cancel')], default="new", compute="_compute_request_status", store=True, compute_sudo=True,
        group_expand='_read_group_request_status')

    # internal transfer fields
    employee_transferred = fields.Many2one(comodel_name='hr.employee', string='Employee Transferred')

    employee_fusion_id = fields.Char('Employee Main Company ID')
    transfer_type = fields.Selection([('temporary', 'Temporary'), ('permanent', 'Permanent')], 'Transfer Type')
    transfer_from_date = fields.Date(string='From Date', required=False)
    transfer_to_date = fields.Date(string='To Date', required=False)
    transfer_reason = fields.Many2one(comodel_name="hr.transfer.reason", string='Transfer Reason')

    employee_type_source = fields.Selection([('contractor', 'Contractor'), ('permanent', 'Permanent')],
                                            'Employee Type')
    employee_type_destination = fields.Selection([('contractor', 'Contractor'), ('permanent', 'Permanent')],
                                                 'Employee Type')

    cost_center_source = fields.Many2one(comodel_name="hr.cost.center", string='Cost Center')
    cost_center_destination = fields.Many2one(comodel_name="hr.cost.center", string='Cost Center')

    sap_source = fields.Selection([('yes', 'Active'), ('no', 'Inactive')], 'SAP Account')
    sap_destination = fields.Selection([('yes', 'Active'), ('no', 'Inactive')], 'SAP Account')

    f_3dx_source = fields.Selection([('yes', 'Active'), ('no', 'Inactive')], '3DX Account')
    f_3dx_destination = fields.Selection([('yes', 'Active'), ('no', 'Inactive')], '3DX Account')

    shared_folder_status_source = fields.Selection([('yes', 'Active'), ('no', 'Inactive')], 'Shared Folder Status')
    shared_folder_status_destination = fields.Selection([('yes', 'Active'), ('no', 'Inactive')], 'Shared Folder Status')

    shared_folder_source = fields.Char(string='Shared Folder Path')
    shared_folder_destination = fields.Char(string='Shared Folder Path')

    other_source = fields.Char(string='Other')
    other_destination = fields.Char(string='Other')

    job_title_source = fields.Many2one(comodel_name='job.title', string='Job Title')
    job_title_destination = fields.Many2one(comodel_name='job.title', string='Job Title')

    line_manager_source = fields.Many2one(comodel_name='hr.employee', string='Line Manager')
    line_manager_destination = fields.Many2one(comodel_name='hr.employee', string='Line Manager')

    group_source = fields.Many2one(comodel_name='hr.department', string='Group', domain=[('type', '=', 'BU')])
    group_destination = fields.Many2one(comodel_name='hr.department', string='Group',
                                        domain=[('type', '=', 'BU')])

    department_source = fields.Many2one(comodel_name='hr.department', string='Department',
                                        domain=[('type', '=', 'BD')])
    department_destination = fields.Many2one(comodel_name='hr.department', string='Department',
                                             domain=[('type', '=', 'BD')])

    section_source = fields.Many2one(comodel_name='hr.department', string='Section',
                                     domain=[('type', '=', 'BS')])
    section_destination = fields.Many2one(comodel_name='hr.department', string='Section',
                                          domain=[('type', '=', 'BS')])

    subsection_source = fields.Many2one(comodel_name='hr.department', string='SubSection',
                                        domain=[('type', '=', 'SS')])
    subsection_destination = fields.Many2one(comodel_name='hr.department', string='SubSection',
                                             domain=[('type', '=', 'SS')])

    job_grade_source = fields.Many2one(comodel_name='job.grade', string='Job Grade')
    job_grade_destination = fields.Many2one(comodel_name='job.grade', string='Job Grade')

    working_shift_source = fields.Many2one(comodel_name='resource.calendar', string='Working Shift')
    working_shift_destination = fields.Many2one(comodel_name='resource.calendar', string='Working Shift')

    status = fields.Char(
        string='Status',
        required=False)
    approval_job_line_ids = fields.One2many('approval.job.lines', 'approval_request_id', string='Approval Job')
    category_approval_type = fields.Selection(related="category_id.approval_type")
    request_employee_id = fields.Many2one('hr.employee', string="Employee")
    has_employee = fields.Selection(related="category_id.has_employee")
    has_request_type = fields.Selection(related="category_id.has_request_type")
    has_leave_type = fields.Selection(related="category_id.has_leave_type")
    has_leave_request_date = fields.Selection(related="category_id.has_leave_request_date")
    has_leave_amount = fields.Selection(related="category_id.has_leave_amount")
    advance_payment_type = fields.Text(string="Advance Payment Type")
    payment_installment_ids = fields.One2many('payment.installment', 'approval_request_id',
                                              string="Payment Installment")
    no_of_installment = fields.Integer(string="No of installment")
    previous_advance_payment = fields.Many2one('approval.request', string="Previous Advance Payment",
                                               compute="compute_previous_advance_payment", store=True)

    job_updated = fields.Boolean(string="Job Updated", default=False)

    def unlink(self):
        vals_list = []
        for record in self.filtered(lambda s: s.category_approval_type == 'advance_payment').sorted('id'):
            vals_list.append({
                'id': record.id or False,
                'request_employee_id': record.request_employee_id.id or False,
            })
        res = super().unlink()
        if res and vals_list:
            for record in vals_list:
                advance_payments = self.search(
                    [('id', '>', record.get('id')), ('request_employee_id', '=', record.get('request_employee_id'))],
                    order='id asc')
                if advance_payments:
                    advance_payments[0].compute_previous_advance_payment()
        return res

    @api.depends('request_employee_id')
    def compute_previous_advance_payment(self):
        self.previous_advance_payment = False
        for record in self:
            if record.request_employee_id and record.create_date:
                advance_payments = self.search(
                    [('id', '<', record._origin.id), ('request_employee_id', '=', self.request_employee_id.id)],
                    order='id asc')
                advance_payments = advance_payments.filtered(lambda s: s.category_approval_type == 'advance_payment')
                if advance_payments:
                    record.previous_advance_payment = advance_payments[-1]

    def generate_installment(self):
        if self.amount <= 0:
            raise UserError('Please enter amount more than zero')
        if self.no_of_installment <= 0:
            raise UserError('Please enter No of installment more than zero')
        for i in range(self.no_of_installment):
            self.write({
                'payment_installment_ids': [(0, 0, {
                    'installment_amount': self.amount / self.no_of_installment
                })]
            })

    def print_approval_request(self):
        report = self.env.ref('hr_approvals.approvals_action').report_action(self)
        return report

    def update_employee_in_job(self):
        if self.approval_job_line_ids:
            for line in self.approval_job_line_ids:
                if line.job_id and line.no_of_employees > 0:
                    line.job_id.sudo().write({'no_of_recruitment': line.no_of_employees})
            self.sudo().write({
                'job_updated': True,
            })

    # def get_read_only_approval(self):
    #     for rec in self:
    #         if self.env.user.has_group('security_rules.group_hc_employee'):
    #             rec.read_only_approval = False
    #         elif rec.request_status == 'new' and rec.request_owner_id.id == self.env.user.id:
    #             rec.read_only_approval = False
    #         elif rec.request_status != 'new' and self.env.user.id in rec.approver_ids.filtered(
    #                 lambda x: x.status == 'pending').user_id.ids:  # user_id.id
    #             rec.read_only_approval = False
    #         else:
    #             rec.read_only_approval = True

    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     res = super(ApprovalRequest, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
    #                                                        submenu=submenu)
    #     if view_type == "form":
    #         doc = etree.XML(res['arch'])
    #         for field in res['fields']:
    #             for node in doc.xpath("//field[@name='%s']" % field):
    #                 print(field)
    #                 if field == 'approver_ids' and self.env.user.has_group('security_rules.group_fusion_employee'):
    #                     print('in fct')
    #                     node.set("readonly", "1")
    #                     modifiers = json.loads(node.get("modifiers"))
    #                     modifiers['readonly'] = True
    #                     node.set("modifiers", json.dumps(modifiers))
    #                 else:
    #                     node.set("readonly", "[('read_only_approval','=',True)]")
    #                     modifiers = json.loads(node.get("modifiers"))
    #                     if not modifiers.get('readonly'):
    #                         modifiers['readonly'] = "[('read_only_approval','=',True)]"
    #                     elif modifiers.get('readonly') != True:
    #                         modifiers['readonly'].insert(0, "|")
    #                         modifiers['readonly'].append(['read_only_approval', '=', True])
    #
    #                     node.set("modifiers", json.dumps(modifiers))
    #
    #         res['arch'] = etree.tostring(doc, encoding='unicode')
    #     return res

    @api.depends('related_job')
    def _get_created_job(self):
        for rec in self:
            if len(rec.related_job) > 0:
                self.created_job_position = rec.related_job[0]
            else:
                self.created_job_position = False

    @api.depends('approver_ids.status')
    def _compute_user_status(self):
        for approval in self:
            approvers = approval.approver_ids.filtered(
                lambda
                    approver: approver.user_id == self.env.user or self.env.user in approver.group_id.users).filtered(
                lambda approver: approver.status != 'approved').sorted(lambda x: x.sequence)
            if len(approvers) > 0:
                approval.user_status = approvers[0].status
            else:
                approval.user_status = False

    def _get_user_group(self):
        user = self.env.user
        for rec in self:
            rec.read_only_user = False
            if user.has_group('security_rules.group_fusion_employee'):
                rec.read_only_user = True

    @api.depends('approver_ids')
    def _get_all_approved(self):
        result = True
        for rec in self:
            for appr in self.approver_ids:
                if appr.status != 'approved':
                    result = False
            rec.all_approved = result

    @api.depends('request_owner_id')
    def _get_direct_employee(self):
        for rec in self:
            employee = self.env['hr.employee'].search([('user_id', '=',
                                                        rec.request_owner_id.id)],
                                                      limit=1)
            rec.direct_employee_id = employee.id

    @api.onchange('request_owner_id')
    def onchange_project_id(self):
        current_employee = self.env['hr.employee'].search([('user_id', '=',
                                                            self.env.user.id)],
                                                          limit=1)
        if current_employee:
            children = current_employee.child_ids
            if not self.env.user.has_group('security_rules.group_hc_employee'):
                return {'domain': {
                    'related_employee_id': ['|', ('id', 'in', children.ids), ('id', '=', current_employee.id)],
                    'employee_transferred': [('id', 'in', children.ids)]
                }}

    @api.onchange('related_resign_request')
    def onchange_related_resign_request(self):
        for rec in self:
            rec.extend_till = rec.related_resign_request.end_date

    @api.onchange('related_employee_id')
    def onchange_employee(self):
        self = self.sudo()
        if self.related_employee_id and self.category_id.is_requisition_request == 'no':
            self.related_contract = self.related_employee_id.contract_id
            self.job_position = self.related_employee_id.job_id
            self.job_title = self.related_employee_id.contract_id.job_title
            self.grade = self.related_employee_id.contract_id.job_grade
            days = self.grade.notice_period if self.grade else 30
            self.resignation_date = fields.Date.today() + datetime.timedelta(
                days=days)
            self.group = self.related_employee_id.contract_id.group
            self.department = self.related_employee_id.contract_id.department
            self.section = self.related_employee_id.contract_id.section
            self.subsection = self.related_employee_id.contract_id.subsection
            self.related_oc = self.related_employee_id.department_id.id
            self.related_manager = self.related_employee_id.parent_id.id
            self.related_time_hired = self.related_employee_id.time_hired
            self.related_warnings = self.related_employee_id.notice_ids

    @api.onchange('employee_transferred')
    def onchange_employee_transferred(self):
        self = self.sudo()
        if self.employee_transferred and self.category_id.is_internal_transfer_request == 'yes':
            self.employee_fusion_id = self.employee_transferred.fusion_id

            self.employee_type_source = self.employee_transferred.contract_id.employment_status
            self.employee_type_destination = self.employee_transferred.contract_id.employment_status

            self.cost_center_source = self.employee_transferred.contract_id.cost_center.id
            self.cost_center_destination = self.employee_transferred.contract_id.cost_center.id

            self.job_title_source = self.employee_transferred.contract_id.job_title.id
            self.job_title_destination = self.employee_transferred.contract_id.job_title.id

            self.line_manager_source = self.employee_transferred.contract_id.manager_id.id
            self.line_manager_destination = self.employee_transferred.contract_id.manager_id.id

            self.group_source = self.employee_transferred.contract_id.group.id
            self.group_destination = self.employee_transferred.contract_id.group.id

            self.department_source = self.employee_transferred.contract_id.department.id
            self.department_destination = self.employee_transferred.contract_id.department.id

            self.section_source = self.employee_transferred.contract_id.section.id
            self.section_destination = self.employee_transferred.contract_id.section.id

            self.subsection_source = self.employee_transferred.contract_id.subsection.id
            self.subsection_destination = self.employee_transferred.contract_id.subsection.id

            self.job_grade_source = self.employee_transferred.contract_id.job_grade.id
            self.job_grade_destination = self.employee_transferred.contract_id.job_grade.id

            self.working_shift_source = self.employee_transferred.contract_id.resource_calendar_id.id
            self.working_shift_destination = self.employee_transferred.contract_id.resource_calendar_id.id

            self.approver_ids = False
            self._onchange_category_id()

            return {'domain': {
                'line_manager_destination': [('id', '!=', self.employee_transferred.id)]
            }}

    @api.onchange('line_manager_destination')
    def onchange_lm_destination(self):
        self = self.sudo()
        if self.line_manager_destination and self.category_id.is_internal_transfer_request == 'yes':
            self.group_destination = self.line_manager_destination.contract_id.group.id
            self.department_destination = self.line_manager_destination.contract_id.department.id
            self.section_destination = self.line_manager_destination.contract_id.section.id
            self.subsection_destination = self.line_manager_destination.contract_id.subsection.id

        self.approver_ids = False
        self._onchange_category_id()

    @api.model
    def create(self, vals):
        res = super(ApprovalRequest, self).create(vals)
        if res.is_termination_request == 'yes':

            # old_resignations = self.env['approval.request']

            res.related_contract = res.related_employee_id.contract_id
            res.job_position = res.related_employee_id.job_id
            res.job_title = res.related_employee_id.contract_id.job_title
            res.grade = res.related_employee_id.contract_id.job_grade
            days = res.grade.notice_period if res.grade else 30
            # res.resignation_date = fields.Date.today() + datetime.timedelta(
            #     days=days)
            res.group = res.related_employee_id.contract_id.group
            res.department = res.related_employee_id.contract_id.department
            res.section = res.related_employee_id.contract_id.section
            res.subsection = res.related_employee_id.contract_id.subsection
        elif res.is_requisition_request == 'yes' and self.env.user.has_group('security_rules.group_fusion_employee'):
            group = res.group
            department = res.department
            section = res.section
            subsection = res.subsection

            employee = res.direct_employee_id

            department_code = employee.department_id.type
            if department_code == 'BU':
                if group.id and group.id != employee.department_id.id:
                    raise ValidationError(
                        _("You must choose a Group related to the Employee's Group: " + employee.department_id.name))
            elif department_code == 'BD':
                if group.id and group.id != employee.department_id.parent_id.id:
                    raise ValidationError(_(
                        "You must choose a Group related to the Employee's Group: " + employee.department_id.parent_id.name))
                elif department.id and department.id != employee.department_id.id:
                    raise ValidationError(_(
                        "You must choose a Department related to the Employee's Department: " + employee.department_id.name))
            elif department_code == 'BS':
                if group.id and group.id != employee.department_id.parent_id.parent_id.id:
                    raise ValidationError(_(
                        "You must choose a Group related to the Employee's Group: " + employee.department_id.parent_id.parent_id.name))
                elif department.id and department.id != employee.department_id.parent_id.id:
                    raise ValidationError(_(
                        "You must choose a Department related to the Employee's Department: " + employee.department_id.parent_id.name))
                elif section.id and section.id != employee.department_id.id:
                    raise ValidationError(_(
                        "You must choose a Section related to the Employee's Section: " + employee.department_id.name))
            elif department_code == 'SS':
                if group.id and group.id != employee.department_id.parent_id.parent_id.parent_id.id:
                    raise ValidationError(_(
                        "You must choose a Group related to the Employee's Group: " + employee.department_id.parent_id.parent_id.parent_id.name))
                elif department.id and department.id != employee.department_id.parent_id.parent_id.id:
                    raise ValidationError(_(
                        "You must choose a Department related to the Employee's Department: " + employee.department_id.parent_id.parent_id.name))
                elif section.id and section.id != employee.department_id.parent_id.id:
                    raise ValidationError(_(
                        "You must choose a Section related to the Employee's Section: " + employee.department_id.parent_id.name))
                elif subsection.id and subsection.id != employee.department_id.id:
                    raise ValidationError(_(
                        "You must choose a Subsection related to the Employee's Subsection: " + employee.department_id.name))

        return res

    def write(self, vals):
        # self = self.sudo()
        res = super(ApprovalRequest, self).write(vals)
        if vals.get(
                'related_employee_id') and self.is_termination_request == 'yes':
            self.related_contract = self.related_employee_id.contract_id
            self.job_position = self.related_employee_id.job_id
            self.job_title = self.related_employee_id.contract_id.job_title
            self.grade = self.related_employee_id.contract_id.job_grade
            days = self.grade.notice_period if self.grade else 30
            # self.resignation_date = fields.Date.today() + datetime.timedelta(
            #     days=days)
            self.group = self.related_employee_id.contract_id.group
            self.department = self.related_employee_id.contract_id.department
            self.section = self.related_employee_id.contract_id.section
            self.subsection = self.related_employee_id.contract_id.subsection
        elif self.is_requisition_request == 'yes' and self.env.user.has_group('security_rules.group_fusion_employee'):
            if vals.get('group', '') != '' or vals.get('department', '') != '' or vals.get('section',
                                                                                           '') != '' or vals.get(
                'subsection', '') != '':
                group = self.group
                department = self.department
                section = self.section
                subsection = self.subsection

                employee = self.direct_employee_id

                department_code = employee.department_id.type

                if department_code == 'BU':
                    if group.id and group.id != employee.department_id.id:
                        raise ValidationError(
                            _(
                                "You must choose a Group related to the Employee's Group: " + employee.department_id.name))
                elif department_code == 'BD':
                    if group.id and group.id != employee.department_id.parent_id.id:
                        raise ValidationError(_(
                            "You must choose a Group related to the Employee's Group: " + employee.department_id.parent_id.name))
                    elif department.id and department.id != employee.department_id.id:
                        raise ValidationError(_(
                            "You must choose a Department related to the Employee's Department: " + employee.department_id.name))
                elif department_code == 'BS':
                    if group.id and group.id != employee.department_id.parent_id.parent_id.id:
                        raise ValidationError(_(
                            "You must choose a Group related to the Employee's Group: " + employee.department_id.parent_id.parent_id.name))
                    elif department.id and department.id != employee.department_id.parent_id.id:
                        raise ValidationError(_(
                            "You must choose a Department related to the Employee's Department: " + employee.department_id.parent_id.name))
                    elif section.id and section.id != employee.department_id.id:
                        raise ValidationError(_(
                            "You must choose a Section related to the Employee's Section: " + employee.department_id.name))
                elif department_code == 'SS':
                    if group.id and group.id != employee.department_id.parent_id.parent_id.parent_id.id:
                        raise ValidationError(_(
                            "You must choose a Group related to the Employee's Group: " + employee.department_id.parent_id.parent_id.parent_id.name))
                    elif department.id and department.id != employee.department_id.parent_id.parent_id.id:
                        raise ValidationError(_(
                            "You must choose a Department related to the Employee's Department: " + employee.department_id.parent_id.parent_id.name))
                    elif section.id and section.id != employee.department_id.parent_id.id:
                        raise ValidationError(_(
                            "You must choose a Section related to the Employee's Section: " + employee.department_id.parent_id.name))
                    elif subsection.id and subsection.id != employee.department_id.id:
                        raise ValidationError(_(
                            "You must choose a Subsection related to the Employee's Subsection: " + employee.department_id.name))
        return res

    @api.onchange('job_title', 'related_employee_id', 'employee_transferred')
    def compute_name_get(self):
        for request in self:
            if request.is_requisition_request == 'yes':
                if request.job_title:
                    request.name = request.category_id.name + " - " + request.job_title.name
                    continue
            elif request.is_termination_request == 'yes' or request.is_termination_extend_request == 'yes':
                if request.related_employee_id:
                    request.name = request.category_id.name + " - " + request.related_employee_id.name
                    continue
            elif request.is_internal_transfer_request == 'yes':
                if request.employee_transferred:
                    request.name = request.category_id.name + " - " + request.employee_transferred.name + " - " + request.employee_transferred.fusion_id
                    continue
            request.name = request.category_id.name

    def get_approvers(self, employee, array):
        if not employee.department_id.type or not employee.parent_id:  # or employee.department_id.type == 'BU' :
            return array
        else:
            array.append(employee)
            return array

    @api.onchange('category_id', 'request_owner_id')
    def _onchange_category_id(self):
        # Check if category have field is_employee_manager_approval
        if self.category_id.is_employee_manager_approval:
            approver_id_vals = []
            manager_user = self.env.user.employee_id.parent_id.user_id
            if manager_user and \
                    manager_user not in self.category_id.approver_ids.mapped('user_id'):
                last_user = self.approver_ids and self.approver_ids[-1]
                last_sequence = (last_user.sequence + 1)
                approver_id_vals.append(Command.create({
                    'user_id': manager_user.id,
                    'status': 'new',
                    'required': True,
                    'date_deadline_after': 0,
                    'sequence': last_sequence,
                }))
                self.approver_ids = approver_id_vals

        current_users = self.approver_ids.mapped('user_id')
        # new_users_unordered = self.category_id.user_ids
        new_approvals_ordered = self.category_id.approval_sequence.sorted(lambda x: x.sequence)
        approver_lines_date = []
        for approval in new_approvals_ordered:
            approver_lines_date.append((approval.user_id, approval.group_id, approval.approve_type, approval.date_deadline_after))
        # new_users = new_users_unordered.sorted(lambda x: x.sequence)
        dynamic_users = []
        last_sequence = 0
        lm_sequence = 0
        if self.category_id.is_internal_transfer_request == 'yes':
            source_dep = self.subsection_source if self.subsection_source.id else (
                self.section_source if self.section_source.id else (
                    self.department_source if self.department_source.id else (
                        self.department_source if self.department_source.id else False)))
            destination_dep = self.subsection_destination if self.subsection_destination.id else (
                self.section_destination if self.section_destination.id else (
                    self.department_destination if self.department_destination.id else (
                        self.department_destination if self.department_destination.id else False)))
            source_manager = source_dep.manager_id if source_dep else False
            destination_manager = destination_dep.manager_id if destination_dep else False

            if source_manager and source_manager.user_id:
                if source_manager.user_id.id not in current_users.ids:
                    dynamic_users.append(source_manager.user_id.id)
                    last_sequence += 10
                    self.approver_ids += self.env['approval.approver'].new({
                        'sequence': last_sequence,
                        'user_id': source_manager.user_id.id,
                        'approver_category': 'Source Head of Department',
                        'request_id': self.id,
                        'status': 'new',
                        'approver_type': 'dynamic'})
            if destination_manager and destination_manager.user_id:
                if destination_manager.user_id.id not in current_users.ids:
                    dynamic_users.append(destination_manager.user_id.id)
                    last_sequence += 10
                    self.approver_ids += self.env['approval.approver'].new({
                        'sequence': last_sequence,
                        'user_id': destination_manager.user_id.id,
                        'approver_category': 'Destination Head of Department',
                        'request_id': self.id,
                        'status': 'new',
                        'approver_type': 'dynamic'})

        elif self.category_id.manager_approval:
            employee = self.env['hr.employee'].search([('user_id', '=', self.request_owner_id.id)], limit=1)
            array_dynamic_employees = []
            array_dynamic_employees = self.get_approvers(employee.parent_id, array_dynamic_employees)
            for employee in array_dynamic_employees:
                if employee.department_id.type == 'SS':
                    if employee.user_id:
                        if employee.user_id.id not in current_users.ids:
                            dynamic_users.append(employee.user_id.id)
                            last_sequence += 10
                            lm_sequence += 1
                            self.approver_ids += self.env['approval.approver'].new({
                                'sequence': last_sequence,
                                'user_id': employee.user_id.id,
                                'approver_category': 'LM' + str(lm_sequence),
                                'request_id': self.id,
                                'status': 'new',
                                'approver_type': 'dynamic'})
                elif employee.department_id.type == 'BS':
                    if employee.user_id:
                        if employee.user_id.id not in current_users.ids:
                            dynamic_users.append(employee.user_id.id)
                            last_sequence += 10
                            lm_sequence += 1
                            self.approver_ids += self.env['approval.approver'].new({
                                'sequence': last_sequence,
                                'user_id': employee.user_id.id,
                                'approver_category': 'LM' + str(lm_sequence),
                                'request_id': self.id,
                                'status': 'new',
                                'approver_type': 'dynamic'})
                elif employee.department_id.type == 'BD':
                    if employee.user_id:
                        if employee.user_id.id not in current_users.ids:
                            dynamic_users.append(employee.user_id.id)
                            last_sequence += 10
                            lm_sequence += 1
                            self.approver_ids += self.env['approval.approver'].new({
                                'sequence': last_sequence,
                                'user_id': employee.user_id.id,
                                'approver_category': 'LM' + str(lm_sequence),
                                'request_id': self.id,
                                'status': 'new',
                                'approver_type': 'dynamic'})
        for approver_data in approver_lines_date:
            if approver_data[0].id not in current_users.ids:
                # if user.id not in dynamic_users:
                last_sequence += 10
                approver_category = self.category_id.approval_sequence.filtered(
                    lambda x: x.user_id.id == approver_data[0].id)[0].approver_category
                self.approver_ids += self.env['approval.approver'].new({
                    'sequence': last_sequence,
                    'user_id': approver_data[0].id,
                    'group_id': approver_data[1].id,
                    'approve_type': approver_data[2],
                    'date_deadline_after': approver_data[3],
                    'approver_category': approver_category,
                    'request_id': self.id,
                    'status': 'new',
                    'approver_type': 'static'})

    @api.depends('request_status', 'is_requisition_request')
    def _create_job(self):
        for rec in self:
            if rec.request_status == 'approved' and rec.is_requisition_request == 'yes':
                rec.can_create_job = True
            else:
                rec.can_create_job = False

    @api.depends('request_status', 'is_termination_request')
    def _create_resign(self):
        for rec in self:
            resign = rec.env['hr.resignation'].search([('related_approval', '=', rec.id)])
            if rec.request_status == 'approved' and rec.is_termination_request == 'yes' and not resign:
                rec.can_create_resign = True
            else:
                rec.can_create_resign = False

    @api.depends('request_status', 'is_termination_extend_request')
    def _extend_resign(self):
        for rec in self:
            resign = rec.env['hr.resignation'].search([('related_approval', '=', rec.id)])
            if rec.request_status == 'approved' and rec.is_termination_extend_request == 'yes' and not resign:
                rec.can_extend_resign = True
            else:
                rec.can_extend_resign = False

    @api.depends('request_status', 'is_internal_transfer_request')
    def _create_transfer(self):
        for rec in self:
            if rec.request_status == 'approved' and rec.is_internal_transfer_request == 'yes':
                rec.can_create_transfer = True
            else:
                rec.can_create_transfer = False

    @api.onchange('group')
    def _on_group_change(self):
        if self.group:
            self.department = False
            self.section = False
            self.subsection = False
            return {'domain': {
                'department': [('type', '=', 'BD'),
                               ('parent_id', 'child_of', self.group.id)],
                'section': [('type', '=', 'BS'),
                            ('parent_id', 'child_of',
                             self.group.id)],
                'subsection': [('type', '=', 'SS'),
                               ('parent_id', 'child_of', self.group.id)]}}
        else:
            return {'domain': {'department': [('type', '=', 'BD')],
                               'section': [('type', '=', 'BS')],
                               'subsection': [('type', '=', 'SS')]}}

    @api.onchange('department')
    def _on_department_change(self):
        if self.department:
            self.section = False
            self.subsection = False
            return {'domain': {
                'section': [('type', '=', 'BS'),
                            ('parent_id', 'child_of',
                             self.department.id)],
                'subsection': [('type', '=', 'SS'),
                               ('parent_id', 'child_of', self.department.id)]}}
        elif self.group:
            return self._on_group_change()
        else:
            return {'domain': {
                'section': [('type', '=', 'BS')],
                'subsection': [('type', '=', 'SS')]}}

    @api.onchange('section')
    def _on_section_change(self):
        if self.section:
            self.subsection = False
            return {'domain': {
                'subsection': [('type', '=', 'SS'),
                               ('parent_id', 'child_of', self.section.id)]}}
        elif self.department:
            return self._on_department_change()
        else:
            return {'domain': {
                'subsection': [('type', '=', 'SS')]}}

    @api.onchange('group_destination')
    def _on_group_destination_change(self):
        if self.group_destination:

            return {'domain': {
                'department_destination': [('type', '=', 'BD'),
                                           ('parent_id', 'child_of', self.group_destination.id)],
                'section_destination': [('type', '=', 'BS'),
                                        ('parent_id', 'child_of',
                                         self.group_destination.id)],
                'subsection_destination': [('type', '=', 'SS'),
                                           ('parent_id', 'child_of', self.group_destination.id)]}}
        else:
            return {'domain': {'department_destination': [('type', '=', 'BD')],
                               'section_destination': [('type', '=', 'BS')],
                               'subsection_destination': [('type', '=', 'SS')]}}

    @api.onchange('department_destination')
    def _on_department_destination_change(self):
        if self.department_destination:

            return {'domain': {
                'section_destination': [('type', '=', 'BS'),
                                        ('parent_id', 'child_of',
                                         self.department_destination.id)],
                'subsection_destination': [('type', '=', 'SS'),
                                           ('parent_id', 'child_of', self.department_destination.id)]}}
        elif self.group_destination:
            return self._on_group_destination_change()
        else:
            return {'domain': {
                'section_destination': [('type', '=', 'BS')],
                'subsection_destination': [('type', '=', 'SS')]}}

    @api.onchange('section_destination')
    def _on_section_destination_change(self):
        if self.section_destination:
            # if self.subsection_destination.parent_id.parent_id.id != self.section_destination.id:
            # self.subsection_destination = False
            return {'domain': {
                'subsection_destination': [('type', '=', 'SS'),
                                           ('parent_id', 'child_of', self.section_destination.id)]}}
        elif self.department_destination:
            return self._on_department_destination_change()
        else:
            return {'domain': {
                'subsection_destination': [('type', '=', 'SS')]}}

    def action_confirm(self):
        if len(self.approver_ids) < self.approval_minimum:
            raise UserError(
                _("You have to add at least %s approvers to confirm your request.") % self.approval_minimum)
        if self.requirer_document == 'required' and not self.attachment_number:
            raise UserError(_("You have to attach at least one document."))

        if self.category_id.is_termination_request == 'yes':
            employee = self.direct_employee_id
            old_resignations = self.env['approval.request'].search(
                [('category_id.is_termination_request', '=', 'yes'), ('direct_employee_id', '=', employee.id),
                 ('request_status', 'in', ('approved', 'pending', 'under_approval'))])

            if len(old_resignations) > 0:
                raise UserError(_("You already have one Resignation Submitted or Approved"))

        approvers = \
            self.mapped('approver_ids').sorted('sequence')[0]
        approvers._create_activity()
        template = self.env.ref('hr_approvals.template_email_approver')
        ctx = {}
        employee_name = self.env['hr.employee'].sudo().search([
            ('user_id', '=', self.create_uid.id)
        ]) if self.create_uid else False
        ctx['employee_name'] = employee_name.arabic_name if employee_name else False
        category_name = self.category_id
        ctx['category_name'] = category_name.with_context(lang='ar_001').name
        email_to_user = approvers[0].user_id if approvers[0].approve_type == 'user' else approvers[0].group_id.users
        if not email_to_user:
            raise ValidationError(f"{approvers[0].group_id.name} group has no users please, assign users to it")
        for email_user in email_to_user:
            employee_user = self.env['hr.employee'].search([('user_id', '=', email_user.id)])
            email_values = {'email_to': email_user.email}
            template.with_context(ctx).send_mail(self.id, email_values=email_values, force_send=False)
            message = f"تم تقديم طلب رقم ({self.name} - {self.category_id.name}) للموظف {employee_name.arabic_name if employee_name.arabic_name else '' } يرجى مراجعة الطلب في نظام موارد"
            employee_user.sudo().with_context(message=message).send_sms_message()
        approvers.write({'status': 'pending'})
        self.write({'date_confirmed': fields.Datetime.now()})
        for rec in self:
            if rec.category_id.approval_type == 'purchase':
                if rec.product_line_ids and \
                        not rec.product_line_ids.product_id.property_account_expense_id:
                    if self.env.context.get('lang') == 'ar_001':
                        raise ValidationError(_("يرجى ادخال حساب النفقات الى اى  منتج  تم إدخاله ...."))
                    else:
                        raise ValidationError(_("Please provide expense account to any product entered ....."))
                if rec.product_line_ids.product_id.property_account_expense_id:
                    related_budgetary_positions = self.env['account.budget.post'].search(
                        [('account_ids', 'in', rec.product_line_ids.product_id.property_account_expense_id[0].ids)])
                    if related_budgetary_positions:
                        related_budget_line = self.env['crossovered.budget.lines'].search(
                            [('general_budget_id', '=', related_budgetary_positions[0].id)])
                        if related_budget_line and rec.amount > related_budget_line[0].remaining_amount and \
                                rec.has_amount != 'no':
                            if self.env.context.get('lang') == 'ar_001':
                                raise ValidationError(_("لا يوجد ميزانية لهذا الصنف ...."))
                            else:
                                raise ValidationError(_("There is no budget for this product ....."))

    def action_approve(self, approver=None):
        if not isinstance(approver, models.BaseModel):
            approver = self.mapped('approver_ids').filtered(
                lambda approver: approver.user_id == self.env.user or self.env.user in approver.group_id.users
            ).filtered(
                lambda approver: approver.status != 'approved').sorted(lambda x: x.sequence)
        if len(approver) > 0:
            if self.category_id.has_eligible_rehire != 'no' and not approver.eligible_rehire_selection:
                raise ValidationError(_('Please set Eligible for Rehire before Approving'))
            approver[0].write(
                {'status': 'approved', 'approval_date': datetime.datetime.now(), 'action_user_id': self.env.uid})
        users = self.env.user
        if approver:
            users |= approver[0].group_id.users
        for user in users:
            self.sudo()._get_user_approval_activities(user=user).action_feedback()
        approvers = self.mapped('approver_ids').filtered(lambda approver: approver[0].status == 'new').sorted(
            'sequence')
        employee_name = self.env['hr.employee'].sudo().search([
            ('user_id', '=', self.create_uid.id)
        ]) if self.create_uid else False
        category_name = self.category_id
        if len(approvers) > 0:
            approvers[0].sudo()._create_activity()
            approvers[0].sudo().write({'status': 'pending'})
            ctx = {}
            ctx['employee_name'] = employee_name.arabic_name if employee_name else False
            ctx['category_name'] = category_name.with_context(lang='ar_001').name
            template = self.env.ref('hr_approvals.template_email_approver')

            email_to_user = approvers[0].user_id if approvers[0].approve_type == 'user' else approvers[0].group_id.users
            if not email_to_user:
                raise ValidationError(f"{approvers[0].group_id.name} group has no users, please assign users to it")
            for email_user in email_to_user:
                employee_user = self.env['hr.employee'].search([('user_id', '=', email_user.id)])
                email_values = {'email_to': email_user.email}
                template.with_context(ctx).send_mail(self.id, email_values=email_values, force_send=False)
                message = f"تم تقديم طلب رقم ({self.name} - {self.category_id.name}) للموظف {employee_name.arabic_name if employee_name.arabic_name else ''} يرجى مراجعة الطلب في نظام موارد"
                employee_user.sudo().with_context(message=message).send_sms_message()

        else:
            self.write({'approval_date': datetime.datetime.now()})

            employee_model = self.sudo().env['ir.model'].search([
                ('model', '=', 'hr.employee')
            ])
            if employee_model:
                ooredo_employee_conf = self.sudo().env['dynamic.integration.configuration'].sudo().search([
                    ('model_id', '=', employee_model.id)
                ])
                if ooredo_employee_conf:
                    message = "تم إعتماد طلبكم رقم : ( %s - %s)." % (
                        self.name, self.category_id.with_context(lang="ar_001").name)
                    employee_name.sudo().with_context(message=message).send_sms_message()

    def action_refuse(self, approver=None):
        if not isinstance(approver, models.BaseModel):
            approver = self.mapped('approver_ids').filtered(
                lambda approver: approver.user_id == self.env.user or self.env.user in approver.group_id.users
            ).filtered(
                lambda approver: approver.status != 'approved').sorted(lambda x: x.sequence)
        if len(approver) > 0:
            approver[0].write({'status': 'refused'})
        users = self.env.user
        if approver:
            users |= approver[0].group_id.users
        for user in users:
            self.sudo()._get_user_approval_activities(user=user).action_feedback()

    def action_withdraw(self, approver=None):
        if not isinstance(approver, models.BaseModel):
            approver = self.mapped('approver_ids').filtered(
                lambda approver: approver.user_id == self.env.user or self.env.user in approver.group_id.users
            )
        approver.write({'status': 'pending'})

    @api.constrains('approver_ids')
    def _check_approver_ids(self):
        for request in self:
            # make sure the approver_ids are unique per request
            # if len(request.approver_ids) != len(request.approver_ids.user_id) + len(request.approver_ids.group_id):
            #     raise UserError(
            #         _("You cannot assign the same approver Users Or Group multiple times on the same request."))
            pass

    @api.depends('approver_ids.status')
    def _compute_request_status(self):
        for request in self:
            status_lst = request.mapped('approver_ids.status')
            minimal_approver = request.approval_minimum if len(status_lst) >= request.approval_minimum else len(
                status_lst)
            if status_lst:
                if status_lst.count('cancel'):
                    status = 'cancel'
                elif status_lst.count('refused'):
                    status = 'refused'
                elif status_lst.count('new') and not status_lst.count('pending') and not status_lst.count('approved'):
                    status = 'new'
                elif 0 < status_lst.count('approved') < len(status_lst):
                    status = 'under_approval'
                elif status_lst.count('approved') == len(status_lst):
                    status = 'approved'
                else:
                    status = 'pending'
            else:
                status = 'new'
            request.request_status = status

    def _get_job_default_values(self):
        dict = {
            'default_group': self.group.id,
            'default_department_id': self.department.id,
            'default_section': self.section.id,
            'default_subsection': self.subsection.id,
            'default_related_requisition': self.id,
            'default_description': self.job_desc,
            'default_job_title': self.job_title.id,
            'default_cost_center': self.cost_center.id,
        }
        dict.update(self._context)
        return dict

    def create_job_position(self):
        return {
            'name': 'Job Position',
            'view_mode': 'form',
            'res_model': 'hr.job',
            'type': 'ir.actions.act_window',
            'context': self._get_job_default_values(),
        }

    def _get_resign_default_values(self):
        dict = {
            'default_related_employee': self.related_employee_id.id,
            'default_related_contract': self.related_contract.id,
            'default_related_approval': self.id,
            'default_start_date': self.create_date,
            'default_end_date': self.resignation_date
        }
        dict.update(self._context)
        return dict

    def create_resignation(self):
        return {
            'name': 'Resignation',
            'view_mode': 'form',
            'res_model': 'hr.resignation',
            'type': 'ir.actions.act_window',
            'context': self._get_resign_default_values(),
        }

    def extend_resignation(self):
        # if self.related_resign_request.state != 'extended':
        self.related_resign_request.set_extend()
        self.related_resign_request.end_date = self.extend_till
        self.related_resign_request.related_approval = self.id
        self._extend_resign()
        self.related_resign_request.related_contract.write(
            {'effective_end_date': self.related_resign_request.end_date})
        # res = self.env['hr.resignation'].create({
        #     'start_date': self.related_resign_request.start_date,
        #     'end_date': self.extend_till,
        #     'related_employee': self.related_resign_request.related_employee.id,
        #     'related_contract': self.related_resign_request.related_contract.id,
        #     'related_approval': self.id,
        #     'extended_from': self.related_resign_request.id,
        # })
        # self.related_resign_request.set_active()

    def open_create_transfer_wizard(self):
        default_event_type = self.env['sap.event.type'].search([('is_related_transfer', '=', True)], limit=1)
        return {
            'view_mode': 'form',
            'res_model': 'create.transfer.event',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_related_approval': self.id,
                'default_event_type_id': default_event_type.id if default_event_type else False,
            }
        }

    has_vacancy_type = fields.Selection(related="category_id.has_vacancy_type")
    has_job_title = fields.Selection(related="category_id.has_job_title")
    has_group = fields.Selection(related="category_id.has_group")
    has_department = fields.Selection(related="category_id.has_department")
    has_section = fields.Selection(related="category_id.has_section")
    has_subsection = fields.Selection(related="category_id.has_subsection")
    has_job_desc = fields.Selection(related="category_id.has_job_desc")
    has_replacement_employee_id = fields.Selection(related="category_id.has_replacement_employee_id")
    has_contract_type = fields.Selection(related="category_id.has_contract_type")
    has_requisition_type = fields.Selection(related="category_id.has_requisition_type")
    has_requisition_period_type = fields.Selection(related="category_id.has_requisition_period_type")
    has_starting_date = fields.Selection(related="category_id.has_starting_date")
    has_other_remarks = fields.Selection(related="category_id.has_other_remarks")
    # has_qty = fields.Selection(related="category_id.has_qty")
    has_related_employee_id = fields.Selection(related="category_id.has_related_employee_id")
    has_related_contract = fields.Selection(related="category_id.has_related_contract")
    has_grade = fields.Selection(related="category_id.has_grade")
    has_related_manager = fields.Selection(related="category_id.has_related_manager")
    has_related_oc = fields.Selection(related="category_id.has_related_oc")
    has_related_time_hired = fields.Selection(related="category_id.has_related_time_hired")
    has_related_warnings = fields.Selection(related="category_id.has_related_warnings")
    has_notice_period = fields.Selection(related="category_id.has_notice_period")
    has_job_position = fields.Selection(related="category_id.has_job_position")
    has_resignation_date = fields.Selection(related="category_id.has_resignation_date")
    is_requisition_request = fields.Selection(related="category_id.is_requisition_request")
    is_termination_request = fields.Selection(related="category_id.is_termination_request")
    is_termination_extend_request = fields.Selection(related="category_id.is_termination_extend_request")
    is_internal_transfer_request = fields.Selection(related="category_id.is_internal_transfer_request")
    has_cost_center = fields.Selection(related="category_id.has_cost_center")
    has_personal_phone_no = fields.Selection(related="category_id.has_personal_phone_no")
    has_personal_email = fields.Selection(related="category_id.has_personal_email")
    has_replacement_position = fields.Selection(related="category_id.has_replacement_position")
    has_resignation_reason = fields.Selection(related="category_id.has_resignation_reason")
    has_resignation_extension_reason = fields.Selection(related="category_id.has_resignation_extension_reason")
    has_eligible_rehire = fields.Selection(related="category_id.has_related_oc")
    has_eligible_rehire_comment = fields.Selection(related="category_id.has_related_oc")
    can_see_eligible = fields.Boolean(
        string='Can See Eligible',
        compute='_can_see_eligible', store=True)
    can_see_eligible_not_stored = fields.Boolean(
        string='Can See Eligible Not Stored',
        compute='_run_always')

    # internal transfer fields
    has_employee_transferred = fields.Selection(related="category_id.has_employee_transferred")

    has_employee_fusion_id = fields.Selection(related="category_id.has_employee_fusion_id")
    has_transfer_type = fields.Selection(related="category_id.has_transfer_type")
    has_transfer_reason = fields.Selection(related="category_id.has_transfer_reason")

    has_employee_type_source = fields.Selection(related="category_id.has_employee_type_source")
    has_employee_type_destination = fields.Selection(related="category_id.has_employee_type_destination")

    has_cost_center_source = fields.Selection(related="category_id.has_employee_type_source")
    has_cost_center_destination = fields.Selection(related="category_id.has_employee_type_destination")

    has_sap_source = fields.Selection(related="category_id.has_sap_source")
    has_sap_destination = fields.Selection(related="category_id.has_sap_destination")

    has_3dx_source = fields.Selection(related="category_id.has_3dx_source")
    has_3dx_destination = fields.Selection(related="category_id.has_3dx_destination")

    has_shared_folder_source = fields.Selection(related="category_id.has_shared_folder_source")
    has_shared_folder_destination = fields.Selection(related="category_id.has_shared_folder_destination")

    has_shared_folder_status_source = fields.Selection(related="category_id.has_shared_folder_status_source")
    has_shared_folder_status_destination = fields.Selection(related="category_id.has_shared_folder_status_destination")

    has_other_source = fields.Selection(related="category_id.has_other_source")
    has_other_destination = fields.Selection(related="category_id.has_other_destination")

    has_job_title_source = fields.Selection(related="category_id.has_job_title_source")
    has_job_title_destination = fields.Selection(related="category_id.has_job_title_destination")

    has_line_manager_source = fields.Selection(related="category_id.has_line_manager_source")
    has_line_manager_destination = fields.Selection(related="category_id.has_line_manager_destination")

    has_group_source = fields.Selection(related="category_id.has_group_source")
    has_group_destination = fields.Selection(related="category_id.has_group_destination")

    has_department_source = fields.Selection(related="category_id.has_department_source")
    has_department_destination = fields.Selection(related="category_id.has_department_destination")

    has_section_source = fields.Selection(related="category_id.has_section_source")
    has_section_destination = fields.Selection(related="category_id.has_section_destination")

    has_subsection_source = fields.Selection(related="category_id.has_subsection_source")
    has_subsection_destination = fields.Selection(related="category_id.has_subsection_destination")

    has_job_grade_source = fields.Selection(related="category_id.has_job_grade_source")
    has_job_grade_destination = fields.Selection(related="category_id.has_job_grade_destination")

    has_working_shift_source = fields.Selection(related="category_id.has_working_shift_source")
    has_working_shift_destination = fields.Selection(related="category_id.has_working_shift_destination")

    def _run_always(self):
        for rec in self:
            rec.can_see_eligible_not_stored = not rec.can_see_eligible_not_stored
            self._can_see_eligible()

    @api.depends('can_see_eligible_not_stored')
    def _can_see_eligible(self):
        self = self.sudo()
        for rec in self:
            approvers = rec.approver_ids
            equal = False
            for approver in approvers:
                if approver.user_id.id == self.env.uid or self.env.user in approver.group_id.users:
                    equal = True
                    break

            if equal or self.env.user.has_group('security_rules.group_hc_employee'):
                rec.can_see_eligible = True
            else:
                rec.can_see_eligible = False


class ApprovalRejectReason(models.TransientModel):
    _name = 'approval.reject.reason'
    _description = 'Approval Reject Reason'

    name = fields.Char('Rejection Reason', required=True)
    approval_id = fields.Many2one('approval.request')

    def on_done_action(self, approver=None):
        # approver = self.approval_id.mapped('approver_ids').filtered(
        #     lambda approver: approver.user_id == self.env.user or self.env.user in approver.group_id.users
        # ).filtered(
        #     lambda approver: approver.status != 'approved').sorted(lambda x: x.sequence)
        #
        # if len(approver) > 0:
        #     approver[0].update({'reject_reason': self.name, 'status': 'refused', 'action_user_id': self.env.uid})
        #     approver[0].request_id.approval_date = datetime.datetime.now()
        #
        #     msg = _('Request Rejected by ' + self.env.user.name + '. Rejection Reason: ' + self.name)
        #     self.approval_id.message_post(body=msg)
        if not isinstance(approver, models.BaseModel):
            approver = self.approval_id.mapped('approver_ids').filtered(
                lambda approver: approver.user_id == self.env.user or self.env.user in approver.group_id.users
            ).filtered(
                lambda approver: approver.status != 'approved').sorted(lambda x: x.sequence)
        if len(approver) > 0:
            approver[0].write({'status': 'refused'})
        users = self.env.user
        if approver:
            users |= approver[0].group_id.users
        for user in users:
            self.approval_id.sudo()._get_user_approval_activities(user=user).action_feedback()
        employee_model = self.sudo().env['ir.model'].search([
            ('model', '=', 'hr.employee')
        ])
        employee_name = self.env['hr.employee'].sudo().search([
            ('user_id', '=', self.approval_id.create_uid.id)
        ]) if self.create_uid else False
        if employee_model:
            ooredo_employee_conf = self.sudo().env['dynamic.integration.configuration'].sudo().search([
                ('model_id', '=', employee_model.id)
            ])
            if ooredo_employee_conf:
                message = "تم رفض طلبكم رقم : ( %s - %s)." % (
                    self.approval_id.name, self.approval_id.category_id.with_context(lang="ar_001").name)
                employee_name.sudo().with_context(message=message).send_sms_message()

    def static_refusal(self, approver_list):
        self.approval_id.update({'request_status': 'pending'})
        approver_list[:1].update({'status': 'pending'})
        for app in approver_list[1:]:
            app.update({'status': 'new'})

    def dynamic_refusal(self):
        self.approval_id.update({'request_status': 'new'})
        for app in self.approval_id.approver_ids:
            app.update({
                'status': 'new'
            })


class ApprovalEligible(models.TransientModel):
    _name = 'approval.eligible'
    _description = 'Approval Eligible'

    name = fields.Boolean(
        string='Eligible for Rehire',
        required=False)

    eligible_rehire_comment = fields.Char(
        string='Comment',
        required=False)
    approval_id = fields.Many2one('approval.request')
    eligible_rehire = fields.Selection(
        string='Eligible for Rehire',
        selection=[('yes', 'Yes'),
                   ('no', 'No'), ])
    replacement_position = fields.Selection(
        string='Replacement of the Position',
        selection=[('yes', 'Yes'),
                   ('no', 'No'), ])

    def on_done_action(self):
        self = self.sudo()
        approver = self.approval_id.mapped('approver_ids').filtered(
            lambda approver: approver.user_id == self.env.user or self.env.user in approver.group_id.users
        ).sorted(lambda x: x.sequence)

        if len(approver) > 0:
            approver[0].update(
                {'eligible_rehire_selection': self.eligible_rehire, 'replacement_position': self.replacement_position,
                 'eligible_rehire_comment': self.eligible_rehire_comment})

            # msg = _('Request Rejected by ' + approver[0].user_id.name + '. Rejection Reason: ' + self.name)
            # self.approval_id.message_post(body=msg)


class ApprovalApprover(models.Model):
    _inherit = 'approval.approver'
    _order = 'sequence'

    approve_type = fields.Selection(string="Type", selection=[('user', 'User'), ('group', 'Group')], required=True,
                                    default='user')
    user_id = fields.Many2one(required=False)
    action_user_id = fields.Many2one(comodel_name="res.users", string="By",
                                     help="Store id of user who accept or reject the request")
    group_id = fields.Many2one(comodel_name="res.groups", string="Group")
    sequence = fields.Integer('Sequence', default=1)
    signature = fields.Char("Signature")
    approver_category = fields.Char(
        string='Approver Category',
        required=False)
    approval_date = fields.Datetime(
        string='Approval Date',
        required=False, readonly=True)

    eligible_rehire = fields.Boolean(
        string='Eligible for Rehire',
        required=False)

    eligible_rehire_comment = fields.Char(
        string='Comment',
        required=False)
    eligible_rehire_selection = fields.Selection(
        string='Eligible for Rehire',
        selection=[('yes', 'Yes'),
                   ('no', 'No'), ])
    replacement_position = fields.Selection(
        string='Replacement of the Position',
        selection=[('yes', 'Yes'),
                   ('no', 'No'), ])

    is_termination_req = fields.Selection(related='request_id.category_id.is_termination_request')

    has_eligible_rehire = fields.Selection(related="request_id.category_id.has_related_oc")
    has_eligible_rehire_comment = fields.Selection(related="request_id.category_id.has_related_oc")

    reject_reason = fields.Char('Rejection Reason')
    approver_type = fields.Selection([('static', 'Static Approver'), ('dynamic', 'Dynamic Approver')])
    date_deadline_after = fields.Integer(string="Deadline After (days)")
    _sql_constraints = [
        ('_unique_approver', 'unique (id)', "Same Approvers for the same Approval is not allowed"),
    ]

    @api.onchange('user_id')
    def _onchange_approver_ids(self):
        pass

    def unlink(self):
        activity = self.env.ref('approvals.mail_activity_data_approval').id
        activities = self._get_user_approval_activities(user=self.user_id | self.group_id.users,
                                                        res_ids=self.request_id.ids, activity_type_id=activity)
        activities.unlink()

        res = super(ApprovalApprover, self).unlink()
        return res

    def _get_user_approval_activities(self, user, res_ids, activity_type_id):
        domain = [
            ('res_model', '=', 'approval.request'),
            ('res_id', 'in', res_ids),
            ('activity_type_id', '=', activity_type_id),
            ('user_id', 'in', user.ids)
        ]
        activities = self.env['mail.activity'].sudo().search(domain)
        return activities

    @api.model
    def create(self, vals):
        res = super(ApprovalApprover, self).create(vals)
        if len(res.request_id.approver_ids.filtered(
                lambda approver: approver.status == 'pending')) > 1:
            raise UserError(_("You Can not add Multiple approve with 'To Approve' Status."))
        next_approvers = self.env['approval.request'].browse(vals['request_id']).approver_ids
        # if not next_approvers.filtered(lambda approver: approver.status == 'pending'):
        next_approver = next_approvers.filtered(lambda approver: approver.status == 'pending').sorted(
            'sequence')
        if next_approver:
            next_approver[0]._create_activity()
            # next_approver[0].status = 'pending'
        return res

    @api.onchange('status')
    def onchange_user_status(self):
        for rec in self:
            request = rec.request_id
            approvers_sequences = request.approver_ids.filtered(lambda x: not str(x.id).startswith('<NewId 0x')).mapped(
                'sequence')
            diff = list(
                set([10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200]) - set(
                    approvers_sequences))
            diff.sort()
            next_seq = diff[0]
            rec.sequence = next_seq if next_seq else 1

    @api.depends('request_id.request_owner_id', 'request_id.approver_ids.user_id', 'request_id.approver_ids.group_id')
    def _compute_existing_request_user_ids(self):
        for approver in self:
            approver.existing_request_user_ids = \
                self.mapped('request_id.approver_ids.user_id')._origin \
                | self.mapped('request_id.approver_ids.group_id.users')._origin \
                | self.request_id.request_owner_id._origin

    def _create_activity(self):
        for approver in self:
            employee = self.env['hr.employee'].sudo().search([
                ('user_id', '=', approver.user_id.id)]) if approver.user_id else False
            date_deadline = False
            if employee:
                contract = employee.active_contract if employee.active_contract else False
                if contract:
                    date_deadline = fields.Date.today()
                    for day in range(int(approver.date_deadline_after)):
                        date = date_deadline + relativedelta(days=1)
                        weekend = str(date.weekday()) not in set(
                            contract.resource_calendar_id.attendance_ids.mapped('dayofweek'))

                        public_holiday = contract.resource_calendar_id.global_leave_ids.filtered(
                            lambda x: x.date_from.date() <= date <= x.date_to.date())

                        while weekend or public_holiday:
                            date = date + relativedelta(days=1)
                            weekend = str(date.weekday()) not in set(
                                contract.resource_calendar_id.attendance_ids.mapped('dayofweek'))
                            public_holiday = contract.resource_calendar_id.global_leave_ids.filtered(
                                lambda x: x.date_from.date() <= date <= x.date_to.date())

                        if not weekend and not public_holiday:
                            date_deadline = date
            if not date_deadline:
                date_deadline = fields.Date.today() + relativedelta(days=int(approver.date_deadline_after))
            users = approver.group_id.users | approver.user_id
            for user in users:
                approver.request_id.activity_schedule(
                    'approvals.mail_activity_data_approval',
                    date_deadline=date_deadline,
                    user_id=user.id)



class Job(models.Model):
    _inherit = "hr.job"
    _description = "Job Position"

    related_requisition = fields.Many2one('approval.request', string='Related Requisition')
    requisition_job_title = fields.Many2one(related="related_requisition.job_title")
    vacancy_type = fields.Selection(related="related_requisition.vacancy_type")
    contract_type = fields.Selection(related="related_requisition.contract_type")
    requisition_type = fields.Selection(related="related_requisition.requisition_type")
    replacement_employee_id = fields.Many2one(related="related_requisition.replacement_employee_id")


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    def activity_format(self):
        if 'ebs.crm.service.process' in self.mapped('res_model') and self.mapped('res_id') and len(
                self.mapped('res_id')) == 1:
            service_order_id = self.env['ebs.crm.service.process'].browse(self.mapped('res_id'))
            workflow_line_ids = service_order_id.proposal_workflow_line_ids
            if workflow_line_ids:
                self += workflow_line_ids.mapped('activity_ids')
        activities = self.read()
        mail_template_ids = set(
            [template_id for activity in activities for template_id in activity["mail_template_ids"]])
        mail_template_info = self.env["mail.template"].browse(mail_template_ids).read(['id', 'name'])
        mail_template_dict = dict([(mail_template['id'], mail_template) for mail_template in mail_template_info])
        for activity in activities:
            activity['mail_template_ids'] = [mail_template_dict[mail_template_id] for mail_template_id in
                                             activity['mail_template_ids']]
        # return activities

        result = activities
        activity_type_approval_id = self.env.ref('approvals.mail_activity_data_approval').id
        for activity in result:
            if activity['activity_type_id'][0] == activity_type_approval_id and \
                    activity['res_model'] == 'approval.request':
                request = self.env['approval.request'].browse(activity['res_id'])
                approver = request.approver_ids.filtered(
                    lambda approver: activity['user_id'][0] == approver.user_id.id or \
                                     activity['user_id'][0] in approver.group_id.users.ids)
                if len(approver) > 0:
                    activity['approver_id'] = approver[0].id
                    activity['approver_status'] = approver[0].status
        return result
