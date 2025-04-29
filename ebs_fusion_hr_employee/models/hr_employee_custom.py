from odoo import models, fields, api, _
from datetime import date, datetime
from datetime import timedelta
from odoo.exceptions import UserError
from dateutil import relativedelta
from odoo.exceptions import UserError, ValidationError


class ebsResidencypermit(models.Model):
    _inherit = 'ebs.residency.permit'
    _rec_name = 'occupation'

    employee_id = fields.Many2one('hr.employee')
    qid_ref_no = fields.Char("QID Reference Number")
    expiry_date = fields.Date("Expiry Date")


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    overseas_phone_number = fields.Char('Overseas Phone  Number')
    gender = fields.Selection(selection='get_gender',string="Gender")

    @api.model
    def get_gender(self):
        return [
            ('male', 'Male'),
            ('female', 'Female')
        ]

    @api.depends('document_o2m')
    def _compute_document_count(self):
        for rec in self:
            rec.document_count = len(rec.document_o2m)

    @api.onchange('first_name', 'middle_name', 'last_name')
    def _onchange_full_name(self):
        self.name = (self.first_name or '') + ' ' + (self.middle_name or '') + ' ' + (self.last_name or '')

    first_name = fields.Char("First Name")
    last_name = fields.Char("Last Name")
    middle_name = fields.Char("Middle Name")
    currency_home_country_id = fields.Many2one('res.currency', string="Currency Home Country")
    religion = fields.Char("Religion")
    father_name = fields.Char("Father Name")
    mother_name = fields.Char("Mother Name")
    blood_group = fields.Selection([('o-', 'O-'), ('o+', 'O+'), ('a-', 'A-'), ('a+', 'A+'),
                                    ('b-', 'B-'), ('b+', 'B+'), ('ab-', 'AB-'), ('Ab+', 'AB+'), ], string="Blood Group")

    blood_test_id = fields.Many2one('documents.document', string="Blood Test Result")
    eye_test = fields.Char("Eye Sight Test")
    vaccination_card_id = fields.Many2one('documents.document', string="Vaccination Card")
    police_certificate_id = fields.Many2one('documents.document', string="Police Certificate")

    is_qid = fields.Boolean('Is QID', default=False)

    comp_hearder = fields.Binary(string="Letter Head")
    comp_footer = fields.Binary(string="Letter Foot")

    document_o2m = fields.One2many(
        comodel_name='documents.document',
        inverse_name='employee_id',
        string='Related Documents',
        required=False
    )
    expired_document_o2m = fields.One2many(
        comodel_name='documents.document',
        inverse_name='employee_id',
        string='Expired Documents',
        required=False,
        domain=[('status', '=', 'expired')]
    )

    document_count = fields.Integer('Documents', related='', compute='_compute_document_count')

    phone_home = fields.Char("Phone Home")
    phone_personal = fields.Char("Personal Phone Number")

    p_o_box = fields.Char("P.O.Box")
    bank_details_in_the_home_country_id = fields.Many2one('res.partner.bank', string="Bank Details in the Home Country")
    trainings_attended = fields.Boolean("Trainings Attended")
    certificates_obtained = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Certificates Obtained")
    skype_id = fields.Char("Skype ID")
    height = fields.Char("Height")
    weight = fields.Char("Weight")
    dress_size = fields.Char("Dress Size")
    waist_size = fields.Char("Waist Size")
    feet_size = fields.Char("Feet Size")
    employee_no = fields.Char(string="Employee No.", copy=False, default='New')

    # HEALTH CONDITION

    allergic_food_drink = fields.Char("Allergic to any Food / Drinks or Nature")
    hypertensive = fields.Boolean("Hypertensive")
    diabetic = fields.Boolean("Diabetic")
    heart_desease = fields.Boolean("Heart Desease")
    blood_pressure = fields.Boolean("Blood Pressure")
    any_contagious_disease = fields.Boolean("Any Contagious Disease")
    others_comments = fields.Text("Others/Comments")
    do_you_smoke = fields.Boolean("Do you smoke ?")
    drink_alcohol = fields.Boolean("Do you Drink Alcohol?")

    # WORKMEN COMPENSATION
    policy_number = fields.Char("Policy Number")
    name_insurance_company = fields.Char("Name of the Insurance Company")
    list_benefeciary = fields.Char("List of Benefeciary")
    value = fields.Float("Value")

    # mail fields
    sponsor = fields.Char(string="Sponsor")

    qid_expiry_date = fields.Date("QID Expiry Date", compute='_qid_exp_date_compute')
    passport_ref_no_id = fields.Many2one('documents.document', string="Passport Ref.No")
    passport_expiry_date = fields.Date("Passport Expiry Date", compute='_passport_exp_date_compute')
    passport_country = fields.Many2one('res.country', 'Country of Passport')
    driver_lic_no_id = fields.Many2one('documents.document', string="Driver's License No")
    driver_lic_expiry_date = fields.Date("Driver's License Expiry Date")
    pro_id_card_ref_no_id = fields.Many2one('documents.document', string="PRO ID Card Ref.No")
    pro_id_expiry_date = fields.Date("PRO ID Expiry Date")
    labor_card_id = fields.Many2one('documents.document', string="Labor Card Ref.No")
    labor_card_expiry_date = fields.Date("Labor Card Expiry Date")
    e_services_expiry_date = fields.Date("E-Services Expiry Date")
    work_permit_ref_no_id = fields.Many2one('documents.document', string="Work Permit Ref.No")
    work_permit_expiry_date = fields.Date("Work Permit Expiry Date")
    health_certificate_expiry_date = fields.Date("Health Certificate (Food Handler Services) Expiry Date")
    remark = fields.Text("Remark")

    # Previous Employment Contract todo

    # SOCIAL MEDIA USER NAME FOR EMPLOYEE
    facebook = fields.Char("Facebook")
    google = fields.Char("Google")
    twitter = fields.Char("Twitter")
    linkedin = fields.Char("Linkedin")
    snapchat = fields.Char("Snapchat")
    other = fields.Char("Other")
    comments = fields.Char("SOCIAL MEDIA Others/Comments")

    passport_details_ids = fields.One2many('ebs.passport.details', 'employee_id', string="Passport Details")
    residency_permit_ids = fields.One2many('ebs.residency.permit', 'employee_id', string="QID")
    health_card_ids = fields.One2many('ebs.health.card', 'employee_id', string="Health Card")
    insurance_ids = fields.One2many('ebs.insurance', 'employee_id', string="Insurance")
    education_ids = fields.One2many('ebs.education', 'employee_id', string="Education")
    sponsoring_dependents_ids = fields.One2many('ebs.sponsoring.dependents', 'employee_id',
                                                string="Sponsoring Dependents")
    family_details_ids = fields.One2many('ebs.family.details', 'employee_id', string="Faily Details")
    visa_details_ids = fields.One2many('ebs.visa.details', 'employee_id', string="Visa Details")

    dependent_work_ids = fields.Many2one('res.partner')
    driving_licence_ids = fields.One2many('ebs.driving.licence', 'employee_id', string="Driving Licence")

    bank_details_ids = fields.One2many('res.partner.bank', 'employee_id', string="Bank Details")
    penalty_ids = fields.One2many('ebs.penalty', 'employee_id', string="Penalty")
    history_experience_ids = fields.One2many('ebs.history.experience', 'employee_id', string="History Experience")
    hobbies_ids = fields.One2many('ebs.hobbies', 'employee_id', string="Hobbies")
    hr_employee_econtract_ids = fields.One2many('hr.employee.econtract', 'employee_id', string="E-Contract")
    arabic_name = fields.Char('Arabic Name')
    reference = fields.Char("Reference")

    qid_name = fields.Char("QID Name")
    qid_no = fields.Char("QID No", compute='_qid_exp_date_compute', compute_sudo=True)
    qid_no_search = fields.Char('QID No', compute='compute_doc_no_search', store=True)
    qid_job_position_id = fields.Many2one('hr.job', string='QID Job Position', compute='_qid_exp_date_compute',
                                          compute_sudo=True)
    passport_name = fields.Char("Passport Name")
    passport_no = fields.Char("Passport No", compute="_passport_exp_date_compute")
    passport_no_search = fields.Char('Passport No', compute='compute_doc_no_search', store=True)
    visa_no = fields.Char('Visa No', groups="hr.group_hr_user", compute="_visa_exp_date_compute")
    visa_no_search = fields.Char('Visa No', compute='compute_doc_no_search', store=True)
    visa_type = fields.Many2one('ebs.visa.type', 'Visa Type', compute="_visa_exp_date_compute")
    visa_expire = fields.Date('Visa Expiring Date', groups="hr.group_hr_user",
                              compute="_visa_exp_date_compute")
    visa_issue = fields.Date('Visa Issue Date', groups="hr.group_hr_user",
                             compute="_visa_exp_date_compute")
    date_entry = fields.Date("Date of Entry", compute="_visa_date_entry_and_valid_till")
    visa_valid_till = fields.Date("Visa Valid till", compute="_visa_date_entry_and_valid_till")
    workmen_compensation_ids = fields.One2many('ebs.workmen.compensation', 'employee_id', string='Workmen Compensation')
    qcsw_dated = fields.Date(string='Dated')
    qcsw_company_name = fields.Char(string='Company Name')
    qcsw_cr_no = fields.Char(string='Commercial Registeration No.')
    qcsw_address = fields.Text(string='QCSW Address')
    qcsw_admin_supervisor = fields.Char(string='Admin Supervisor')

    qcsw_file = fields.Many2one('documents.document', string='File')
    qcsw_mobile_no = fields.Char(string='Mobile No')
    qcsw_phone = fields.Char(string='Phone')
    qcsw_po_box = fields.Char(string='QCSW P.O Box')
    qcsw_fax = fields.Char(string='Fax')
    qcsw_email = fields.Char(string='Email')
    qcsw_preffered_contact = fields.Selection([('fax', 'Fax'),
                                               ('email', 'Email'),
                                               ('sms', 'SMS'), ],
                                              string='Preffered Contact')
    qcsw_comments = fields.Text(string='QCSW Other/ Comments')

    nationality_birth = fields.Many2one('res.country', string='Nationality – Birth')
    employee_allowance_ids = fields.One2many('ebs.employee.allowance', 'employee_id', string='Allowances')

    has_employee_personal_profile = fields.Boolean('Employee Personal Profile')

    has_access_card = fields.Boolean('Access Card')
    age = fields.Integer('Age', compute='compute_age')
    emergency_contact_qatar = fields.Char('Emergency Contact(Qatar)')
    emergency_phone_qatar = fields.Char('Emergency Phone(Qatar)')
    emergency_relation_qatar = fields.Char('Relation to Employee(Qatar)')
    emergency_relation_hc = fields.Char('Relation to Employee')
    entry_date = fields.Date(string="Entry Date")
    exit_date = fields.Date(string="Exit Date")
    service_fee = fields.Float(string="Service Fee")
    signature = fields.Binary(string="Signature")
    transfer_no = fields.Char('Transfer No.')
    end_of_notice_period = fields.Date('End of Notice Period')
    release_of_responsibility = fields.Date('Release of Responsibility', compute='compute_release_of_responsibility')
    absconding_report_no = fields.Char('Absconding Report No.')
    transfer_completion = fields.Date('Transfer Completion Date')
    cancellation_date = fields.Date('Cancellation Date')
    emp_residence_id = fields.Many2one(comodel_name="ebs.emp.residence", string="Employee Residence")
    zone_id = fields.Many2one('ebs.na.zone', string="Zone")
    na_street = fields.Many2one('ebs.na.street', string="Street")
    building = fields.Many2one('ebs.na.building', string="Building")
    unit = fields.Char('Unit')
    client_abbreviation = fields.Char(related='partner_parent_id.abbreviation')
    child_allowance = fields.Float('Child Allowance')
    tuition_fees = fields.Float("رسوم تعلیم")
    medical_ins = fields.Float("تأمين طبي")

    def link_employee_partner(self, partner=None):
        if partner:
            self.user_partner_id = partner.id
        else:
            self.user_partner_id = self.env['res.partner'].create({
                'is_employee': True,
                'name': self.name,
                'email': self.work_email,
                'parent_id': self.partner_parent_id.id,
                'main_parent_id': self.parent_id.id,
                'company_type': 'person',
                'is_company': False
            })
        if self.user_partner_id:
            self.add_payable_receivable_employee_partner()

    def add_payable_receivable_employee_partner(self):
        res_company = self.env.user.company_id.search([])
        for company in res_company:
            if self.employee_type == 'fusion_employee':
                self.user_partner_id.sudo().with_context(force_company=company.id).write({
                    'property_account_receivable_id': company.fusion_employee_receivable.id if company.fusion_employee_receivable else False,
                    'property_account_payable_id': company.fusion_employee_payable.id if company.fusion_employee_payable else False})
            if self.employee_type == 'fos_employee':
                self.user_partner_id.sudo().with_context(force_company=company.id).write({
                    'property_account_receivable_id': company.outsourced_employee_receivable.id if company.outsourced_employee_receivable else False,
                    'property_account_payable_id': company.outsourced_employee_payable.id if company.outsourced_employee_payable else False})

    def outsourced_national_address_reminder(self):
        report_config_id = self.env['outsourced.employee.report.config'].search(
            [('template', '=', 'outsourced_national_address_report')])
        if report_config_id:
            attachment_id = self.env['outsourced.employee.report.wizard'].with_context(
                {'mail_attachment': True}).get_outsourced_national_address_report()
            mail_server_id = self.env['ir.mail_server'].sudo().search([], order='sequence asc', limit=1)
            for user in report_config_id.user_ids:
                recipient_ids = [(4, user.partner_id.id)]
                mail = self.env['mail.mail'].sudo().create({
                    'subject': 'Outsourced Employee National Address Expiry Date Reminder',
                    'body_html': '''<p>Dear %s,</p><p>Please find attached the auto-generated report on national address 
                                    registration. If you are the allocated account manager, please take the necessary actions.</p>
                                    <p>Kind Regards,</p><p>Odoo System</p>''' % (user.partner_id.name),
                    'recipient_ids': recipient_ids,
                    'attachment_ids': [(6, 0, attachment_id.ids)],
                    'mail_server_id': mail_server_id and mail_server_id.id,
                })
                mail.send()

    def outsourced_qid_reminder(self):
        report_config_id = self.env['outsourced.employee.report.config'].search(
            [('template', '=', 'outsourced_qid_report')])
        if report_config_id:
            attachment_id = self.env['outsourced.employee.report.wizard'].with_context(
                {'mail_attachment': True}).get_outsourced_qid_report()
            mail_server_id = self.env['ir.mail_server'].sudo().search([], order='sequence asc', limit=1)
            for user in report_config_id.user_ids:
                recipient_ids = [(4, user.partner_id.id)]
                mail = self.env['mail.mail'].sudo().create({
                    'subject': 'Outsourced Employee Qid Expiry Date Reminder',
                    'body_html': '''<p>Dear %s,</p><p>Please find attached the auto-generated report on both expired QIDs and 
                                    upcoming QID expiries within the next 3 months. If you are the allocated account manager, 
                                    please take the necessary actions.</p><p>Kind Regards,</p><p>Odoo System</p>'''
                                 % (user.partner_id.name),
                    'recipient_ids': recipient_ids,
                    'attachment_ids': [(6, 0, attachment_id.ids)],
                    'mail_server_id': mail_server_id and mail_server_id.id,
                })
                mail.send()

    @api.onchange('emp_residence_id')
    def emp_residence_id_onchange(self):
        self.zone_id = self.emp_residence_id.zone_id.id
        self.na_street = self.emp_residence_id.street.id
        self.building = self.emp_residence_id.building.id
        self.unit = self.emp_residence_id.unit

    def action_update_employee_outsourced_status(self):
        if any(employee.employee_type != 'fos_employee' for employee in self):
            raise ValidationError(_("This action is available only for Outsourced Employees."))
        action = self.env.ref('ebs_fusion_hr_employee.update_outsourced_status_wizard_action').read()[0]
        action['context'] = {'default_employee_ids': [(6, 0, self.ids)]}
        return action

    def _get_eng_to_arabic(self, model, res_id, field):
        rec = self.env['ir.translation'].search([
            ('name', '=', model + ',' + field),
            ('lang', '=', 'ar_SY'),
            ('res_id', '=', res_id)
        ])
        return rec.value or ''

    @api.depends('end_of_notice_period')
    def compute_release_of_responsibility(self):
        for rec in self:
            if rec.end_of_notice_period:
                rec.release_of_responsibility = rec.end_of_notice_period + timedelta(days=30)
            else:
                rec.release_of_responsibility = False

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            self.name = str(self.name).title()
        else:
            self.name = ''

    def open_my_profile(self):
        action = self.env.ref('hr.open_view_employee_list_my').read()[0]
        action['views'] = [(self.env.ref('ebs_fusion_hr_employee.ebs_custom_hr_employee_view').id, 'form')]
        action['context'] = {'create': 0, 'edit': 0, 'delete': 0, 'my_profile': True}
        action['view_mode'] = 'form'
        action['res_id'] = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)]).id
        return action

    @api.onchange('partner_parent_id')
    def onchange_partner_parent_id(self):
        contract_id = self.env['ebs.crm.proposal']
        if self.partner_parent_id:
            contract_id = self.env['ebs.crm.proposal'].search(
                [('contact_id', '=', self.partner_parent_id.id), ('state', '=', 'active')], limit=1)
        self.service_fee = contract_id.service_fee_per_employee

    @api.depends('birthday')
    def compute_age(self):
        for rec in self:
            rec.age = relativedelta.relativedelta(datetime.now(), rec.birthday).years

    @api.constrains('employee_no')
    def validate_unique_employee_no(self):
        if self.employee_type == 'fusion_employee' and self.state == 'approved':
            if self.employee_no != 'New':
                if self.env['hr.employee'].search([('employee_no', '=', self.employee_no)]) - self:
                    raise UserError(_('Employee No field must be unique'))

    @api.model
    def create(self, vals):
        if vals.get('employee_type') == 'fusion_employee':
            vals.update({'employee_no': self.env['ir.sequence'].next_by_code('employee_no') or _('New')})
        result = super(HrEmployee, self).create(vals)
        if 'contract_employee' in self._context:
            contract_employee_line = self.env['ebs.crm.proposal.employee.line'].browse(
                [self._context.get('contract_employee')])

            contract_employee_line.contract_id = self.env['hr.contract'].create({
                'employee_id': result.id,
                'date_start': date.today(),
                'job_id': contract_employee_line.job_id.id,
                'wage': contract_employee_line.total_salary_package,
                'accommodation': contract_employee_line.monthly_eos,
                'transport_allowance': contract_employee_line.monthly_service_fees,
                'food_allowance': contract_employee_line.food_allowance,
                'other_allowance': contract_employee_line.other_allowance,
                'structure_type_id': contract_employee_line.structure_type_id.id,
            })
        return result

    @api.depends('visa_details_ids')
    def _visa_date_entry_and_valid_till(self):
        for rec in self:
            entry = ''
            valid = ''
            visa_id = self.env['ebs.visa.details'].search([('employee_id', '=', rec._origin.id)], order='id desc',
                                                          limit=1)
            if visa_id:
                entry = visa_id.date_entry
                valid = visa_id.visa_valid_till
            rec.date_entry = entry
            rec.visa_valid_till = valid

    def _qid_exp_date_compute(self):
        for rec in self:
            qid_ids = self.env['documents.document'].search([
                ('document_type_name', '=', 'QID'),
                ('employee_id', '=', rec.id)
            ])
            if qid_ids:
                rec.qid_expiry_date = qid_ids[0].expiry_date
                rec.qid_no = qid_ids[0].document_number
                rec.qid_job_position_id = qid_ids[0].job_title.id
            else:
                rec.qid_expiry_date = False
                rec.qid_no = False
                rec.qid_job_position_id = False

    def _passport_exp_date_compute(self):
        for rec in self:
            passport_ids = self.env['documents.document'].search([
                ('document_type_name', '=', 'Passport'),
                ('employee_id', '=', rec.id)
            ])
            if passport_ids:
                rec.sudo().passport_expiry_date = passport_ids[0].expiry_date
                rec.sudo().passport_no = passport_ids[0].document_number
                rec.sudo().passport_country = passport_ids[0].country_passport_id.id
            else:
                rec.sudo().passport_expiry_date = False
                rec.sudo().passport_no = False
                rec.sudo().passport_country = False

    def _visa_exp_date_compute(self):
        for rec in self:
            visa_ids = self.env['documents.document'].search([
                ('document_type_name', '=', 'Visa'),
                ('employee_id', '=', rec.id)
            ])
            if visa_ids:
                rec.visa_no = visa_ids[0].document_number
                rec.visa_expire = visa_ids[0].expiry_date
                rec.visa_issue = visa_ids[0].issue_date
                rec.visa_type = visa_ids[0].visa_type_id.id
            else:
                rec.visa_no = False
                rec.visa_expire = False
                rec.visa_issue = False
                rec.visa_type = False

    @api.depends('qid_no', 'visa_no', 'passport_no')
    def compute_doc_no_search(self):
        for rec in self:
            rec.qid_no_search = rec.qid_no
            rec.passport_no_search = rec.passport_no
            rec.visa_no_search = rec.visa_no

    def open_related_documents(self):
        res = self.env.ref('documents.document_action').read()[0]
        res.update({
            'context': {'search_default_employee_id': self.id, 'default_employee_id': self.id},
            'domain': [('employee_id', '=', self.id), ('employee_id', '!=', False)],
        })
        return res

    partner_id = fields.Many2one("res.partner", string="Partner")

    user_partner_id = fields.Many2one('res.partner', related=False, string="User's partner")

    def write(self, vals):
        res = super(HrEmployee, self).write(vals)
        if vals.get('user_partner_id'):
            self.user_partner_id.email = self.work_email
        if self.user_partner_id and vals.get('work_email'):
            self.user_partner_id.email = vals.get('work_email')
        if vals.get('state'):
            if vals.get('state') == 'approved':
                proposal_employee_line = self.env['ebs.crm.proposal.employee.line'].search(
                    [('name', '=', self.id), ('proposal_state', '=', 'active')])
                if proposal_employee_line:
                    print(proposal_employee_line.fos_fees_line_id)
                    labor_quota_line_id = proposal_employee_line.fos_fees_line_id.labor_quota_line_id
                    if labor_quota_line_id:
                        labor_quota_line_id.write({
                            'subline_ids': [
                                (0, 0, {'status': 'booked', 'contract_id': proposal_employee_line.proposal_id.id,
                                        'employee_id': self.id})],
                        })
                        proposal_reserved_lines = labor_quota_line_id.reserved_line_ids.filtered(
                            lambda l: l.lead_id.id == proposal_employee_line.proposal_id.lead_id.id)
                        if proposal_reserved_lines:
                            proposal_reserved_lines[0].unlink()
            if vals.get('state') == 'reject':
                proposal_employee_line = self.env['ebs.crm.proposal.employee.line'].search(
                    [('name', '=', self.id), ('proposal_state', '=', 'active')])
                if proposal_employee_line:
                    print(proposal_employee_line.fos_fees_line_id)
                    fos_structure_id = proposal_employee_line.fos_fees_line_id
                    labor_quota_line_id = fos_structure_id.labor_quota_line_id
                    if labor_quota_line_id:
                        labor_quota_line_id.write({
                            'reserved_line_ids': [
                                (0, 0, {'nationality_id': fos_structure_id.nationality_id.id,
                                        'job_id': fos_structure_id.job_position.id,
                                        'gender': fos_structure_id.gender,
                                        'lead_id': fos_structure_id.lead_id.id})],
                        })
                        proposal_subline_ids = labor_quota_line_id.subline_ids.filtered(
                            lambda l: l.employee_id.id == self.id)
                        if proposal_subline_ids:
                            proposal_subline_ids.write({'status': 'released', 'employee_id': False})

        if vals.get('name') and self.user_partner_id:
            self.user_partner_id.name = vals.get('name')

        if vals.get('user_partner_id'):
            if self.document_o2m:
                for doc in self.document_o2m:
                    doc.write({'partner_id': self.user_partner_id.id})
            if self.user_partner_id.document_o2m:
                for doc in self.user_partner_id.document_o2m:
                    if not doc.employee_id or doc.employee_id.id != self.id:
                        doc.write({'employee_id': self.id})
        return res

    @api.onchange('user_id')
    def onchange_user_partner_id(self):
        if self.user_id and not self.user_partner_id:
            self.user_partner_id = self.user_id.partner_id.id


class EbsEmployeeAllowance(models.Model):
    _name = 'ebs.employee.allowance'
    _description = 'EBS Employee Allowance'

    employee_id = fields.Many2one('hr.employee', 'Employee')
    type = fields.Selection([('housing', 'Housing'), ('car', 'car'), ('other', 'Other/Comments')],
                            string='Type of Allowance')
    start_date = fields.Date('Start Date')
    renewal_date = fields.Date('Renewal Date')
    comments = fields.Text('Comments')
    instructions = fields.Text('Instructions')
