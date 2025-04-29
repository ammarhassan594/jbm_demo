from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import xml.etree.ElementTree as ET
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.osv import expression


class DocumentsCustom(models.Model):
    _inherit = 'documents.document'
    _rec_name = 'document_number'

    partner_id = fields.Many2one('res.partner', string="Partner")
    employee_id = fields.Many2one('hr.employee', "Employee")
    status = fields.Selection(
        string='Status',
        selection=[('na', 'N/A'),
                   ('active', 'Active'), ('expired', 'Expired')],
        default='na',
        required=False, readonly=True)

    document_type_categ_id = fields.Many2one(
        string='Document Type Category',
        related='document_type_id.document_categ_id',
        store=True
    )

    document_type_id = fields.Many2one(
        comodel_name='ebs.document.type',
        string='Document Type',
        required=False)
    is_seq = fields.Boolean(related='document_type_id.seq_req')
    document_type_name = fields.Selection(string='Document Type', related="document_type_id.meta_data_template")
    active = fields.Boolean(default=True, string="Active")
    arabic_file = fields.Binary(string="Arabic File")
    show_ar_file = fields.Boolean(related='document_type_id.show_ar_file')

    document_number = fields.Char(
        string='Document Number',
        required=False)

    hide_related_fields = fields.Boolean(default=False)
    expiry_date = fields.Date("Expiry Date")
    issue_date = fields.Date("Issue Date")
    show_issue_date = fields.Boolean()
    is_expired = fields.Boolean('Is Expired')
    show_issue_expiry = fields.Boolean()
    show_issue_expiry_req = fields.Boolean()
    document_cycle_ids = fields.One2many('document.cycle', 'document_id', string='Document Cycle')
    version = fields.Integer('Version', default=1, copy=False)
    document_ids = fields.Many2many('documents.document', 'm2m_documents_document', column1="document_parent_id",
                                    column2="document_child_id", string="Document", context={'active_test': False},
                                    domain=['|', ('active', '=', True), ('active', '=', False)])

    qid = fields.Integer('QID')
    qid_name = fields.Char('QID Name')
    sponsor_name = fields.Many2one('res.partner', string='Sponsor Name')
    job_title = fields.Many2one('hr.job', string="Job Title")
    residency_type = fields.Selection([
        ('entry', 'Entry Visas'), ('work', 'Work Residence Permit'), ('id', 'ID Cards'),
        ('family', 'Family Residence Visa'), ('exit', 'Exit Permit'),
        ('consular', 'Consular Services')
    ], default="work", string="Residency Type")
    passport_no = fields.Char('Passport No')
    passport_name = fields.Char('Passport Name')

    date_of_birth = fields.Date('Date Of Birth')
    nationality = fields.Many2one('res.country', string="Nationality")
    place_of_birth = fields.Char('Place Of Birth')
    passport_type = fields.Selection(
        [('regular', 'Regular'), ('special', 'Special'), ('diplomatic', 'Diplomatic'), ('service', 'Service')],
        string="Passport Type")
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], string="Gender", default="male")
    date_of_contract = fields.Date('Date Of Contract')
    duration = fields.Selection([
        ('1', '1 Year'),
        ('2', '2 Year'),
        ('3', '3 Year'),
        ('4', '4 Year'),
        ('5', '5 Year'),
    ], default="1")
    basic_salary = fields.Float('Basic Salary')
    allowances_salary = fields.Float('Allowances Salary')
    address = fields.Char('Address')
    university = fields.Char('University')
    degree = fields.Char('Degree')
    year_of_graduation = fields.Date('Year Of Graduation')
    folder_ids = fields.Many2many('documents.folder', string='Folder')
    passport_id = fields.Char(string='Passport')
    visa_type_id = fields.Many2one('ebs.visa.type', 'Visa Type')
    stay_period = fields.Integer('Stay Period in Months')
    residency_period = fields.Integer('Residency Period in Years')
    entry_date = fields.Date('Entry Date')
    is_original = fields.Boolean('Original')

    date_initiation = fields.Date('Date of initiation')
    period = fields.Integer('Period in Years')
    date_term = fields.Date('Date of Term')

    agreement_party1 = fields.Many2one('res.partner', 'Party 1')
    agreement_party2 = fields.Many2one('res.partner', 'Party 2')
    power_of_attorney_contact_person = fields.Many2one('res.partner', 'Contact Person')

    financial_day = fields.Integer('Day', default=1)
    financial_month = fields.Selection(
        [('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'), ('5', 'May'),
         ('6', 'June'), ('7', 'July'), ('8', 'August'), ('9', 'September'),
         ('10', 'October'), ('11', 'November'), ('12', 'December'), ], string='Financial Month', default='1')
    financial_year = fields.Date('Financial year')
    financial_link_partner = fields.Many2one('res.partner', 'Financial Manager')
    general_manager = fields.Many2one('res.partner', 'General Manager')
    general_secretary = fields.Many2one('res.partner', 'General Secretary')
    admin_manager = fields.Many2one('res.partner', 'Administration Manager')
    banking_signatory = fields.Many2one('res.partner', 'Banking Signatory')
    liaison_officer = fields.Many2one('res.partner', 'Liaison Officer')

    shareholder_contact_ids = fields.Many2many('res.partner', 'client_shareholder_document_rel', 'document_id',
                                               'shareholder_id', string="Shareholders", )
    edit_access = fields.Boolean(compute='compute_edit_access')

    def compute_edit_access(self):
        for rec in self:
            rec.edit_access = self.user_has_groups('documents.group_documents_manager')

    @api.onchange('date_initiation', 'period')
    def cal_date_of_term(self):
        if self.date_initiation and self.period:
            self.date_term = self.date_initiation + relativedelta(years=self.period)
        else:
            self.date_term = False

    @api.model
    def create(self, vals):
        partner = self.env['res.partner'].sudo().browse(self.env.context.get('default_partner_id'))

        if not vals.get('document_number'):
            document_type = self.env['ebs.document.type'].search([('id', '=', vals.get('document_type_id'))])
            if document_type.seq_req:
                vals['document_number'] = document_type.sequence.next_by_id()

        if self._context.get('default_type') and self._context.get('default_type') not in ['url', 'binary']:
            context = dict(self.env.context).copy()
            context.update({'default_type': 'binary'})
            self.env.context = context
        res = super(DocumentsCustom, self).create(vals)
        if res.expiry_date and res.expiry_date < date.today():
            res.status = 'expired'
            res.is_expired = True
        elif res.expiry_date and res.expiry_date >= date.today():
            res.status = 'active'
            res.is_expired = False
        else:
            res.status = 'na'
            res.is_expired = False
        return res

    def send_mail(self):
        mail_server_id = self.env['ir.mail_server'].sudo().search([], order='sequence asc', limit=1)
        message = self.env['mail.message'].sudo().create({
            'subject': self._context.get('subject'),
            'body': self._context.get('body_html'),
            'author_id': self.env.user.partner_id.id,
            'model': self._name,
            'res_id': self.id,
        })
        mail = self.env['mail.mail'].sudo().create({
            'email_from': self._context.get('email_from'),
            'subject': self._context.get('subject'),
            'body_html': self._context.get('body_html'),
            'email_to': self._context.get('email_to'),
            'email_cc': self._context.get('email_cc'),
            'attachment_ids': [(6, 0, self._context.get('attachment_ids'))],

            'mail_server_id': self._context.get('mail_server_id') or mail_server_id.id,
            'mail_message_id': message.id,
        })
        mail.send()

    def open_mail_window(self):
        partner_lst = []
        doc_with_emp = self.filtered(lambda x: x.employee_id.id)
        doc_without_emp = self.filtered(lambda x: not x.employee_id.id)
        if doc_without_emp:
            if len(doc_without_emp.mapped('partner_id.id')) > 1:
                raise ValidationError(_('Please select Document For same Client'))
            else:
                partner_lst += doc_without_emp.mapped('partner_id.id')
        if doc_with_emp:
            if len(doc_with_emp.mapped('employee_client_id.id')) > 1:
                raise ValidationError(_('Please select Document For same Client'))
            else:
                if partner_lst and doc_with_emp.mapped('employee_client_id.id') != partner_lst:
                    raise ValidationError(_('Please select Document For same Client'))
                elif not partner_lst:
                    partner_lst += doc_with_emp.mapped('employee_client_id.id')
        client = self.env['res.partner'].browse(partner_lst)
        body = "Dear <b>%s,</b> <br/><br/> Find attached the document requested. <br/><br/> Regards. " % (client.name)
        subject = "Document Send by Mail"
        attachment = [(6, 0, self.attachment_id.ids)]
        partner_id = [(6, 0, self.mapped('partner_id').ids)]

        return {
            'name': _('Document Send By mail'),
            'type': 'ir.actions.act_window',
            'res_model': 'document.send.mail',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {
                'default_model': 'documents.document',
                'default_attachment_ids': attachment,
                'default_partner_ids': partner_id,
                'default_body': body,
                'default_subject': subject,
                'active_doc': self.ids,
                'default_template_id': self.env.ref('ebs_fusion_documents.document_email_template_send').id
            }
        }

    cr_reg_no = fields.Char('Commercial Reg. No.')
    cr_tax_reg_no = fields.Char(string='Tax Reg. No.')
    cr_trade_name = fields.Char('CR Trade Name')
    cr_creation_date = fields.Date('Creation Date')
    cr_legal_form = fields.Many2one('cr.legal.form', 'Legal Form')
    cr_capital = fields.Float('Capital', default=0)
    cr_reg_status = fields.Many2one('commercial.reg.status', 'Commercial Reg. status')
    cr_no_brances = fields.Integer('No. of branches', default=0)
    cl_partner_id = fields.Many2one('res.partner', string='Manager in charge')
    license_number = fields.Char(string="License Number")
    cr_partner_ids = fields.Many2many('res.partner', 'document_partner_rel', string='Partners')
    cr_managers_ids = fields.Many2many('res.partner', 'document_manager_rel', string='Managers')
    cr_authorizers_ids = fields.Many2many('res.partner', 'document_authorizer_rel', string='Authorizers')
    cr_business_activities_ids = fields.Many2many('business.activities', string='Business Activities')
    cl_name = fields.Char("Name")
    cl_location_category = fields.Char('Location Category')
    cl_location_type = fields.Char('Location Type')
    cl_area = fields.Char('Area')
    cl_street = fields.Char('Street')
    cl_street_no = fields.Char('Street No.')
    cl_plot_no = fields.Char('Plot No.')
    cl_unit_no = fields.Char('Unit No.')
    cl_owner_name = fields.Char('Owner Name')
    cl_licence_type = fields.Char('License Type')
    cl_address_description = fields.Char('Address Description')
    est_id = fields.Char('Est. ID')
    est_name_en = fields.Char('Est. Name (En)')
    arabic_name = fields.Char()
    est_sector = fields.Many2one('est.sector', 'Sector')
    est_first_issue = fields.Date(' First Issue')
    first_name = fields.Char("First Name")
    middle_name = fields.Char("Middle Name")
    last_name_1 = fields.Char("Last Name 1")
    last_name_2 = fields.Char("Last Name 2")
    father_name = fields.Char("Father Name")
    place_of_issue = fields.Char('Place Of Issue')
    country_passport_id = fields.Many2one('res.country', string='Country of Passport')
    double_citizenship_ids = fields.Many2many('res.country', string='Double Country Citizenship')
    sponsor_id = fields.Char('Sponsor ID')
    visa_residence_permit = fields.Char('Visa/Residence Permit')
    occupation = fields.Char('Occupation')
    visit_visa = fields.Char('Visit Visa')
    text = fields.Text('Others/Comments')
    visa_ref_no = fields.Char('Visa Reference Number')
    lead_id = fields.Many2one('crm.lead', string='Lead')

    child_national_ids = fields.Many2many('res.partner', string='National Address',
                                          )
    # Child National Fields
    zone_id = fields.Many2one('ebs.na.zone', string="Zone")
    street = fields.Many2one('ebs.na.street', string="Street")
    building = fields.Many2one('ebs.na.building', string="Building")
    unit = fields.Char('Unit')

    aoa_partner_ids = fields.Many2many('res.partner', 'client_shareholder_document_rel', 'document_id',
                                       'shareholder_id', string="Shareholders",
                                       )
    document_o2m = fields.Many2many('documents.document', 'document_document_custom_rel', 'document_id', 'documents_id',
                                    string="Documents")
    is_client_rel = fields.Boolean('Client Relation')

    @api.constrains('issue_date', 'expiry_date')
    def validate_issue_date(self):
        for rec in self:
            if rec.issue_date and rec.expiry_date and rec.issue_date >= rec.expiry_date:
                raise ValidationError("Issue Date Must Be Less Than Expiry Date.")

    @api.onchange('document_type_id')
    def onchange_document_type(self):
        for rec in self:
            if rec.document_type_id:
                folder_line_id = self.env['ebs.document.type.folder'].sudo().search(
                    [('doc_type_id', '=', rec.document_type_id.id), ('company_id', '=', self.env.company.id)])
                rec.sudo().write({'folder_id': folder_line_id.folder_id.id})
            else:
                rec.folder_id = False
            if rec.document_type_id.has_reminder_for_renewal == 'required':
                rec.reminder_for_renewal = True
            else:
                rec.reminder_for_renewal = False

    @api.constrains('document_number')
    def _check_document_number(self):
        for record in self:
            qid_document_type_id = self.env['ebs.document.type'].search([('meta_data_template', '=', 'QID')])
            cr_document_type_id = self.env['ebs.document.type'].search(
                [('meta_data_template', '=', 'Commercial Registration (CR) Application')])
            cl_document_type_id = self.env['ebs.document.type'].search(
                [('meta_data_template', '=', 'Commercial License')])
            if record.document_type_id.id == qid_document_type_id.id and not len(
                    ''.join(filter(str.isalnum, record.document_number))) == 11:
                raise ValidationError("Please enter exact 11 characters for QID document number")

    # @api.onchange('document_number', 'visa_type_id')
    # def onchange_document_number(self):
    #     if self.document_number:
    #         self.document_number = self.translate_doc_no(self.document_number)
    #         domain = [('document_number', '=', self.document_number),
    #                   ('document_type_id', '=', self.document_type_id.id)]
    #         if self.document_type_name == 'Visa':
    #             domain.append(('visa_type_id', '=', self.visa_type_id.id))
    #         search_record = self.env['documents.document'].sudo().search(domain) - self
    #         if search_record:
    #             raise ValidationError("A %s document with this document number %s already exists!"
    #                                   % (self.document_type_id.name, self.document_number))

    def translate_doc_no(self, txt):
        pass
    #     intab = '١٢٣٤٥٦٧٨٩٠'
    #     outtab = '1234567890'
    #     translation_table = str.maketrans(intab, outtab)
    #     return txt.translate(translation_table)

    def write(self, vals):
        if 'document_type_id' in vals and not vals.get('document_number'):
            old_doc = self.document_number
            document_type = self.env['ebs.document.type'].search([('id', '=', vals.get('document_type_id'))])
            if document_type and document_type.seq_req:
                vals['document_number'] = document_type.sequence.next_by_id()

        res = super(DocumentsCustom, self).write(vals)
        if 'expiry_date' in vals:
            if self.expiry_date and self.expiry_date < date.today():
                self.status = 'expired'
                self.is_expired = True
            elif self.expiry_date and self.expiry_date >= date.today():
                self.status = 'active'
                self.is_expired = False
            else:
                self.status = 'na'
                self.is_expired = False
        return res

    def preview_document(self):
        self.ensure_one()
        action = {
            'type': "ir.actions.act_url",
            'target': "_blank",
            'url': '/documents/content/preview/%s' % self.id
        }
        return action

    def name_get(self):
        result = []
        for rec in self:
            rec_name = ""

            rec_name = ''
            if rec.document_type_id:
                if rec.document_type_id.abbreviation:
                    rec_name += rec.document_type_id.abbreviation
                else:
                    rec_name += rec.document_type_id.name
            if rec.partner_id:
                if rec.partner_id.abbreviation and rec.document_type_id.meta_data_template in [
                    'Commercial Registration (CR) Application', 'Commercial License', 'Establishment Card']:
                    rec_name += ' - ' + rec.partner_id.abbreviation
                else:
                    rec_name += ' - ' + rec.partner_id.name
            if rec.expiry_date:
                rec_name += ' - ' + str(rec.expiry_date)
            if rec.document_type_name == 'Proposal':
                rec_name += ' - ' + 'v%s' % rec.version
            result.append((rec.id, rec_name))
        return result

    # @api.model
    # def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
    #     args = args or []
    #     if operator == 'ilike' and not (name or '').strip():
    #         domain = []
    #     else:
    #         domain = ['|', '|', '|', ('name', operator, name), ('document_type_id.name', operator, name),
    #                   ('expiry_date', operator, name), ('partner_id.name', operator, name)]
    #     rec = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
    #     return models.lazy_name_get(self.browse(rec).with_user(name_get_uid))

    def notify_renewal(self):
        for rec in self.search([]):
            if rec.expiry_date and rec.reminder_for_renewal:
                days = (rec.expiry_date - date.today()).days
                template_obj = self.env['mail.mail']
                receiver_email = rec.owner_id.partner_id.email
                if days <= 30 and days > 0:
                    template_data = {
                        'subject': 'Your Document %s is expiring soon' % (rec.document_number),
                        'body_html': """
                                <p>Hello %s,<p>
                                Your document %s is expiring in %s days. Please renew it as soon as possible. <br/><br/>

                                Thank you,
                                <br/>
                                --
                                Administrator""" % (
                            rec.owner_id.name, rec.document_number, days),
                        'email_from': 'admin@example.com',
                        'email_to': receiver_email or '',
                        'record_name': rec.name,
                    }
                    template_id = template_obj.create(template_data)
                    template_obj.send(template_id)
                if days < 0:
                    template_data = {
                        'subject': 'Your Document %s has expired' % (rec.document_number),
                        'body_html': """
                                <p>Hello %s,<p>
                                Your document %s has expired. Please renew it as soon as possible <br/><br/>

                                Thank you,
                                <br/>
                                --
                                Administrator""" % (
                            rec.owner_id.name, rec.document_number),
                        'email_from': 'admin@example.com',
                        'email_to': receiver_email or '',
                        'record_name': rec.name,
                    }
                    template_id = template_obj.create(template_data)
                    template_obj.send(template_id)

    def update_expired_status(self):
        for rec in self.search([('expiry_date', '!=', False)]).filtered(lambda x: x.status in ['na', 'active']):
            if rec.expiry_date <= date.today():
                rec.write({'status': 'expired'})
                rec.is_expired = True
            else:
                rec.status = 'active'
                rec.is_expired = False

    def access_content(self):
        return super(DocumentsCustom, self).access_content()


class BusinessActivities(models.Model):
    _name = 'business.activities'
    _description = 'Business Activity'

    name = fields.Char('Name', translate=True)
    code = fields.Char('Code')


class CrTradeType(models.Model):
    _name = 'cr.trade.type'
    _description = 'CR Trade Type'

    name = fields.Char('Name')


class CrLegalForm(models.Model):
    _name = 'cr.legal.form'
    _description = 'CR Legal Form '

    name = fields.Char('Name')


class CommercialRegStatus(models.Model):
    _name = 'commercial.reg.status'
    _description = 'Commercial Registration Status'

    name = fields.Char('Name')


class EstSector(models.Model):
    _name = 'est.sector'
    _description = 'EST Sector'

    name = fields.Char('Name')
