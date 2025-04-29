# -*- coding: utf-8 -*-
import json
from odoo import models, fields, api, _
from datetime import date, timedelta
from odoo.exceptions import AccessError, UserError, ValidationError

GCC_COUNTRIES_CODES = ['BH', 'OM', 'AE', 'KW', 'SA']


class HREmployeeCustom(models.Model):
    _inherit = 'hr.employee'

    pin = fields.Char(string="PIN", groups="base.group_user", copy=False,
                      help="PIN used to Check In/Out in Kiosk Mode (if enabled in Configuration).")
    appraisal_date = fields.Date(string='Last Appraisal date', groups="base.group_user",
                                 help="The date of the next appraisal is computed by the appraisal plan's dates (last appraisal + periodicity).")
    appraisal_date_related = fields.Date(related="appraisal_date", groups="base.group_user",
                                         string="Last Appraisal Date", help="Used to configure the last appraisal date",
                                         readonly=False)
    # appraisal_by_manager = fields.Boolean(string='Managers', groups="base.group_user",
    #                                       default=lambda self: self.env.user.company_id.appraisal_by_manager)
    appraisal_manager_ids = fields.Many2many('hr.employee', 'emp_appraisal_manager_rel', 'hr_appraisal_id',
                                             groups="base.group_user",
                                             domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    # appraisal_by_colleagues = fields.Boolean(string='Colleagues', groups="base.group_user",
    #                                          default=lambda self: self.env.user.company_id.appraisal_by_colleagues)
    appraisal_colleagues_ids = fields.Many2many('hr.employee', 'emp_appraisal_colleagues_rel', 'hr_appraisal_id',
                                                groups="base.group_user",
                                                domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    # appraisal_self = fields.Boolean(string='Employee', groups="base.group_user",
    #                                 default=lambda self: self.env.user.company_id.appraisal_by_employee)
    # appraisal_by_collaborators = fields.Boolean(string='Collaborators', groups="base.group_user",
    #                                             default=lambda
    #                                                 self: self.env.user.company_id.appraisal_by_collaborators)
    appraisal_collaborators_ids = fields.Many2many('hr.employee', 'emp_appraisal_subordinates_rel', 'hr_appraisal_id',
                                                   groups="base.group_user",
                                                   domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    # TODO remove the useless field in master
    periodic_appraisal_created = fields.Boolean(string='Periodic Appraisal has been created', groups="base.group_user",
                                                default=False)  # Flag for the cron
    parent_user_id = fields.Many2one(related='parent_id.user_id', string="Parent User", groups="base.group_user")
    last_duration_reminder_send = fields.Integer(string='Duration after last appraisal when we send last reminder mail',
                                                 groups="base.group_user", default=0)

    employee_name_in_arabic = fields.Char("Employee Name in Arabic")
    certificate_ids = fields.One2many("employee.certificate", "employee_id", string='Certificate')
    secondment_permit_check = fields.Boolean("Secondment Permit")
    work_permit_check = fields.Boolean("Work Permit")
    wassef_religion = fields.Selection([
        ('muslim', 'Muslim'),
        ('christian', 'Christian'),
        ('hindu', 'Hindu'),
        ('other', 'Other')])
    insurance_details = fields.Char("Insurance Details")

    job_name_en = fields.Char(related="job_id.name",
                              groups="base.group_user", store=True)

    job_name_arabic = fields.Char(related="job_id.job_arabic_name", groups="base.group_user")
    qid_job = fields.Char(string="QID Job", groups="base.group_user")

    profession_id = fields.Many2one('profession.profession', string="Profession")

    permanent_staff_employee = fields.Many2one(comodel_name="permanent.employee.pay.scale",
                                               string="Pay Scale",
                                               required=False)
    permanent_staff_employee_domain = fields.Char(
        compute="_compute_permanent_staff_employee_domain",
        readonly=True
    )
    wassef_employee_type = fields.Selection(string="Employment Category", default="perm_in_house", required=True,
                                            selection=[('temp', 'Temporary Employee'),
                                                       ('perm_in_house', 'Permanent In house'),
                                                       ('perm_staff', 'Permanent Staff')], )

    emp_allocation_type = fields.Selection([
        ('accrual', 'Accrual'),
        ('regular', 'Regular')
    ], default='accrual', string='Allocation Type')

    is_married = fields.Boolean(string="Married ?", compute="_check_is_married", default=False)
    is_qatari = fields.Boolean(string="Qatari ?", compute="_check_is_qatari", default=False)
    is_gcc_country = fields.Boolean(string="GCC ?", compute="_check_is_gcc", default=False)
    is_classified = fields.Boolean(string="Classified", default=False)
    is_confidential = fields.Boolean(string="Confidential ?", default=False)
    line_manager_id = fields.Many2one('hr.employee', string='Line 2 Manager',
                                      domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    directorate = fields.Many2one(comodel_name="hr.department", related='department_id.directorate')
    contract_status = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married')
    ], string="Contract Status", default='single', groups="base.group_user")

    mother_nationality = fields.Selection([
        ('qatari', 'Qatari'),
        ('non_qatari', 'non Qatari')],
        string="Mother Nationality", copy=False,
    )

    termination_date = fields.Datetime('Termination Date')
    reason = fields.Char()
    event_ids = fields.One2many('employee.event', 'id', compute="get_event_ids")
    effective_date = fields.Date()
    resource_calendar_domain = fields.Char("Resource Calendar Domain", compute="_compute_resource_calendar")
    pension_basic = fields.Float(string="Pension Basic", default=0.0)
    pension_social = fields.Float(string="Pension Social", default=0.0)
    pension_accommodation = fields.Float(string="Pension Accommodation", default=0.0)

    def get_event_ids(self):
        for rec in self:
            employee_event_ids = self.env['employee.event'].sudo().search([('employee_id', '=', rec.id)])
            rec.event_ids = [(6, 0, employee_event_ids.ids)]

    @api.model
    def action_write_effective_date(self, employee_id, effective_date):
        if date and employee_id:
            self.sudo().browse(int(employee_id)).sudo().update({'effective_date': effective_date})
            return True

    def write(self, vals):
        fields_list = ['registration_number', 'name', 'main_project', 'marital', 'department_id', 'sponsorship_type',
                       'sponsor', 'payroll_group', 'permanent_staff_employee', 'contract_status', 'country_id',
                       'job_id', 'gender', 'parent_id', 'line_manager_id', 'registration_number_previous',
                       'name_previous', 'main_project_previous', 'marital', 'department_id', 'sponsorship_type',
                       'sponsor_previous', 'payroll_group_previous', 'permanent_staff_employee_previous',
                       'contract_status_previous', 'country_id_previous', 'job_id_previous', 'gender_previous',
                       'parent_id_previous', 'line_manager_id_previous']
        # if not self.effective_date:
        #     self.effective_date = date.today()
        # if change manager of department give singleton error
        # so loop on self
        for record in self:
            if not record.env.context.get('from_project_transfer') and \
                    not vals.get(
                        'effective_date') and record.effective_date and 'is_created_cron' not in record._context:
                applied_fields = list(set(fields_list).intersection(vals.keys()))
                if len(applied_fields) > 0:
                    final_vals = {}
                    temp_vals = vals
                    for key, value in list(temp_vals.items()):
                        if key not in fields_list:
                            final_vals[key] = vals[key]
                        is_one2many = isinstance(record._fields[key], (fields.One2many))
                        if is_one2many:
                            final_vals[key] = vals[key]
                            del vals[key]
                        vals[key + '_previous'] = getattr(record, key, None)
                    record.with_context(
                        updated_from_promotion=record._context.get('updated_from_promotion')).create_employee_event(
                        record.effective_date, vals)
                    if final_vals:
                        res = super(HREmployeeCustom, self).write(final_vals)
                        return res
                    return False
                else:
                    res = super(HREmployeeCustom, self).write(vals)
                    return res
            else:
                res = super(HREmployeeCustom, self).write(vals)
                return res

    def create_employee_event(self, effective_date, vals):
        event_obj = self.env['employee.event']
        data = {}
        final_data = {}
        ctx = {}
        fields_list = ['registration_number', 'name', 'main_project', 'marital', 'department_id', 'sponsorship_type',
                       'sponsor', 'payroll_group', 'permanent_staff_employee', 'contract_status', 'country_id',
                       'job_id', 'gender', 'parent_id', 'line_manager_id']
        previous_vals = ['registration_number_previous',
                         'name_previous', 'main_project_previous', 'marital', 'department_id', 'sponsorship_type',
                         'sponsor_previous', 'payroll_group_previous', 'permanent_staff_employee_previous',
                         'contract_status_previous', 'country_id_previous', 'job_id_previous', 'gender_previous',
                         'parent_id_previous', 'line_manager_id_previous']
        if vals:
            for key, value in vals.items():
                if key in fields_list or key in previous_vals:
                    field = self.env['ir.model.fields'].sudo().search(
                        [('model', '=', 'employee.event'), ('name', '=', key)])
                    if field.name and field.name not in previous_vals:
                        data[field.name] = value
                        if hasattr(self, key):
                            if field.ttype == 'many2one' and field.relation:
                                name = self.env[field.relation].sudo().browse(value).name_get()
                                old_value = getattr(self, key) if getattr(self, key) else ''
                                values = name[0][1] if name else ''
                                final_data[field.field_description] = [
                                    old_value.sudo().name_get()[0][1] or '' if old_value else '',
                                    values]
                            else:
                                values = value
                                final_data[field.field_description] = [getattr(self, key) if getattr(self, key) else '',
                                                                       values]
                        else:
                            final_data[field.field_description] = ['', value]
                    if field.name:
                        data[field.name] = value
        if data:
            res = event_obj.sudo().create({
                'employee_id': self.id,
                'event_type': 'update_employee',
                'effective_date': effective_date,
            })
            res.onchange_employee_id()
            res.sudo().write(data)
            if self._context.get('updated_from_promotion'):
                res.sudo().write({'state': 'approve'})
                res.sudo()._update_employee_event()
            template = self.env.ref('ebs_hr_custom.email_template_for_event')
            ctx.update({'final_data': final_data})
            template.with_context(ctx).send_mail(res.id, force_send=False)

    @api.model
    def send_notification_of_completion_of_trial_period(self):
        employees = self.sudo().search([('probation_date', '!=', False)])
        today = date.today()
        for employee in employees:
            two_weeks_before_probation_date = today + timedelta(weeks=2)
            template = self.env.ref('ebs_hr_custom.mail_template_of_notify_completion_of_trial_period',
                                    raise_if_not_found=False)
            if employee.probation_date == two_weeks_before_probation_date and template:
                template.sudo().with_context(
                    email_to=employee.parent_id.work_email,
                    email_from=self.env.user.email).send_mail(employee.id,
                                                              force_send=True)

    @api.model
    def create(self, vals):
        rec = super(HREmployeeCustom, self).create(vals)
        template = self.env.ref('ebs_hr_custom.mail_template_of_added_new_employee_in_system',
                                raise_if_not_found=False)
        users = []
        if template:
            if rec.parent_id and rec.parent_id.user_id:
                users += rec.parent_id.user_id
            if rec.department_id and rec.department_id.manager_id and rec.department_id.manager_id.user_id:
                users += rec.department_id.manager_id.user_id
            if rec.directorate and rec.directorate.manager_id and rec.directorate.manager_id.user_id:
                users += rec.directorate.manager_id.user_id
            users += self.env.ref('hr.group_hr_manager').sudo().users
            users += self.env.ref('hr.group_hr_user').sudo().users
            users += self.env.ref('base.group_system').sudo().users
            users += self.env.ref('ebs_hr_custom.group_it_department').sudo().users
            users += self.env.ref('ebs_hr_custom.group_gs_department').sudo().users
            users += self.env.ref('ebs_hr_custom.group_hse_department').sudo().users
            partner_to = [str(user.partner_id.id) for user in users if users]
            # partner_to = [user.partner_id.id for user in users if users]
            if partner_to:
                template.sudo().with_context(
                    partner_to=','.join(partner_to)).send_mail(rec.id, force_send=True)
        return rec

    @api.model
    def default_get(self, fields):
        res = super(HREmployeeCustom, self).default_get(fields)
        if res.get('wassef_employee_type') and res.get('wassef_employee_type') == 'perm_staff':
            calender_id = self.env['resource.calendar'].sudo().search([('default_work_calendar', '=', 'staff')],
                                                                      limit=1)
            res.update({'resource_calendar_id': calender_id.id})
        elif res.get('wassef_employee_type') and res.get('wassef_employee_type') == 'perm_in_house':
            calender_id = self.env['resource.calendar'].sudo().search([('default_work_calendar', '=', 'in_house')],
                                                                      limit=1)
            res.update({'resource_calendar_id': calender_id.id})
        elif res.get('wassef_employee_type') and res.get('wassef_employee_type') == 'temp':
            calender_id = self.env['resource.calendar'].sudo().search([('default_work_calendar', '=', 'temp')],
                                                                      limit=1)
            res.update({'resource_calendar_id': calender_id.id})

        return res

    @api.onchange('wassef_employee_type')
    def onchange_employee_id(self):
        for rec in self:
            if rec.wassef_employee_type and rec.wassef_employee_type == 'perm_staff':
                calender_id = self.env['resource.calendar'].sudo().search([('default_work_calendar', '=', 'staff')],
                                                                          limit=1)
                rec.resource_calendar_id = calender_id.id
            elif rec.wassef_employee_type and rec.wassef_employee_type == 'perm_in_house':
                calender_id = self.env['resource.calendar'].sudo().search([('default_work_calendar', '=', 'in_house')],
                                                                          limit=1)
                rec.resource_calendar_id = calender_id.id
            elif rec.wassef_employee_type and rec.wassef_employee_type == 'temp':
                calender_id = self.env['resource.calendar'].sudo().search([('default_work_calendar', '=', 'temp')],
                                                                          limit=1)
                rec.resource_calendar_id = calender_id.id

    @api.onchange('department_id')
    def _onchange_department(self):
        """Override base function to add a custom logic based on wassef requirements."""
        if self.unit != 'operation':
            if self.department_id and self.department_id.manager_id:
                self.parent_id = self.department_id.manager_id
            if self.department_id and self.department_id.line_manager_id:
                self.line_manager_id = self.department_id.line_manager_id

    @api.depends('wassef_employee_type')
    def _compute_resource_calendar(self):
        for emp in self:
            if emp.wassef_employee_type == 'perm_in_house':
                emp.resource_calendar_domain = json.dumps(
                    [('default_work_calendar', '=', 'in_house')]
                )
            elif emp.wassef_employee_type == 'perm_staff':
                emp.resource_calendar_domain = json.dumps(
                    [('default_work_calendar', '=', 'staff')]
                )
            elif emp.wassef_employee_type == 'temp':
                emp.resource_calendar_domain = json.dumps(
                    [('default_work_calendar', '=', 'temp')]
                )
            else:
                emp.resource_calendar_domain = json.dumps(
                    [('default_work_calendar', '=', False)]
                )

    @api.depends('contract_status')
    def _check_is_married(self):
        for rec in self:
            if rec.contract_status == "married":
                rec.is_married = True
            else:
                rec.is_married = False

    @api.depends('country_id')
    def _check_is_gcc(self):
        for rec in self:
            if rec.country_id.code in GCC_COUNTRIES_CODES:
                rec.is_gcc_country = True
            else:
                rec.is_gcc_country = False

    @api.depends('country_id')
    def _check_is_qatari(self):
        for rec in self:
            if rec.country_id.code == "QA":
                rec.is_qatari = True
            else:
                rec.is_qatari = False

    @api.depends('is_married', 'is_qatari', 'country_id', 'gender', 'is_gcc_country')
    def _compute_permanent_staff_employee_domain(self):
        for rec in self:
            if rec.gender == "male":
                rec.permanent_staff_employee_domain = json.dumps(
                    [('is_married', '=', rec.is_married), ('is_qatari', '=', rec.is_qatari),
                     ('is_gcc_country', '=', rec.is_gcc_country), ('gender', '=', 'male')]
                )
            elif rec.gender == 'female':
                rec.permanent_staff_employee_domain = json.dumps(
                    [('is_married', '=', rec.is_married), ('is_qatari', '=', rec.is_qatari),
                     ('is_gcc_country', '=', rec.is_gcc_country), ('gender', '=', 'female')]
                )
            else:
                rec.permanent_staff_employee_domain = json.dumps(
                    [('is_married', '=', rec.is_married), ('is_qatari', '=', rec.is_qatari),
                     ('is_gcc_country', '=', rec.is_gcc_country)]
                )

    # @api.depends('project_id')
    # def _compute_employee_main_project_domain(self):
    #     for rec in self:
    #         rec.main_project = False
    #         projects = []
    #         for proj in rec.project_id:
    #             projects.append(proj.project_id.id)
    #
    #         rec.main_project_domain = json.dumps([('id', 'in', projects)])

    @api.onchange('is_married', 'is_qatari', 'country_id', 'gender', 'is_gcc_country')
    def check_employee_permanent_staff(self):
        for rec in self:
            if rec.permanent_staff_employee:
                rec.permanent_staff_employee = None

    @api.model
    def _change_managers_based_department(self):
        employees = self.search([
            ('unit', '!=', 'operation')
        ])
        print("Employees ", employees)
        print("Employees ", len(employees))
        for emp in employees:
            emp._onchange_department()

    @api.model
    def _document_type_visa_domain(self):
        return [
            ('document_type.id', '=',
             self.env.ref('ebs_capstone_hr.hr_document_type_Visa').id)
        ]

    @api.model
    def _document_type_passport_domain(self):
        return [
            ('document_type.id', '=',
             self.env.ref('ebs_capstone_hr.hr_document_type_passport').id)
        ]

    @api.model
    def _document_type_qid_domain(self):
        return [
            ('document_type.id', '=',
             self.env.ref('ebs_capstone_hr.hr_document_type_qid').id)
        ]

    @api.model
    def _document_type_healthcard_domain(self):
        return [
            ('document_type.id', '=',
             self.env.ref('ebs_capstone_hr.hr_document_type_healthcard').id)
        ]

    @api.depends("qid_doc_number", "depend_qid")
    def _get_qid_number(self):
        for rec in self:
            qid_num = self.env['ebs.hr.document'].search([
                ('state', '=', 'active'),
                ('employee_id', '=', rec.id),
                ('document_type.id', '=',
                 rec.env.ref('ebs_capstone_hr.hr_document_type_qid').id)
            ],
                order='create_date desc', limit=1)
        self.qid_doc_number = qid_num.name

    @api.depends("passport_doc_number", "depend_passport")
    def _get_passport_number(self):
        for rec in self:
            passport_num = self.env['ebs.hr.document'].search([
                ('state', '=', 'active'),
                ('employee_id', '=', rec.id),
                ('document_type.id', '=', rec.env.ref('ebs_capstone_hr.hr_document_type_passport').id)],
                order='create_date desc', limit=1)
        self.passport_doc_number = passport_num.name

    @api.depends("visa_doc_number", "depend_visa")
    def _get_visa_number(self):
        for rec in self:
            visa_num = self.env['ebs.hr.document'].search([
                ('state', '=', 'active'),
                ('employee_id', '=', rec.id),
                ('document_type.id', '=', rec.env.ref('ebs_capstone_hr.hr_document_type_Visa').id)],
                order='create_date desc', limit=1)
        self.visa_doc_number = visa_num.name

    @api.constrains('work_email')
    def _check_email_domain(self):
        for rec in self:
            domains = rec.company_id.company_domain.mapped('name')
            if rec.work_email:
                email = rec.work_email.split('@')
                if len(email) > 1:
                    work_email_domain = email[1]
                    if work_email_domain not in domains:
                        raise ValidationError(_("The Email's domain is not correct."))
                else:
                    raise ValidationError(_("The Email is not correct."))

    def move_to_confirmed(self):
        self.employee_states = 'confirmed'

    def set_to_draft(self):
        self.employee_states = 'draft'

    employee_number = fields.Integer(
        string='Employee Number')

    age = fields.Integer(
        string='Age',
        compute='_compute_age')

    country = fields.Many2one(comodel_name="res.country", string="Country", required=False, )

    home_country_phone_number = fields.Char(
        string='Home Country Phone Number')

    home_country_address = fields.Char(
        string='Home Country Address')

    involvement = fields.Selection(
        [('example', 'Example'), ('example2', 'Example2'), ],
        string='Involvement')

    supervisor = fields.Many2one(
        comodel_name='hr.employee',
        string='Supervisor',
        store=True)

    # project_id = fields.One2many(
    #     comodel_name='employee.project.line',
    #     inverse_name='employee_id',
    #     string='Project Name',
    #     groups='base.group_user')
    main_project = fields.Many2one('project.project', string='Work Location (Project)')
    # main_project_domain = fields.Char(
    #     compute="_compute_employee_main_project_domain",
    #     readonly=True
    # )
    main_project_domain = fields.Char(
        readonly=True
    )

    blood_group = fields.Selection(
        [('a+', 'A+'), ('a-', 'A-'), ('b+', 'B+'), ('b-', 'B-'), ('ab+', 'AB+'), ('ab-', 'AB-'), ('o+', 'O+'),
         ('o-', 'O-')],
        string='Blood Group'
    )

    health_card_number = fields.One2many(
        comodel_name='ebs.hr.document',
        inverse_name='employee_id',
        domain=_document_type_healthcard_domain,
        string='Health Card Number'
    )

    emergency_contact_custom = fields.One2many(
        comodel_name='emergency.contact',
        inverse_name='employee_id',
        string='Emergency Contact'
    )

    passport_number = fields.One2many(
        comodel_name='ebs.hr.document',
        inverse_name='employee_id',
        domain=_document_type_passport_domain,
        string='Passport'
    )

    visa_id = fields.One2many(
        comodel_name='ebs.hr.document',
        inverse_name='employee_id',
        domain=_document_type_visa_domain,
        string='Visa'
    )

    qid_number = fields.One2many(
        comodel_name='ebs.hr.document',
        inverse_name='employee_id',
        domain=_document_type_qid_domain,
        string='QID'
    )

    @api.model
    def _document_type_work_permit_domain(self):
        return [
            ('document_type.id', '=',
             self.env.ref('ebs_capstone_hr.hr_document_type_work_permit').id)
        ]

    @api.model
    def _document_type_secondment_permit_domain(self):
        return [
            ('document_type.id', '=',
             self.env.ref('ebs_capstone_hr.hr_document_type_secondment_permit').id)
        ]

    work_permit = fields.One2many(
        comodel_name='ebs.hr.document',
        inverse_name='employee_id',
        domain=_document_type_work_permit_domain,
        string='Work Permit'
    )

    secondment_permit = fields.One2many(
        comodel_name='ebs.hr.document',
        inverse_name='employee_id',
        domain=_document_type_secondment_permit_domain,
        string='Secondment Permit'
    )

    exit_permit_required = fields.Boolean(
        string='Exit Permit Required'
    )

    last_country_exit_date = fields.Date(
        string='Last Country Exit Date'
    )

    last_country_entry_date = fields.Date(
        string='Last Country Entry Date'
    )

    address_zone = fields.Char(
        string='National Address Zone', related="address_home_id.address_zone"
    )

    address_street = fields.Char(
        string='National Address Street', related="address_home_id.address_street"
    )

    address_building = fields.Char(
        string='National Address Building', related="address_home_id.address_building"
    )

    # group = fields.Selection(
    #     string="Group", default="g1", selection=[('g1', 'A1'), ('g2', 'A2'), ('g3', 'A3'), ('g4', 'A4'), ('g5', 'A5'),
    #                                              ('g6', 'A6'), ('g7', 'A7'), ('g8', 'A8'), ('g9', 'A9')],
    #     required=False)

    payroll_group = fields.Many2one(comodel_name="employee.payroll.group", string="Grade", required=False, store=True)

    qid_doc_number = fields.Char(compute="_get_qid_number", store=True, string="QID Number")

    passport_doc_number = fields.Char(compute="_get_passport_number", store=True, string="Passport Number")

    visa_doc_number = fields.Char(compute="_get_visa_number", store=True, string="Visa Number")

    # qid_doc_number = fields.Char(compute="_get_qid_number",  string="QID Number")
    #
    # passport_doc_number = fields.Char(compute="_get_passport_number", string="Passport Number")
    #
    # visa_doc_number = fields.Char(compute="_get_visa_number",  string="Visa Number")

    depend_qid = fields.Boolean()

    depend_passport = fields.Boolean()
    depend_visa = fields.Boolean()

    # driving_licence = fields.Many2many(comodel_name="driving.licence", string="Driving Licence", )

    qualification_type = fields.Char(string="Qualification Type", default="", required=False, )

    qualification_title = fields.Char(string="Qualification Title", default="", required=False, )

    unit = fields.Selection([
        ('support_services', 'Support Services'),
        ('business_support', 'Business Support'),
        ('portfolio', 'Portfolio'),
        ('operation', 'Operation'),
        ('directors', 'Directors')], string='Unit Selection', default='support_services')

    # ('PM_FM_manager', 'PM/ FM Manager'),
    sub_unit = fields.Selection([
        ('technician', 'Technician'),
        ('FM_site_staff', 'FM Site Staff'),
        ('PM_site_staff', 'PM Site Staff'),
        ('PM_manager', 'PM Manager'),
        ('FM_manager', 'FM Manager'),
        ('department_staff', 'Department Staff')], string='Sub Unit Selection')

    overtime_category = fields.Selection([
        ('fm_a9_a5', 'FM'),
        ('technical', 'Technical'),
        ('fm_a4_a1', 'FM'),
        ('pm', 'PM')])

    employee_states = fields.Selection(string="Status", default="draft",
                                       selection=[('draft', 'Draft'), ('confirmed', 'Confirmed'), ],
                                       required=False, )

    @api.onchange('birthday')
    def _compute_age(self):
        for rec in self:
            if rec.birthday:
                rec.age = ((date.today() - rec.birthday) / 365).days
            else:
                rec.age = 0

    def toggle_active(self):
        res = super(HREmployeeCustom, self).toggle_active()
        for rec in self:
            if rec.active:
                if rec.user_id:
                    rec.user_id.sudo().write({'active': True})
                contracts = self.env['hr.contract'].sudo().search(
                    [('active', '=', False), ('employee_id', '=', rec.id)])
                for contract in contracts:
                    contract.sudo().write({'active': True})
                if rec.sudo().address_home_id:
                    rec.sudo().address_home_id.sudo().write({'active': True})
        return res

    # @api.model
    # def create(self, vals):
    #     rec = super(HREmployeeCustom, self).create(vals)
    #     if rec:
    #         self.env['res.partner'].create({'name': rec.name})
    #         if rec.project_id:
    #             sum_perc = 0
    #             for each_project in rec.project_id:
    #                 sum_perc += each_project.percentage
    #             if sum_perc > 100 or sum_perc < 100:
    #                 raise UserError(_('You must enter percentage of involvement equal to 100.'))
    #     return rec
    #
    # def write(self, vals):
    #     # if "state" in vals:
    #     #     pass
    #     # else:
    #     #     vals['state'] = 'joined'
    #     res = super(HREmployeeCustom, self).write(vals)
    #     if self:
    #         if self.project_id:
    #             sum_perc = 0
    #             for each_project in self.project_id:
    #                 sum_perc += each_project.percentage
    #             if sum_perc > 100 or sum_perc < 100:
    #                 raise UserError(_('You must enter percentage of involvement equal to 100.'))
    #     return res

    def name_get(self):
        res = []
        for rec in self:
            res.append((rec.id, '%s' % (rec.name)))
        return res

    # @api.model
    # def _name_search(self, name='', args=None, operator='ilike', limit=100):
    #     if args is None:
    #         args = []
    #     domain = args + ['|', ('registration_number', operator, name), ('name', operator, name)]
    #     return super(HREmployeeCustom, self).search(domain, limit=limit).name_get()

    # cron job action
    # def create_employee_masterList(self):
    #     employees = self.env['hr.employee'].search([])
    #     for rec in employees:
    #         # age = ((date.today() - rec.birthday) / 365).days
    #         projects_list = []
    #         for line in rec.project_id:
    #             projects_list.append((0, 0, {
    #                 'project_id': line.project_id.id,
    #                 'start_date': line.start_date,
    #                 'end_date': line.end_date,
    #                 'transfer_date': line.transfer_date,
    #                 'transfer_reason': line.transfer_reason,
    #                 'trade': line.trade,
    #                 'percentage': line.percentage,
    #                 'type': line.type,
    #                 'nature': line.nature,
    #                 'job_title': line.job_title.id,
    #                 'department_id': line.department_id.id,
    #                 'department_id2': line.department_id2.id,
    #                 'department_id3': line.department_id3.id,
    #                 'active': line.active,
    #                 'company_id': line.company_id.id,
    #             }))
    #
    #         grade = ''
    #         if rec.wassef_employee_type == 'perm_in_house':
    #             grade = rec.payroll_group.name
    #         elif rec.wassef_employee_type == 'perm_staff':
    #             grade = rec.permanent_staff_employee.name
    #
    #         employee_masterList = {
    #             'name': rec.name,
    #             'employee_number': rec.registration_number,
    #             'status': rec.employee_states,
    #             "nationality": rec.country_id.id,
    #             "wassef_employee_type": rec.wassef_employee_type,
    #             "mobile": rec.sim_card,
    #             "gender": rec.gender,
    #             "marital": rec.marital,
    #             "email": rec.work_email,
    #             "national_identifier": rec.qid_doc_number,
    #             "passport_num": rec.passport_doc_number,
    #             "hire_date": rec.joining_date,
    #             "probation_date": rec.probation_date,
    #             "emp_dob": rec.birthday,
    #             # "emp_age": age,
    #             "job_pos": rec.job_id.id,
    #             "employee_projects": projects_list,
    #             "qualification_type": rec.qualification_type,
    #             "qualification_title": rec.qualification_title,
    #             'experience': ((date.today() - rec.joining_date) / 365).days if rec.joining_date else 0,
    #             "supervisor": rec.supervisor.id,
    #             "supervisor_no": rec.supervisor.registration_number,
    #             "emp_grade": grade if grade else '',
    #             "emp_profession": rec.qid_job if rec.qid_job else '',
    #             "basic": rec.contract_id.wage,
    #             "social": rec.contract_id.social_allowance_for_permanent_staff if
    #             rec.wassef_employee_type == 'perm_staff' else '',
    #             "housing": rec.contract_id.accommodation,
    #             "transportation": rec.contract_id.transport_allowance,
    #             "telephone": rec.contract_id.mobile_allowance,
    #             "other": rec.contract_id.other_allowance if rec.contract_id.other_allowance else '',
    #             "total": rec.contract_id.gross_salary,
    #
    #         }
    #
    #         master_list = self.env['employee.masterlist'].create(employee_masterList)

    # Employee Tickets
    ticket_ids = fields.One2many(comodel_name="hr.flight.ticket", inverse_name="emp_id", string="Tickets")
    ticket_count = fields.Float(string="Tickets Count", compute="_get_ticket_count")

    @api.depends('ticket_ids')
    def _get_ticket_count(self):
        for rec in self:
            if rec.ticket_ids:
                rec.ticket_count = len(rec.ticket_ids)
            else:
                rec.ticket_count = 0

    def custom_open_ticket(self):
        return {
            'name': _("Tickets"),
            'domain': [('id', 'in', self.ticket_ids.ids)],
            'view_type': 'form',
            'res_model': 'hr.flight.ticket',
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window'
        }

    # Cron job function to send email to hr responsible user to be informed with the employees missing bank accounts
    # def _send_email_to_hr_responsible(self):
    #     for rec in self:
    #         employees_wbar = rec.env['hr.employee'].search([('bank_account_id', '=', False)]).mapped('hr_responsible')
    #         for responsible in employees_wbar:
    #             employees = rec.env['hr.employee'].search(
    #                 [('bank_account_id', '=', False), ('hr_responsible', '=', responsible.id)])
    #             base = rec.env['ir.config_parameter'].sudo().get_param('web.base.url')
    #
    #             if employees:
    #                 ctx = {}
    #                 ctx['email_to'] = responsible.email
    #                 ctx['email_from'] = rec.env.user.company_id.email
    #                 ctx['send_email'] = True
    #                 ctx['employees'] = employees
    #                 ctx['base'] = base
    #                 template = rec.env.ref('ebs_hr_custom.email_template_for_hr_responsible')
    #                 template.with_context(ctx).send_mail(rec.id, force_send=True, raise_exception=False)

    def create_employee_portal_user(self):
        for rec in self:
            if not rec.user_id and rec.work_email and rec.name:
                group = rec.env['res.groups'].search([('name', '=', 'Portal')], limit=1)
                user = rec.env['res.users'].create({
                    'name': rec.name,
                    'login': rec.work_email,
                    'groups_id': [(6, 0, [group.id])]
                })

                if user:
                    rec.user_id = user.id
                    if user.partner_id:
                        user.partner_id.email = rec.user_id.login
                self.env.cr.commit()
                user.action_reset_password_portal()

    def action_get_employees_activities(self):
        # activities = self.env['mail.activity'].search([('res_model_id', '=', 'hr.employee')])
        # print(activities)
        return {
            'name': _('Employees Activities'),
            'domain': [('res_model_id', '=', 'hr.employee')],
            'view_type': 'form',
            'res_model': 'mail.activity',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }
        # return {
        #     'name': _('Employees Bank Account'),
        #     'domain': [('id', 'in', emp_banks.ids)],
        #     'view_type': 'form',
        #     'res_model': 'res.partner.bank',
        #     'view_id': False,
        #     'view_mode': 'tree,form',
        #     'type': 'ir.actions.act_window',
        # }


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    department_id = fields.Many2one('hr.department', 'Department',
                                    domain="['|', ('company_id', '=', False), ('company_id', '=', company_id), ('is_directorate','=', False)]")
