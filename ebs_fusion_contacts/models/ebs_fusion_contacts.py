from lxml import etree
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

from datetime import date, datetime


class Contacts_Contacts(models.Model):
    _inherit = 'res.partner'
    _rec_name = 'name'

    def _default_stage_id(self):
        if self._context.get('display_stages_type'):
            stage_id = self.env['res.partner.state'].search(
                [('stages_type', '=', self._context.get('display_stages_type'))], order='sequence ASC', limit=1)
            if stage_id:
                return stage_id.id
        return False

    def get_client_relation_ec_record(self):
        if self.ec_document_id:
            print("client Relation")

    def get_passport_file(self):
        return [('document_type_name', '=', 'Passport')]

    def get_qid_file(self):
        return [('document_type_name', '=', 'QID')]

    def get_visa_file(self):
        document_type = self.env['ebs.document.type'].search([('name', '=', 'Visa')])
        return [('document_type_id', '=', document_type.id)]

    def _count_contract(self):
        for rec in self:
            proposal = self.env['ebs.crm.proposal'].search([('contact_id', '=', rec.id)])
            rec.contract_count = len(proposal)

    name = fields.Char(index=True, translate=True)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string="Gender")
    is_customer = fields.Boolean(string="Customer")
    is_vendor = fields.Boolean(string="Supplier")
    is_aoa_partner = fields.Boolean(string="AOA Partner")
    is_authorised_signatory = fields.Boolean(string="Authorised Signatory")
    is_dependent = fields.Boolean("IS Dependent")
    is_employee = fields.Boolean("IS Employee")
    is_aoa_finance_contact = fields.Boolean("Is AOA")
    is_general_secretary = fields.Boolean("Is General secretary")
    is_admin_manager = fields.Boolean("Is Admin Manager")
    is_liaison_officer = fields.Boolean("Is Liaison Officer")
    is_primary_contact = fields.Boolean('IS Primary Contact')
    is_legal_contact = fields.Boolean("Is Legal Contact")
    is_auditor_contact = fields.Boolean("Is Auditor Contact")
    is_corporate_banking_signatory = fields.Boolean('Is Corporate Banking Signatory')
    is_referral_contact = fields.Boolean("Referral Contact")
    is_authorised_representative = fields.Boolean("IS Authorised Representative")
    is_general_manager = fields.Boolean("Is General Manager")
    is_country_manager = fields.Boolean("Country Manager")
    is_manager_cr = fields.Boolean("Manager CR")
    is_manager_ec = fields.Boolean("Manager EC")
    is_manager_cl = fields.Boolean('Manager Cl')
    is_client_hr = fields.Boolean("Client HR")
    is_client_finance_ac = fields.Boolean("Client Finance/Accounts")
    dependent_id = fields.Many2one('res.partner', "Sponsor by")
    main_parent_id = fields.Many2one('res.partner', "Main Parent")
    arabic_name = fields.Char('Arabic Name')
    dependent_type_id = fields.Many2one('dependent.type', "Dependents Type")

    passport_details_ids = fields.One2many('ebs.passport.details', 'partner_id', string="Passport Details")
    ps_employee_id = fields.Many2one('hr.employee')
    ps_partner_id = fields.Many2one('res.partner')
    ps_passport_serial_no_id = fields.Many2one('documents.document', string="Passport File", domain=get_passport_file)
    ps_issue_date = fields.Date(string='PS Issue Date', related='ps_passport_serial_no_id.issue_date')
    ps_place_issue = fields.Char("Place of Issue", related='ps_passport_serial_no_id.place_of_issue')
    ps_place_birth = fields.Char("Place of Birth", related='ps_passport_serial_no_id.place_of_birth')
    ps_country_passport_id = fields.Many2one('res.country', string="Country of Passport",
                                             related='ps_passport_serial_no_id.country_passport_id')
    ps_citizenship_id = fields.Many2one('res.country', string="Citizenship",
                                        related='ps_passport_serial_no_id.nationality')
    ps_double_citizenship_ids = fields.Many2many('res.country', string="Double Country Citizenship",
                                                 related='ps_passport_serial_no_id.double_citizenship_ids')
    ps_passport_type = fields.Selection(
        [('regular', 'Regular'), ('special', 'Special'), ('diplomatic', 'Diplomatic'), ('service', 'Service')],
        string="Passport Type")

    ps_passport_name = fields.Char("PS Passport Name")
    ps_first_name = fields.Char("PS First Name", related='ps_passport_serial_no_id.passport_name')
    ps_middle_name = fields.Char("PS Middle Name", related='ps_passport_serial_no_id.middle_name')
    ps_last_name_1 = fields.Char("PS Last Name 1", related='ps_passport_serial_no_id.last_name_1')
    ps_last_name_2 = fields.Char("PS Last Name 2", related='ps_passport_serial_no_id.last_name_2')
    ps_father_name = fields.Char("PS Father Name", related='ps_passport_serial_no_id.father_name')

    ps_passport_ref_no = fields.Char("Passport Reference Number", related='ps_passport_serial_no_id.document_number')
    ps_expiry_date = fields.Date("PS Expiry Date", related='ps_passport_serial_no_id.expiry_date')
    ps_gender = fields.Selection([('male', 'Male'), ('female', 'Female')],
                                 string='PS Gender')
    ps_birth_date = fields.Date(string='PS Birth Date', related='ps_passport_serial_no_id.date_of_birth')
    ps_arabic_name = fields.Char(string='PS Arabic Name', related='ps_passport_serial_no_id.arabic_name')

    po_box = fields.Char(string='PO Box')

    social_twitter = fields.Char('Twitter Account')
    social_facebook = fields.Char('Facebook Account')
    social_github = fields.Char('GitHub Account')
    social_linkedin = fields.Char('LinkedIn Account')
    social_youtube = fields.Char('Youtube Account')
    social_instagram = fields.Char('Instagram Account')

    document_o2m = fields.One2many(
        comodel_name='documents.document',
        inverse_name='partner_id',
        string='Related Documents',
        required=False
    )

    document_legal_ids = fields.One2many(
        comodel_name='documents.document',
        inverse_name='partner_id',
        string='Legal Documents',
        required=False, domain=[('folder_id.name', '=', 'Legal')]
    )
    document_agreement_ids = fields.One2many(
        comodel_name='documents.document',
        inverse_name='partner_id',
        string='Legal Agreement Documents',
        required=False, domain=[('document_type_id.is_agreement', '=', True)]
    )
    document_foa_ids = fields.One2many(
        comodel_name='documents.document',
        inverse_name='partner_id',
        string='Legal FOA Documents',
        required=False, domain=[('document_type_id.meta_data_template', '=', 'Foreign AOA')]
    )
    document_cr_ids = fields.One2many(
        comodel_name='documents.document',
        inverse_name='partner_id',
        string='Legal CR Documents',
        required=False, domain=[('document_type_id.meta_data_template', '=', 'Foreign CR')]
    )
    document_poa_ids = fields.One2many(
        comodel_name='documents.document',
        inverse_name='partner_id',
        string='Legal POA Documents',
        required=False, domain=[('document_type_id.meta_data_template', '=', 'Foreign POA')]
    )

    document_license_ids = fields.One2many(
        comodel_name='documents.document',
        inverse_name='partner_id',
        string='License Documents',
        required=False, domain=[('document_type_id.is_license', '=', True)]
    )
    document_finance_ids = fields.One2many(
        comodel_name='documents.document',
        inverse_name='partner_id',
        string='Finance Audit Documents',
        required=False, domain=[('document_type_id.is_financial_audit', '=', True)]
    )
    nature_of_business = fields.Selection(string='Nature of business',
                                          selection=[('trading', 'Trading'), ('service', 'Service')])
    incorporation_date = fields.Date("Incorporation Date")
    expiry_date = fields.Date("Expiry Date")
    qid = fields.Char("QID")
    commercial_reg_no = fields.Char("Commercial Registration No", translate=True)
    establishment_card_no = fields.Char("Establishment Card No", translate=True)
    type_of_company = fields.Char("Type of Company")
    shareholder_ids = fields.Many2many('res.partner', 'res_partner_sharholder_rel', 'shareholder_id', 'partner_id',
                                       string='Client Shareholders')
    shareholder_o2m_ids = fields.One2many('share.holder', 'partner_id', string='Shareholders')
    articles_of_association_file = fields.Many2one('documents.document', string='Articles of Association File')
    amendments_articles_of_association_file = fields.Many2one('documents.document',
                                                              string='Amendments Articles of Association')
    shareholders_agreement_file = fields.Many2one('documents.document', string='Shareholders Agreement')
    service_agreement_file = fields.Many2one('documents.document', string='Service Agreement')
    loan_agreement_file = fields.Many2one('documents.document', string='Loan Agreement')
    other_agreement_file = fields.Many2one('documents.document', string='Other Agreement File')
    local_power_of_attorney_file = fields.Many2one('documents.document', string='Local Power of Attorney')
    general_assembly_resolution_file = fields.Many2one('documents.document', string='General Assembly Resolution')
    annual_general_assembly_resolution_file = fields.Many2one('documents.document',
                                                              string='Annual General Assembly Resolution')
    special_license_detail_id = fields.Many2one('documents.document', string='Special Licence Detail')

    passport_no = fields.Char("Passport No.")
    qid_no = fields.Char("QID No")
    per = fields.Float('Percentage')
    company_managment_structure_ids = fields.One2many('company.managment.structure', 'partner_id',
                                                      "Company Management Structures")
    company_mgt_structure_ids = fields.Many2many('res.partner', 'res_partner_company_mgt_structure',
                                                 'company_mgt_structure_ids', 'partner_id',
                                                 "Company Managment Structure")

    # Corporate licences

    authorised_signatory_ids = fields.Many2many('res.partner', 'res_partner_authorised_signatory',
                                                'authorised_signatory_ids', 'partner_id', string="Authorised Signatory")
    authorised_signatory_trade_license_ids = fields.Many2many('res.partner',
                                                              'res_partner_trade_license_authorised_signatory',
                                                              'authorised_signatory_trade_license_ids', 'partner_id',
                                                              string="Authorised Signatory Trade Licence")

    authorised_representative_id = fields.One2many('authorised.representative', 'partner_id',
                                                   string="Authorised Representatives")
    ec_authorised_signatory_ids = fields.Many2many('res.partner', 'res_partner_ec_authorised_signatory',
                                                   'ec_authorised_signatory_ids', string="Authorised Signatory EC")
    cr_authorised_signatory_ids = fields.Many2many('res.partner', 'res_partner_cr_authorised_signatory',
                                                   'cr_authorised_signatory_ids', string="Authorised Signatory CR")

    trade_name = fields.Char("Trade Name")
    creation_date = fields.Date("Creation Date")
    legal_form = fields.Many2one('cr.legal.form', string="Legal Form")
    commercial_reg_status = fields.Selection([('active', 'Active'), ('inactive', 'Inactive')],
                                             string='Commercial Reg.Status')
    no_of_branches = fields.Integer("No.of Branches")
    tax_reg_no = fields.Char("Tax Reg.No")

    capital = fields.Integer("Capital")
    firm_nationality_id = fields.Many2one('res.country', "Firm Nationality")
    res_state_id = fields.Many2one('res.partner.state', string="Stages",
                                   default=lambda self: self._default_stage_id())  #
    state = fields.Char("state")

    residency_permit_ids = fields.One2many('ebs.residency.permit', 'partner_id', string="QID")
    qid_partner_id = fields.Many2one('res.partner', string="Dependent")
    qid_residency_id = fields.Many2one('documents.document', string="QID File",
                                       domain=[('document_type_name', '=', 'QID')])
    qid_occupation = fields.Many2one('hr.job', string="Job Title", related='qid_residency_id.job_title')
    qid_residency_type = fields.Selection(
        [('entry', 'Entry Visas'), ('work', 'Work Residence Permit'), ('id', 'ID Cards'),
         ('family', 'Family Residence Visa'), ('exit', 'Exit Permit'),
         ('consular', 'Consular Services')],
        string="Residency type", default='entry')
    qid_sponsor_name = fields.Many2one(string="Sponsor Name", related='qid_residency_id.sponsor_name')
    qid_sponsor_id = fields.Char("Sponsor ID", related='qid_residency_id.sponsor_id')
    qid_country_of_passport = fields.Many2one('res.country', string='QID Country',
                                              related='qid_residency_id.country_passport_id')
    qid_text = fields.Text("QID Others/Comments", related='qid_residency_id.text')
    qid_visa_residence_permit = fields.Char("Visa/Residence Permit", related='qid_residency_id.visa_residence_permit')
    qid_visit_visa = fields.Char("Visit Visa", related='qid_residency_id.visit_visa')

    qid_first_name = fields.Char("QID First Name", related='qid_residency_id.qid_name')
    qid_arabic_name = fields.Char("QID Arabic Name", related='qid_residency_id.arabic_name')
    qid_middle_name = fields.Char("QID Middle Name", related='qid_residency_id.middle_name')
    qid_last_name_1 = fields.Char("QID Last Name 1", related='qid_residency_id.last_name_1')
    qid_last_name_2 = fields.Char("QID Last Name 2", related='qid_residency_id.last_name_2')
    qid_father_name = fields.Char("QID Father Name", related='qid_residency_id.father_name')
    qid_passport_no = fields.Char("Passport", related='qid_residency_id.passport_id')

    qid_ref_no = fields.Char("QID Reference Number", related='qid_residency_id.document_number')
    qid_expiry_date = fields.Date("QID Expiry Date", related='qid_residency_id.expiry_date')
    qid_birth_date = fields.Date("QID Birth Date", related='qid_residency_id.date_of_birth')

    visa_file_id = fields.Many2one('documents.document', string="Visa File", domain=get_visa_file)
    visa_ref_no = fields.Char("Visa Reference Number")
    visa_expiry_date = fields.Date("Visa Expiry Date", related='visa_file_id.expiry_date')

    share_holder_structure_id = fields.One2many('share.holder.structure', 'partner_id', string="Share Holder Structure")
    profit_share_structure_id = fields.One2many('profit.share.structure', 'partner_id', string="Profit Share Structure")
    mgt_structure_id = fields.One2many('mgt.structure', 'partner_id', string="Management Structure")

    commercial_name = fields.Char("Commercial Name")
    company_type_id = fields.Many2one('company.type', "Company-Type")
    company_status_id = fields.Many2one('company.status', string="Company Status")
    trademark = fields.Binary("Trademark")
    share_capital = fields.Char("Share Capital")

    # incorporation_date all ready
    reg_doc_en_id = fields.Many2one('documents.document', "Commercial Registration Document English")
    reg_doc_ar_id = fields.Many2one('documents.document', "Commercial Registration Document Arabic")
    cr_contact_ids = fields.One2many('cr.contact', 'partner_id', "CR Contact")
    commercial_activity_ids = fields.Many2many('commercial.activity', string="Commercial Activity")
    sp_approvel_comm_activity_id = fields.Many2one('documents.document', "Special Approvel Commercial Activity")
    # special_license_detail_ids all ready o2m
    qtr_chm_com_ind_id = fields.Many2one('documents.document', "Qatar Chamber of comm Industry Details")
    civil_def_lic_detail_id = fields.Many2one('documents.document', "Civil Defense Licence Details")
    trade_lic_detail_id = fields.Many2one('documents.document', "Trade Licence Details")
    establishment_card_detail_id = fields.Many2one('documents.document', "Establishment Card Details")
    tax_card_detail_id = fields.Many2one('documents.document', "Tax Card Details")
    appointed_auditor_id = fields.Many2one('appointed.auditor', "Appointed Auditor")
    labour_quota_details = fields.Char("Client Labour Quota Details")
    labour_quota_app_no = fields.Char("Labour Quota Application No")
    labour_quota_vp_no = fields.Char("Labour Quota VP Number")
    labour_quota_app_date = fields.Date("Labour Quota Application Date")
    labour_quota_exp_date = fields.Date("Labour Quota Expiry Date")
    qcsw_appinted_agent = fields.Char("QCSW Appointed Agent")
    qcsw_expiry = fields.Date("QCSW")
    related_company_ids = fields.Many2many('res.company', string="Related Entities")
    related_companies = fields.Many2many(comodel_name='res.partner', relation='related_companies_rel',
                                         column1='partner_id',
                                         column2='company_ids', string="Working With")
    child_ids = fields.One2many('res.partner', 'parent_id', string='Contact', domain=[('address_type', 'in',
                                                                                       ['head_office', 'local_office',
                                                                                        'Work_sites',
                                                                                        "labor_accommodation",
                                                                                        "national_address"]),
                                                                                      ('active', '=',
                                                                                       True)])  # force "active_test" domain to bypass _search() override

    contact_child_ids = fields.Many2many('res.partner', 'client_primary_contact_rel', 'client_id', 'partner_id',
                                         string='Primary Contacts',
                                         domain=[('address_type', '=', False), ('active', '=', True)])
    secondary_contact_child_ids = fields.Many2many('res.partner', 'client_secondary_contact_rel', 'client_id',
                                                   'partner_id',
                                                   string='Secondary Contacts',
                                                   domain=[('address_type', '=', False), ('active', '=', True)])
    auditor_contact_child_ids = fields.Many2many('res.partner', 'client_auditor_contact_rel', 'client_id', 'partner_id',
                                                 string='Auditor Contacts',
                                                 domain=[('address_type', '=', False), ('active', '=', True)])
    signatory_contact_child_ids = fields.Many2many('res.partner', 'client_signatory_contact_rel', 'client_id',
                                                   'partner_id',
                                                   string='Signatory Contacts',
                                                   domain=[('address_type', '=', False), ('active', '=', True)])
    hr_contact_child_ids = fields.Many2many('res.partner', 'client_hr_contact_rel', 'client_id',
                                            'partner_id',
                                            string='HR Contacts',
                                            domain=[('address_type', '=', False), ('active', '=', True)])
    referred_by_ids = fields.Many2many(relation='referred_by',
                                       comodel_name='res.partner', column1='partner_id', column2='referred_by_ids',
                                       string="Referred by")
    emails_ids = fields.One2many('email.addresses', 'partner_id', string="Email Addresses")
    company_partner = fields.Boolean(compute='compute_company_partner', default=False, store=True,
                                     string='My Companies')

    # building_villa_pic  = fields.Bi
    building_villa_no = fields.Char("Unit")
    floor_room_no = fields.Char("Floor/room Number")
    zone_no = fields.Char("Zone Number")
    zone_name = fields.Char("Zone Name")
    zone_id = fields.Many2one('ebs.na.zone', "Zone")
    street_no = fields.Char("Street Number")
    street_name = fields.Many2one('ebs.na.street', "Street Name", domain="[('zone_id','=',zone_id)]")
    building_villa_name = fields.Many2one('ebs.na.building', "Building/Villa Name",
                                          domain="[('street_id','=',street_name)]")
    signage = fields.Many2one('documents.document', string='Signage')
    blue_signage_zone_no = fields.Char("Blue Signage Zone No.")
    blue_signage_street_no = fields.Char("Blue Signage street No.")
    blue_signage_building_no = fields.Char("Blue Signage Building No.")
    building_villa_photo = fields.Many2one('documents.document', string='Building/Villa Photo')
    client_stamp = fields.Many2one('documents.document', string='Client Stamp')
    picture_with_the_signage = fields.Many2one('documents.document',
                                               string='Picture with the Signage in Building/Villa')
    office_drawing = fields.Many2one('documents.document', string='Office Drawing')
    building_villa_drawing_locating_office = fields.Many2one('documents.document',
                                                             string='Building/Villa drawing locating the office')
    lease_agreement_copy = fields.Many2one('documents.document', string='Lease Agreement Copy')
    kahramaa = fields.Char(string='Kahramaa')
    dependent_work_ids = fields.One2many('ebs.dependent.work', 'partner_id', string="Dependent Work")
    document_expiring_count = fields.Integer("Expiring Document", compute='_compute_expiring_document_count')
    document_expired_count = fields.Integer("Expired Document", compute='_compute_expired_document_count')
    labour_quota_details_ids = fields.One2many('labour.quota.details', 'partner_id', string='Labour Quota Details')
    qc_single_window_facility_ids = fields.One2many('qc.single.window.facility', 'partner_id',
                                                    string='Qatar Customs Single Window Facility')
    description = fields.Text(string='Other/Comments')
    commercial_letterhead = fields.Many2one('documents.document', string='Commercial Letterhead')
    letterhead_file = fields.Binary('Letterhead')
    corporate_stamp = fields.Many2one('documents.document', string='Corporate Stamp')
    corporate_logo = fields.Many2one('documents.document', string='Corporate Logo')
    home_country_contact = fields.Char(string='Home Country Contact')
    is_chairman = fields.Boolean(string='Chairman')
    is_ceo = fields.Boolean(string='CEO')
    is_cfo = fields.Boolean(string='CFO')
    is_clo = fields.Boolean(string='CLO')
    is_chro = fields.Boolean(string='CHRO')
    is_cmo = fields.Boolean(string='CMO')
    is_board_member = fields.Boolean('Is Board Member')
    tax_card_ids = fields.One2many('res.partner.tax.card', 'partner_id', string='Tax Card Number')
    kanban_view_name = fields.Char(compute='_compute_kanban_view_name', store=True, index=True)
    bank_details_ids = fields.One2many('res.partner.bank', 'client_id', string="Bank Details")
    legal_general_other_info = fields.Text('Other Information')
    primary_contact_ids = fields.One2many('res.partner', 'parent_id', 'Primary Client Contacts',
                                          compute='compute_key_contact_ids')
    key_contact_ids = fields.One2many('res.partner', 'parent_id', 'Key Client Contacts',
                                      compute='compute_key_contact_ids')
    board_contact_ids = fields.One2many('res.partner', 'parent_id', 'Board Members',
                                        compute='compute_key_contact_ids')
    shareholder_contact_ids = fields.Many2many('res.partner', 'client_shareholder_contact_rel', 'client_id',
                                               'shareholder_id', string="Contact Shareholders",
                                               domain=[('address_type', '=', False), ('active', '=', True)])
    head_office_contact_id = fields.Many2one('res.partner', 'Head Office Contact',
                                             compute='compute_key_contact_ids')
    head_office_phone = fields.Char(related='head_office_contact_id.phone',
                                    string='Phone Number (Landline - Head Office)')
    head_office_mobile = fields.Char(related='head_office_contact_id.mobile',
                                     string='Phone Number (Mobile - Head Office)')
    head_office_street = fields.Char(related='head_office_contact_id.street',
                                     string='Street (Head Office)')
    head_office_unit = fields.Char(related='head_office_contact_id.building_villa_no',
                                   string='Unit (Head Office)')
    head_office_city = fields.Char(related='head_office_contact_id.city',
                                   string='City (Head Office)')
    head_office_country = fields.Many2one(related='head_office_contact_id.country_id',
                                          string='Country (Head Office)')
    legal_docs_comment = fields.Text('Comments')
    aoa_shareholder_ids = fields.One2many(
        comodel_name='aoa.shareholder',
        inverse_name='partner_id',
        string='AOA Shareholder Structure',
        required=False,
    )
    aoa_profit_share_ids = fields.One2many(
        comodel_name='aoa.profit.share',
        inverse_name='partner_id',
        string='AOA Profit Share Structure',
        required=False,
    )
    tender_count = fields.Integer("Tenders", compute='_compute_tender_count')
    tender_ids = fields.Many2many(comodel_name='crm.lead', string='Tenders', compute='compute_tenders', readonly=1)
    product_ids = fields.One2many('product.template', 'partner_id', compute='compute_products', readonly=1)
    relation_with_dependent = fields.Selection([('Wife', 'Wife'), ('Child', 'Child')], string='Relation with Dependant',
                                               default='Wife')
    first_name = fields.Char("First Name", required=False)
    middel_name = fields.Char("Middle Name", required=False)
    last_name = fields.Char("Last Name", required=False)
    dob = fields.Date("Date of Birth", compute='compute_contact_dob_nationality', store=True)
    nationality_id = fields.Many2one('res.country', string='Nationality', compute='compute_contact_dob_nationality',
                                     store=True)
    infotech_user_ids = fields.Many2many('res.users', string='Users', compute='compute_user_ids', readonly=1)
    accounting_contact_ids = fields.Many2many('res.partner', 'client_accountant_contact_rel', 'client_id',
                                              'accountant_id', string="Accounting Contacts",
                                              domain=[('address_type', '=', False), ('active', '=', True)])
    employee_ids = fields.Many2many('hr.employee')
    permission = fields.Selection([
        ('approver', 'Approver'),
        ('requester', 'Requester'),
    ], string="Permission")
    percentage = fields.Float('Percentage')
    client_state = fields.Selection([('draft', 'Draft'),
                                     ('active', 'Active'),
                                     ('under_review', 'Under Process'),
                                     ('cancelled', 'Cancelled (CR cancelled or TL cancelled)'),
                                     ('closed', 'Closed / Archived (closure process has been completed)'),
                                     ('for_liquidation', 'For Liquidation'),
                                     ('under_liquidation', 'Under Liquidation'),
                                     ('st_out_under_process', 'Share Transferred Out (ST-Out) - Under Process'),
                                     ('st_out_completed', 'Share Transferred Out (ST-Out) - Completed'),
                                     ('for_court_closure', 'For Court Closure'),
                                     ('for_closure', 'For Closure'),
                                     ('with_problem', 'With Problem / Issue')],
                                    string='Status', default='draft')
    contact_state = fields.Selection([('draft', 'Draft'),
                                      ('under_review', 'Under Process'),
                                      ('active', 'Active'),
                                      ('archived', 'Archived')],
                                     string='Contact Status', default='draft')
    commercial_license_no = fields.Char(string='Commercial License No.')
    country_origin_id = fields.Many2one('res.country', string='Country Of Origin')
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict',
                               domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    email = fields.Char(translate=True)
    phone = fields.Char(translate=True)
    mobile = fields.Char(translate=True)
    qid_resident = fields.Boolean('QID Resident')
    cr_partner_ids = fields.Many2many('res.partner', related='cr_document_id.cr_partner_ids')
    cr_manager_ids = fields.Many2many('res.partner', related='cr_document_id.cr_managers_ids')
    cr_activity_ids = fields.Many2many('business.activities', related='cr_document_id.cr_business_activities_ids')
    ec_manager_ids = fields.Many2many('res.partner', related='ec_document_id.cr_authorizers_ids')
    cl_manager_ids = fields.Many2one('res.partner', related='cl_document_id.cl_partner_id')
    cr_document_id = fields.Many2one('documents.document', string="Commercial Registration",
                                     domain="[('document_type_name', '=', 'Commercial Registration (CR) Application'), ('partner_id', 'in', [False,id])]")
    new_expiry_date = fields.Date(related='cr_document_id.expiry_date', string="CR Expiry Date")
    new_issue_date = fields.Date(related='cr_document_id.issue_date', string="CR Issue Date")
    cr_tax_reg_no = fields.Char(related='cr_document_id.cr_tax_reg_no')
    cr_trade_name = fields.Char(related='cr_document_id.cr_trade_name')
    cr_arabic_name = fields.Char(related='cr_document_id.arabic_name', string="CR Arabic Name")
    cr_creation_date = fields.Date(related='cr_document_id.cr_creation_date', string="CR Creation Date")
    cr_legal_form = fields.Many2one('cr.legal.form', 'Legal CR Form', related='cr_document_id.cr_legal_form')
    cr_capital = fields.Float(related='cr_document_id.cr_capital', string="CR Capital")
    cr_reg_status = fields.Many2one('commercial.reg.status', 'Commercial Reg. status',
                                    related='cr_document_id.cr_reg_status')
    cr_no_brances = fields.Integer(related='cr_document_id.cr_no_brances', string="Cr No. Of Brances")
    cr_nationality = fields.Many2one('res.country', string="CR Nationality", related='cr_document_id.nationality')
    cr_doc_no = fields.Char(string="Commercial Reg. No.", related='cr_document_id.cr_reg_no')
    cl_document_id = fields.Many2one('documents.document', string="Commercial License",
                                     domain="[('document_type_name', '=', 'Commercial License'), ('partner_id', 'in', [False,id])]")
    child_national_ids = fields.Many2many('res.partner', string='National Address',
                                          related='cl_document_id.child_national_ids')
    cl_document_o2m = fields.Many2many('documents.document', string="Documents", related='cl_document_id.document_o2m')
    aoa_document_id = fields.Many2one('documents.document', string="Article of Association",
                                      domain="[('document_type_name', '=', 'articles of association'), ('partner_id', '=',id)]")
    financial_year = fields.Date('Financial Year', related='aoa_document_id.financial_year')
    financial_link_partner = fields.Many2one('res.partner', 'Financial Partner',
                                             related='aoa_document_id.financial_link_partner')
    general_manager = fields.Many2one('res.partner', 'General Manager', related='aoa_document_id.general_manager')
    general_secretary = fields.Many2one('res.partner', 'General Secretary', related='aoa_document_id.general_secretary')
    admin_manager = fields.Many2one('res.partner', 'Administration Manager', related='aoa_document_id.admin_manager')
    banking_signatory = fields.Many2one('res.partner', 'Banking Signatory', related='aoa_document_id.banking_signatory')
    liaison_officer = fields.Many2one('res.partner', 'Liaison Officer', related='aoa_document_id.liaison_officer')
    financial_day = fields.Integer('Day', related='aoa_document_id.financial_day', default=1)
    financial_month = fields.Selection(
        [('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'), ('5', 'May'),
         ('6', 'June'), ('7', 'July'), ('8', 'August'), ('9', 'September'),
         ('10', 'October'), ('11', 'November'), ('12', 'December')],
        string='Financial Month')
    aoa_shareholder_contact_ids = fields.Many2many('res.partner', string="AOA Shareholders",
                                                   domain=[('address_type', '=', False), ('active', '=', True)],
                                                   related='aoa_document_id.aoa_partner_ids')
    aoa_issue_date = fields.Date(related='aoa_document_id.issue_date', string="AOA Issue Date")
    aoa_expiry_date = fields.Date(related='aoa_document_id.expiry_date', string="AOA Expiry Date")
    cl_expiry_date = fields.Date(related='cl_document_id.expiry_date', string="CL Expiry Date")
    cl_issue_date = fields.Date(related='cl_document_id.issue_date', string="CL Issue Date")
    cl_arabic_name = fields.Char(related='cl_document_id.arabic_name', string="Cl Arabic Name")
    cl_name = fields.Char(related='cl_document_id.cl_name', string="CL Name")
    cl_license_number = fields.Char(related='cl_document_id.license_number')
    cl_partner_id = fields.Many2one('res.partner', string='Manager in charge', related='cl_document_id.cl_partner_id')
    cl_zone_id = fields.Many2one('ebs.na.zone', string="CL Zone", related='cl_document_id.zone_id')
    cl_street = fields.Many2one('ebs.na.street', string="CL Street", related='cl_document_id.street')
    cl_building = fields.Many2one('ebs.na.building', string="CL Building", related='cl_document_id.building')
    cl_unit = fields.Char('CL Unit', related='cl_document_id.unit')
    ec_document_id = fields.Many2one('documents.document', string="Establishment Card",
                                     domain="[('document_type_name', '=', 'Establishment Card'), ('partner_id', 'in', [False,id])]")
    ec_expiry_date = fields.Date(related='ec_document_id.expiry_date', string="EC Expiry Date")
    ec_issue_date = fields.Date(related='ec_document_id.issue_date', string="EC Issue Date")
    cr_status = fields.Selection(related='cr_document_id.status', string="CR Status")
    cl_status = fields.Selection(related='cl_document_id.status', string="CL Status")
    aoa_status = fields.Selection(related='aoa_document_id.status', string="AOA Status")
    ec_status = fields.Selection(related='ec_document_id.status', string="EC Status")
    est_id = fields.Char(related='ec_document_id.est_id')
    est_name_en = fields.Char(related='ec_document_id.est_name_en')
    est_arabic_name = fields.Char(related='ec_document_id.arabic_name', string="ES Arabic Name")
    est_sector = fields.Many2one('est.sector', 'Sector', related='ec_document_id.est_sector')
    est_first_issue = fields.Date(related='ec_document_id.est_first_issue')
    cl_manager_status = fields.Selection(related='cl_manager_ids.contact_state', string="CL Manager Status ")
    is_doc_active = fields.Boolean(compute='compute_is_doc_active')
    is_qid_active = fields.Boolean(compute='compute_is_doc_active')
    abbreviation = fields.Char(string="Abbreviation")
    is_branch = fields.Boolean(string="Branch")
    is_form_submit = fields.Boolean(string="Form Submit")
    is_summary = fields.Boolean(string="Summary")
    is_user_information = fields.Boolean(string="User Information")
    is_commercial_registration = fields.Boolean(string="IS Commercial Registration")
    is_commercial_license = fields.Boolean(string="IS Commercial License")
    is_establishment_card = fields.Boolean(string="IS Establishment Card")
    is_national_address = fields.Boolean(string="IS National Address")
    is_services_submit = fields.Boolean(string="Is Services Submit")
    client_parent_id = fields.Many2one('res.partner', string="Parent",
                                       domain="[('is_customer', '=', True), ('is_company', '=', True), ('parent_id', '=', False)]")
    branch_ids = fields.One2many('res.partner', 'client_parent_id', string="Branches")
    show_branch = fields.Boolean('Show Branch', compute='show_branches')
    last_client_id = fields.Many2one('res.partner', string="Last Client")
    cr_partner_is_client = fields.Boolean('Is Client')
    client_contact_rel_ids = fields.One2many('ebs.client.contact', 'partner_id', string='Client Relation')
    partner_permission = fields.Selection([('approver', 'Approver'), ('requester', 'Requester')], string="Permission",
                                          default=False, compute='compute_partner_permission')
    partner_percentage = fields.Float(string='Partner Percentage', compute='compute_partner_percentage')
    partner_profit_share = fields.Float('Profit Share', related='client_contact_rel_ids.profit_share')
    partner_email = fields.Char(string="Partner Email", default=False, compute='compute_partner_email')
    website_error_msg = fields.Text(string="Error Message")
    is_newly_create = fields.Boolean(string="Is newly created")
    is_referral = fields.Boolean(string="Is Referral")
    referral_note = fields.Text(string="Referral Note")
    tax_id = fields.Many2one('account.tax', string="Tax", domain="[('type_tax_use','=','purchase')]")
    legal_case_ids = fields.One2many('ebs.legal.case', 'partner_id', string="Legal Case")
    date_initiation = fields.Date('Date of initiation', related='aoa_document_id.date_initiation')
    period = fields.Integer('Period in Years', related='aoa_document_id.period')
    date_term = fields.Date('Date of Term', related='aoa_document_id.date_term')
    contract_count = fields.Integer('Contract count', compute='_count_contract')

    # business Related Fields
    business_sector_id = fields.Many2one('ebs.business.sector', string="Business Sector")
    company_business_type = fields.Selection([('services', 'Services'),
                                              ('trading', 'Trading'),
                                              ('other', 'Other')], string="Company Business Type")
    other_business_type = fields.Char('Other Business Type')
    conversion_rate_ids = fields.One2many('ebs.client.conversion.rate', 'partner_id', string='Custom conversion Rate')

    # Operation Tab
    # Using qcsw_expiry for qcsw date field
    mof_username = fields.Char('Username')
    mof_password = fields.Char('Password')
    cr_eng_link = fields.Char('English Printing Link')
    cr_ar_link = fields.Char('Arabic Printing Link')
    tl_link = fields.Char('Printing Link')
    client_ec_rel_ids = fields.One2many('ebs.client.contact', 'client_id', string='Client Relation EC',
                                        domain=[('is_manager_ec', '=', True)])
    account_manager_id = fields.Many2one(comodel_name='hr.employee',
                                         string='Account Manager',
                                         domain=[('employee_type', '=', 'fusion_employee')])
    client_account_manager_id = fields.Many2one(comodel_name='res.users', string='Account Manager')
    has_grading_system = fields.Boolean('Has Grading System')
    related_employee_id = fields.Many2one('hr.employee', compute='compute_related_employee', string='Related Employee')
    subcontractors_ids = fields.One2many(comodel_name='ebs.supplier.subcontractor', inverse_name='partner_id',
                                         string='Subcontractor')

    _sql_constraints = [
        ('abbreviation_unique', 'unique (abbreviation)', "A Client With This Abbreviation Already Exists."),
    ]

    def compute_related_employee(self):
        for rec in self:
            rec.related_employee_id = self.env['hr.employee'].search([('user_partner_id', '=', rec.id)], limit=1)

    def update_client_contact_relation(self, datas):
        for rec in self:
            for data in datas:
                field_ids = getattr(rec, data)
                for partner in field_ids:
                    available_client_line = partner.client_contact_rel_ids.filtered(
                        lambda o: o.client_id.id == rec.id)
                    if available_client_line and not getattr(available_client_line, datas[data]):
                        available_client_line.write({datas[data]: True})
                    elif not available_client_line:
                        update_dict = ({'client_id': rec.id,
                                        'permission': partner.permission,
                                        datas[data]: True})
                        partner.write({'client_contact_rel_ids': [(0, 0, update_dict)]})
                    else:
                        continue

    @api.depends('branch_ids')
    def show_branches(self):
        if len(self.branch_ids) > 0:
            self.show_branch = True
        else:
            self.show_branch = False

    @api.depends('document_o2m')
    def compute_aoa_doc_data(self):
        for rec in self:
            aoa_doc_id = rec.document_o2m.filtered(lambda o: o.document_type_name == 'articles of association')
            if aoa_doc_id:
                rec.date_initiation = aoa_doc_id[0].date_initiation
                rec.period = aoa_doc_id[0].period
                rec.date_term = aoa_doc_id[0].date_term
            else:
                rec.date_initiation = False
                rec.period = False
                rec.date_term = False

    def open_client_relation_details(self):
        action = self.env.ref('ebs_fusion_contacts.action_client_contact').read([])[0]
        action['domain'] = [('client_id', '=', self.id)]
        action['context'] = {'create': 0, 'edit': 0, 'delete': 0}
        return action

    @api.model
    def default_get(self, fields):
        res = super(Contacts_Contacts, self).default_get(fields)
        if self._context.get('clients_review'):
            res.update({'client_contact_rel_ids': [
                (0, 0, {
                    'client_id': self._context.get('active_id') or self._context.get('partner_id'),
                    self._context.get('role'): True
                })]})

        return res

    @api.onchange('client_state')
    def onchange_client_state(self):
        for rec in self:
            if rec.client_state == 'active':
                self.check_client_doc_status()
                if any(contact.contact_state != 'active' for contact in rec.contact_child_ids):
                    raise UserError(_('Please Activate All Contacts.'))

    @api.depends('ps_passport_serial_no_id', 'qid_residency_id')
    def compute_contact_dob_nationality(self):
        for rec in self:
            rec.dob = rec.ps_passport_serial_no_id.date_of_birth or rec.qid_residency_id.date_of_birth
            rec.nationality_id = rec.ps_passport_serial_no_id.country_passport_id.id or rec.qid_residency_id.country_passport_id.id

    def action_see_client_documents(self):
        action = self.env.ref('documents.document_action').read([])[0]
        action['domain'] = [('partner_id', '=', self.id)]
        return action

    @api.onchange('client_parent_id')
    def onchange_client_parent_id(self):
        for rec in self:
            if rec.is_branch == True:
                rec.cr_document_id = rec.client_parent_id.cr_document_id.id

    @api.depends('client_contact_rel_ids')
    def compute_partner_permission(self):
        # compute method to show permission for same contact and different client
        for rec in self:
            if self._context.get('clients_review'):
                line = rec.client_contact_rel_ids.filtered(
                    lambda o: o.client_id.id in [self._context.get('active_id') or self._context.get('partner_id')])
                if line:
                    rec.partner_permission = line[0].permission
                else:
                    rec.partner_permission = False
            else:
                rec.partner_permission = False

    @api.depends('client_contact_rel_ids')
    def compute_partner_email(self):
        # compute method to show permission for same contact and different client
        for rec in self:
            if self._context.get('clients_review'):
                line = rec._origin.client_contact_rel_ids.filtered(
                    lambda o: o.client_id.id in [self._context.get('active_id') or self._context.get('partner_id')])
                if line:
                    rec.partner_email = line[0].email
                else:
                    rec.partner_email = False
            else:
                rec.partner_email = False

    @api.depends('client_contact_rel_ids')
    def compute_partner_percentage(self):
        # compute method to show percentage for same contact and different client
        for rec in self:
            if self._context.get('clients_review'):
                line = rec._origin.client_contact_rel_ids.filtered(
                    lambda o: o.client_id.id in [self._context.get('active_id') or self._context.get('partner_id')])
                if line:
                    rec.partner_percentage = line[0].percentage
                else:
                    rec.partner_percentage = False
            else:
                rec.partner_percentage = False

    @api.depends('client_contact_rel_ids')
    def compute_partner_profit_share(self):
        # compute method to show profit share for same contact and different client
        for rec in self:
            if self._context.get('clients_review'):
                line = rec._origin.client_contact_rel_ids.filtered(
                    lambda o: o.client_id.id in [self._context.get('active_id') or self._context.get('partner_id')])
                if line:
                    rec.partner_profit_share = line[0].profit_share
                else:
                    rec.partner_profit_share = False
            else:
                rec.partner_profit_share = False

    def name_get(self):
        names = []
        for record in self:
            names.append((record.id, "%s" % (record.name)))
        return names

    def preview_partner(self):
        return {
            'view_id': self.env.ref('base.view_partner_form').id,
            'view_mode': 'form',
            'res_model': 'res.partner',
            'type': 'ir.actions.act_window',
            'context': {'create': False, 'edit': False},
            'name': _('Contact'),
            'res_id': self.id
        }

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            duplicate_name_ids = self.search([('name', 'ilike', self.name)]) - self
            if duplicate_name_ids:
                warning = {
                    'title': _('Warning'),
                    'message':
                        _('Client/Contact Already Exists.')}
                return {'warning': warning}

    @api.onchange('cr_partner_ids')
    def cr_partners(self):
        print("========", self._origin.cr_partner_ids)
        for partner in self._origin.cr_partner_ids:
            partner.is_shareholder = True
            if partner.cr_partner_is_client == True and partner.company_type == 'company':
                partner.is_customer = True
                partner.parent_id = False

    @api.depends('ps_passport_serial_no_id', 'qid_residency_id', 'qid_resident')
    def compute_is_doc_active(self):
        for rec in self:
            if rec.ps_passport_serial_no_id.status == 'active':
                rec.is_doc_active = True
            else:
                rec.is_doc_active = False
            if rec.qid_residency_id.status == 'active':
                rec.is_qid_active = True
            else:
                rec.is_qid_active = False

    def active_client(self):
        self.ensure_one()
        self.check_client_doc_status()
        self.client_state = 'active'

    def check_client_doc_status(self):
        empty_doc = []
        status_list = []
        if not self.cr_document_id:
            empty_doc.append('Commercial Registration ')
        if not self.cl_document_id:
            empty_doc.append('Trade License')
        if not self.ec_document_id:
            empty_doc.append('Establishment Card')
        if not self.aoa_document_id:
            empty_doc.append('Article of Association')
        if empty_doc:
            raise UserError(_('Please Create or Set %s Document ' % (", ".join(empty_doc))))
        if self.cr_status != 'active':
            status_list.append('Commercial Registration')
        if self.cl_status != 'active':
            status_list.append('Trade License')
        if self.ec_status != 'active':
            status_list.append('Establishment Card')
        if self.aoa_status != 'active':
            status_list.append('Article of Association')
        if status_list:
            raise UserError(_('Please Activate %s Documents.' % (", ".join(status_list))))
        if any(contact.contact_state != 'active' for contact in self.contact_child_ids):
            raise UserError(_('Please Activate All Contacts.'))

    def inactive_client(self):
        self.ensure_one()
        self.client_state = 'under_review'

    def active_contact(self):
        self.ensure_one()
        if self.qid_resident == False and self.ps_passport_serial_no_id and self.ps_passport_serial_no_id.status != 'active':
            raise UserError(_('Please Activate Of Contact\'s Passport.'))
        if self.qid_resident == True and self.qid_residency_id and self.qid_residency_id.status != 'active':
            raise UserError(_('Please Activate Of Contact\'s QID.'))
        self.contact_state = 'active'

    def inactive_contact(self):
        self.ensure_one()
        self.contact_state = 'under_review'

    def active_cl_manager(self):
        self.ensure_one()
        if self.cl_manager_ids.qid_resident == False and self.cl_manager_ids.ps_passport_serial_no_id and self.cl_manager_ids.ps_passport_serial_no_id.status != 'active':
            raise UserError(_('Please Activate Of Contact\'s Passport.'))
        if self.cl_manager_ids.qid_resident == True and self.cl_manager_ids.qid_residency_id and self.cl_manager_ids.qid_residency_id.status != 'active':
            raise UserError(_('Please Activate Of Contact\'s QID.'))
        self.cl_manager_ids.contact_state = 'active'

    def inactive_cl_manager(self):
        self.ensure_one()
        self.cl_manager_ids.contact_state = 'under_review'

    def active_passport(self):
        self.ensure_one()
        if self.ps_passport_serial_no_id and self.ps_passport_serial_no_id.expiry_date and self.ps_passport_serial_no_id.expiry_date <= date.today():
            action = {
                'name': _('Warning'),
                'view_mode': 'form',
                'res_model': 'ebs.document.active.confirm',
                'view_id': self.env.ref('ebs_fusion_contacts.view_ebs_document_active_confirm_form').id,
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {
                    'default_document_id': self.ps_passport_serial_no_id.id,
                    'default_partner_id': self.id,
                    'default_field_name': 'is_doc_active'
                }
            }
            return action
        else:
            if self.ps_passport_serial_no_id:
                self.ps_passport_serial_no_id.write({'status': 'active'})
                self.is_doc_active = True

    def inactive_passport(self):
        self.ensure_one()
        self.ps_passport_serial_no_id.write({'status': 'na'})
        self.is_doc_active = False

    def active_qid(self):
        self.ensure_one()
        if self.qid_residency_id and self.qid_residency_id.expiry_date and self.qid_residency_id.expiry_date <= date.today():
            action = {
                'name': _('Warning'),
                'view_mode': 'form',
                'res_model': 'ebs.document.active.confirm',
                'view_id': self.env.ref('ebs_fusion_contacts.view_ebs_document_active_confirm_form').id,
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {
                    'default_document_id': self.qid_residency_id.id,
                    'default_partner_id': self.id,
                    'default_field_name': 'is_qid_active'
                }
            }
            return action
        else:
            if self.qid_residency_id:
                self.qid_residency_id.write({'status': 'active'})
                self.is_qid_active = True

    def inactive_qid(self):
        self.ensure_one()
        self.qid_residency_id.write({'status': 'na'})
        self.is_qid_active = False

    def active_cr(self):
        self.ensure_one()
        if any(partner.contact_state != 'active' for partner in self.cr_partner_ids):
            raise UserError(_('Please Activate All Partners In Commercial Registration (CR) Application Document.'))
        if any(manager.contact_state != 'active' for manager in self.cr_manager_ids):
            raise UserError(_('Please Activate All Managers In Commercial Registration (CR) Application Document.'))

        if self.cr_document_id and self.cr_document_id.expiry_date and self.cr_document_id.expiry_date <= date.today():
            action = {
                'name': _('Warning'),
                'view_mode': 'form',
                'res_model': 'ebs.document.active.confirm',
                'view_id': self.env.ref('ebs_fusion_contacts.view_ebs_document_active_confirm_form').id,
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {
                    'default_document_id': self.cr_document_id.id,
                    'default_partner_id': False,
                }
            }
            return action
        else:
            if self.cr_document_id:
                self.cr_document_id.write({'status': 'active'})

    def inactive_cr(self):
        self.ensure_one()
        self.cr_document_id.write({'status': 'na'})

    def active_cl(self):
        self.ensure_one()
        if self.cl_manager_ids.contact_state != 'active':
            raise UserError(_('Please Activate Manager In Charge In Commercial License Document.'))
        if self.cl_document_id and self.cl_document_id.expiry_date and self.cl_document_id.expiry_date <= date.today():
            action = {
                'name': _('Warning'),
                'view_mode': 'form',
                'res_model': 'ebs.document.active.confirm',
                'view_id': self.env.ref('ebs_fusion_contacts.view_ebs_document_active_confirm_form').id,
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {
                    'default_document_id': self.cl_document_id.id,
                    'default_partner_id': False,
                }
            }
            return action
        else:
            if self.cl_document_id:
                self.cl_document_id.write({'status': 'active'})

    def inactive_cl(self):
        self.ensure_one()
        self.cl_document_id.write({'status': 'na'})

    def active_aoa(self):
        self.ensure_one()
        if any(shareholder.contact_state != 'active' for shareholder in self.aoa_shareholder_contact_ids):
            raise UserError(_('Please Activate Shareholders In Article of Association Document.'))
        if self.aoa_document_id and self.aoa_document_id.expiry_date and self.aoa_document_id.expiry_date <= date.today():
            action = {
                'name': _('Warning'),
                'view_mode': 'form',
                'res_model': 'ebs.document.active.confirm',
                'view_id': self.env.ref('ebs_fusion_contacts.view_ebs_document_active_confirm_form').id,
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {
                    'default_document_id': self.aoa_document_id.id,
                    'default_partner_id': False,
                }
            }
            return action
        else:
            if self.aoa_document_id:
                self.aoa_document_id.write({'status': 'active'})

    def inactive_aoa(self):
        self.ensure_one()
        self.aoa_document_id.write({'status': 'na'})

    def active_ec(self):
        self.ensure_one()
        if any(authoriser.contact_state != 'active' for authoriser in self.ec_manager_ids):
            raise UserError(_('Please Activate All Authorisers In Establishment Card Document.'))

        if self.ec_document_id and self.ec_document_id.expiry_date and self.ec_document_id.expiry_date <= date.today():
            action = {
                'name': _('Warning'),
                'view_mode': 'form',
                'res_model': 'ebs.document.active.confirm',
                'view_id': self.env.ref('ebs_fusion_contacts.view_ebs_document_active_confirm_form').id,
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {
                    'default_document_id': self.ec_document_id.id,
                    'default_partner_id': False,
                }
            }
            return action
        else:
            if self.ec_document_id:
                self.ec_document_id.write({'status': 'active'})

    def inactive_ec(self):
        self.ensure_one()
        self.ec_document_id.write({'status': 'na'})

    @api.constrains('child_ids')
    def check_national_address_limit(self):
        for rec in self:
            national_address = rec.child_ids.filtered(
                lambda o: o.address_type == 'national_address' and o.type == 'other')
            if len(national_address) > 1:
                raise UserError(_('Client Can Have Only One National Address.'))

    def get_client_contact_rel_vals(self, client_id):
        # method to get available relation line vals from contact and client
        client_line = self.client_contact_rel_ids.filtered(
            lambda o: o.client_id.id == client_id.id)
        return {'email': client_line.email, 'permission': client_line.permission, 'percentage': client_line.percentage}

    @api.model
    def create(self, vals):
        res = super(Contacts_Contacts, self).create(vals)
        if self._context.get('clients_review') and self._context.get('clients_review') == True:
            res.ps_passport_serial_no_id.partner_id = res.id
            res.qid_residency_id.partner_id = res.id
            if not vals.get('is_branch'):
                res.cr_document_id.partner_id = res.id
            res.cl_document_id.partner_id = res.id
            res.ec_document_id.partner_id = res.id
            res.dependent_id = res.qid_residency_id.sponsor_name.id
        # Create client rel line if changes done from clients review form
        self.get_client_contact_rel(vals, res)
        if self._context.get('lead_id'):
            lead_id = self.env['crm.lead'].browse(self._context.get('lead_id'))
            lead_id.write({'partner_id': res.id})
            lead_id._onchange_partner_id()
            lead_id.onchange_contact_ids()

        return res

    def get_client_contact_rel(self, vals, client):
        # Create client rel lines for primary contact
        if vals.get('contact_child_ids') and not any(
                k in self._context for k in ("add_prmry_cntct", "rmv_prmry_cntct")):
            if vals.get('contact_child_ids')[0][0] == 4:
                partner = self.env['res.partner'].browse(vals.get('contact_child_ids')[0][1])
                available_client_line = partner.client_contact_rel_ids.filtered(lambda o: o.client_id.id == client.id)
                if available_client_line:
                    available_client_line.write(
                        {'is_primary_contact': True, 'permission': partner.permission})
                else:
                    partner.write({'client_contact_rel_ids': [(0, 0,
                                                               {'client_id': client.id, 'is_primary_contact': True,
                                                                'permission': partner.permission,
                                                                'percentage': partner.percentage,
                                                                'email': partner.email})]})

            if vals.get('contact_child_ids')[0][0] == 6:
                for partner_id in vals.get('contact_child_ids')[0][2]:
                    partner = self.env['res.partner'].browse(partner_id)
                    available_client_line = partner.client_contact_rel_ids.filtered(
                        lambda o: o.client_id.id == client.id)
                    if available_client_line:
                        available_client_line.write({'is_primary_contact': True, 'permission': partner.permission})
                    else:
                        partner.write({'client_contact_rel_ids': [(0, 0,
                                                                   {'client_id': client.id, 'is_primary_contact': True,
                                                                    'permission': partner.permission,
                                                                    'email': partner.email})]})
        # Create client rel line for seconadry contact
        if vals.get('secondary_contact_child_ids') and not any(
                k in self._context for k in ("add_scndr_cntct", "rmv_scndr_cntct")):
            if vals.get('secondary_contact_child_ids')[0][0] == 4:
                partner = self.env['res.partner'].browse(vals.get('secondary_contact_child_ids')[0][1])
                available_client_line = partner.client_contact_rel_ids.filtered(lambda o: o.client_id.id == client.id)
                if available_client_line:
                    available_client_line.write(
                        {'is_secondary_contact': True, 'permission': partner.permission})
                else:
                    partner.write({'client_contact_rel_ids': [(0, 0,
                                                               {'client_id': client.id, 'is_secondary_contact': True,
                                                                'permission': partner.permission,
                                                                'email': partner.email})]})

            if vals.get('secondary_contact_child_ids')[0][0] == 6:
                for partner_id in vals.get('secondary_contact_child_ids')[0][2]:
                    partner = self.env['res.partner'].browse(partner_id)
                    available_client_line = partner.client_contact_rel_ids.filtered(
                        lambda o: o.client_id.id == client.id)
                    if available_client_line:
                        available_client_line.write({'is_secondary_contact': True, 'permission': partner.permission})
                    else:
                        partner.write({'client_contact_rel_ids': [(0, 0,
                                                                   {'client_id': client.id,
                                                                    'is_secondary_contact': True,
                                                                    'permission': partner.permission,
                                                                    'email': partner.email})]})
        # Creating Client relation line Auditor contact
        if vals.get('auditor_contact_child_ids') and not any(
                k in self._context for k in ("add_auditor", "rmv_auditor")):
            if vals.get('auditor_contact_child_ids')[0][0] == 4:
                partner = self.env['res.partner'].browse(vals.get('auditor_contact_child_ids')[0][1])
                available_client_line = partner.client_contact_rel_ids.filtered(lambda o: o.client_id.id == client.id)
                if available_client_line:
                    available_client_line.write(
                        {'is_auditor_contact': True, 'permission': partner.permission})
                else:
                    partner.write({'client_contact_rel_ids': [(0, 0,
                                                               {'client_id': client.id, 'is_auditor_contact': True,
                                                                'permission': partner.permission,
                                                                'email': partner.email})]})

            if vals.get('auditor_contact_child_ids')[0][0] == 6:
                for partner_id in vals.get('auditor_contact_child_ids')[0][2]:
                    partner = self.env['res.partner'].browse(partner_id)
                    available_client_line = partner.client_contact_rel_ids.filtered(
                        lambda o: o.client_id.id == client.id)
                    if available_client_line:
                        available_client_line.write({'is_auditor_contact': True, 'permission': partner.permission})
                    else:
                        partner.write({'client_contact_rel_ids': [(0, 0,
                                                                   {'client_id': client.id, 'is_auditor_contact': True,
                                                                    'permission': partner.permission,
                                                                    'email': partner.email})]})
        # Creating Client relation line Signatory contact
        if vals.get('signatory_contact_child_ids') and not any(
                k in self._context for k in ("add_signatory", "rmv_signatory")):
            if vals.get('signatory_contact_child_ids')[0][0] == 4:
                partner = self.env['res.partner'].browse(vals.get('signatory_contact_child_ids')[0][1])
                available_client_line = partner.client_contact_rel_ids.filtered(lambda o: o.client_id.id == client.id)
                if available_client_line:
                    available_client_line.write(
                        {'is_corporate_banking_signatory': True, 'permission': partner.permission})
                else:
                    partner.write({'client_contact_rel_ids': [(0, 0,
                                                               {'client_id': client.id,
                                                                'is_corporate_banking_signatory': True,
                                                                'permission': partner.permission,
                                                                'email': partner.email})]})

            if vals.get('signatory_contact_child_ids')[0][0] == 6:
                for partner_id in vals.get('signatory_contact_child_ids')[0][2]:
                    partner = self.env['res.partner'].browse(partner_id)
                    available_client_line = partner.client_contact_rel_ids.filtered(
                        lambda o: o.client_id.id == client.id)
                    if available_client_line:
                        available_client_line.write(
                            {'is_corporate_banking_signatory': True, 'permission': partner.permission})
                    else:
                        partner.write({'client_contact_rel_ids': [(0, 0,
                                                                   {'client_id': client.id,
                                                                    'is_corporate_banking_signatory': True,
                                                                    'permission': partner.permission,
                                                                    'email': partner.email})]})
        if vals.get('hr_contact_child_ids') and not any(k in self._context for k in ("add_hr_cntct", "rmv_hr_cntct")):
            if vals.get('hr_contact_child_ids')[0][0] == 4:
                partner = self.env['res.partner'].browse(vals.get('hr_contact_child_ids')[0][1])
                available_client_line = partner.client_contact_rel_ids.filtered(lambda o: o.client_id.id == client.id)
                if available_client_line:
                    available_client_line.write(
                        {'is_hr_contact': True, 'permission': partner.permission})
                else:
                    partner.write({'client_contact_rel_ids': [(0, 0,
                                                               {'client_id': client.id, 'is_hr_contact': True,
                                                                'permission': partner.permission,
                                                                'email': partner.email})]})

            if vals.get('hr_contact_child_ids')[0][0] == 6:
                for partner_id in vals.get('hr_contact_child_ids')[0][2]:
                    partner = self.env['res.partner'].browse(partner_id)
                    available_client_line = partner.client_contact_rel_ids.filtered(
                        lambda o: o.client_id.id == client.id)
                    if available_client_line:
                        available_client_line.write({'is_hr_contact': True, 'permission': partner.permission})
                    else:
                        partner.write({'client_contact_rel_ids': [(0, 0,
                                                                   {'client_id': client.id, 'is_hr_contact': True,
                                                                    'permission': partner.permission,
                                                                    'email': partner.email})]})

        if vals.get('accounting_contact_ids') and not any(
                k in self._context for k in ("add_finance_cntct", "rmv_finance_cntct")):
            if vals.get('accounting_contact_ids')[0][0] == 4:
                partner = self.env['res.partner'].browse(vals.get('accounting_contact_ids')[0][1])
                available_client_line = partner.client_contact_rel_ids.filtered(lambda o: o.client_id.id == client.id)
                if available_client_line:
                    available_client_line.write(
                        {'is_client_finance_ac': True, 'permission': partner.permission})
                else:
                    partner.write({'client_contact_rel_ids': [(0, 0,
                                                               {'client_id': client.id, 'is_client_finance_ac': True,
                                                                'permission': partner.permission,
                                                                'email': partner.email})]})

            if vals.get('accounting_contact_ids')[0][0] == 6:
                for partner_id in vals.get('accounting_contact_ids')[0][2]:
                    partner = self.env['res.partner'].browse(partner_id)
                    available_client_line = partner.client_contact_rel_ids.filtered(
                        lambda o: o.client_id.id == client.id)
                    if available_client_line:
                        available_client_line.write({'is_client_finance_ac': True, 'permission': partner.permission})
                    else:
                        partner.write({'client_contact_rel_ids': [(0, 0,
                                                                   {'client_id': client.id,
                                                                    'is_client_finance_ac': True,
                                                                    'permission': partner.permission,
                                                                    'email': partner.email})]})

        if vals.get('shareholder_contact_ids') and not any(
                k in self._context for k in ("add_shareholder", "rmv_shareholder")):
            if vals.get('shareholder_contact_ids')[0][0] == 4:
                partner = self.env['res.partner'].browse(vals.get('shareholder_contact_ids')[0][1])
                available_client_line = partner.client_contact_rel_ids.filtered(lambda o: o.client_id.id == client.id)
                if available_client_line:
                    available_client_line.write(
                        {'is_shareholder': True, 'permission': partner.permission})
                else:
                    partner.write({'client_contact_rel_ids': [(0, 0,
                                                               {'client_id': client.id, 'is_shareholder': True,
                                                                'permission': partner.permission,
                                                                'percentage': partner.percentage,
                                                                'email': partner.email})]})

            if vals.get('shareholder_contact_ids')[0][0] == 6:
                for partner_id in vals.get('shareholder_contact_ids')[0][2]:
                    partner = self.env['res.partner'].browse(partner_id)
                    available_client_line = partner.client_contact_rel_ids.filtered(
                        lambda o: o.client_id.id == client.id)
                    if available_client_line:
                        available_client_line.write({'is_shareholder': True, 'permission': partner.permission})
                    else:
                        partner.write({'client_contact_rel_ids': [(0, 0,
                                                                   {'client_id': client.id, 'is_shareholder': True,
                                                                    'permission': partner.permission,
                                                                    'email': partner.email})]})

    def remove_client_contact_rel(self, vals, client):
        # Remove client contact relation for primary contact
        if vals.get('contact_child_ids') and not any(
                k in self._context for k in ("add_prmry_cntct", "rmv_prmry_cntct")):
            if vals.get('contact_child_ids')[0][0] == 3:
                contact = self.env['res.partner'].browse([vals.get('contact_child_ids')[0][1]])
                client_line = contact.client_contact_rel_ids.filtered(lambda o: o.client_id.id == client.id)
                if client_line:
                    client_line.write({'is_primary_contact': False})
            if vals.get('contact_child_ids')[0][0] == 6:
                for contact in client.contact_child_ids:
                    if contact.id not in vals.get('contact_child_ids')[0][2]:
                        client_line = contact.client_contact_rel_ids.filtered(lambda o: o.client_id.id == client.id)
                        if client_line:
                            client_line.write({'is_primary_contact': False})

        # Remove client contact relation for secondary contact
        if vals.get('secondary_contact_child_ids') and not any(
                k in self._context for k in ("add_scndr_cntct", "rmv_scndr_cntct")):
            if vals.get('secondary_contact_child_ids')[0][0] == 3:
                contact = self.env['res.partner'].browse([vals.get('secondary_contact_child_ids')[0][1]])
                client_line = contact.client_contact_rel_ids.filtered(lambda o: o.client_id.id == client.id)
                if client_line:
                    client_line.write({'is_secondary_contact': False})
            if vals.get('secondary_contact_child_ids')[0][0] == 6:
                for contact in client.secondary_contact_child_ids:
                    if contact.id not in vals.get('secondary_contact_child_ids')[0][2]:
                        client_line = contact.client_contact_rel_ids.filtered(lambda o: o.client_id.id == client.id)
                        if client_line:
                            client_line.write({'is_secondary_contact': False})
        if vals.get('auditor_contact_child_ids') and not any(
                k in self._context for k in ("add_auditor", "rmv_auditor")):
            if vals.get('auditor_contact_child_ids')[0][0] == 3:
                contact = self.env['res.partner'].browse([vals.get('auditor_contact_child_ids')[0][1]])
                client_line = contact.client_contact_rel_ids.filtered(lambda o: o.client_id.id == client.id)
                if client_line:
                    client_line.write({'is_auditor_contact': False})
            if vals.get('auditor_contact_child_ids')[0][0] == 6:
                for contact in client.auditor_contact_child_ids:
                    if contact.id not in vals.get('auditor_contact_child_ids')[0][2]:
                        client_line = contact.client_contact_rel_ids.filtered(lambda o: o.client_id.id == client.id)
                        if client_line:
                            client_line.write({'is_auditor_contact': False})
        if vals.get('signatory_contact_child_ids') and not any(
                k in self._context for k in ("add_signatory", "rmv_signatory")):
            if vals.get('signatory_contact_child_ids')[0][0] == 3:
                contact = self.env['res.partner'].browse([vals.get('signatory_contact_child_ids')[0][1]])
                client_line = contact.client_contact_rel_ids.filtered(lambda o: o.client_id.id == client.id)
                if client_line:
                    client_line.write({'is_corporate_banking_signatory': False})
            if vals.get('signatory_contact_child_ids')[0][0] == 6:
                for contact in client.signatory_contact_child_ids:
                    if contact.id not in vals.get('signatory_contact_child_ids')[0][2]:
                        client_line = contact.client_contact_rel_ids.filtered(lambda o: o.client_id.id == client.id)
                        if client_line:
                            client_line.write({'is_corporate_banking_signatory': False})

        if vals.get('hr_contact_child_ids') and not any(k in self._context for k in ("add_hr_cntct", "rmv_hr_cntct")):
            if vals.get('hr_contact_child_ids')[0][0] == 3:
                contact = self.env['res.partner'].browse([vals.get('hr_contact_child_ids')[0][1]])
                client_line = contact.client_contact_rel_ids.filtered(lambda o: o.client_id.id == client.id)
                if client_line:
                    client_line.write({'is_hr_contact': False})
            if vals.get('hr_contact_child_ids')[0][0] == 6:
                for contact in client.hr_contact_child_ids:
                    if contact.id not in vals.get('hr_contact_child_ids')[0][2]:
                        client_line = contact.client_contact_rel_ids.filtered(lambda o: o.client_id.id == client.id)
                        if client_line:
                            client_line.write({'is_hr_contact': False})

        if vals.get('accounting_contact_ids') and not any(
                k in self._context for k in ("add_finance_cntct", "rmv_finance_cntct")):
            if vals.get('accounting_contact_ids')[0][0] == 3:
                contact = self.env['res.partner'].browse([vals.get('accounting_contact_ids')[0][1]])
                client_line = contact.client_contact_rel_ids.filtered(lambda o: o.client_id.id == client.id)
                if client_line:
                    client_line.write({'is_client_finance_ac': False})
            if vals.get('accounting_contact_ids')[0][0] == 6:
                for contact in client.accounting_contact_ids:
                    if contact.id not in vals.get('accounting_contact_ids')[0][2]:
                        client_line = contact.client_contact_rel_ids.filtered(lambda o: o.client_id.id == client.id)
                        if client_line:
                            client_line.write({'is_client_finance_ac': False})

        if vals.get('shareholder_contact_ids') and not any(
                k in self._context for k in ("add_shareholder", "rmv_shareholder")):
            if vals.get('shareholder_contact_ids')[0][0] == 3:
                contact = self.env['res.partner'].browse([vals.get('shareholder_contact_ids')[0][1]])
                client_line = contact.client_contact_rel_ids.filtered(lambda o: o.client_id.id == client.id)
                if client_line:
                    client_line.with_context({'rmv_shareholder': True}).write({'is_shareholder': False})
            if vals.get('shareholder_contact_ids')[0][0] == 6:
                for contact in client.shareholder_contact_ids:
                    if contact.id not in vals.get('shareholder_contact_ids')[0][2]:
                        client_line = contact.client_contact_rel_ids.filtered(lambda o: o.client_id.id == client.id)
                        if client_line:
                            client_line.with_context({'rmv_shareholder': True}).write({'is_shareholder': False})

        # Remove client contact relation for CR partners and CR managers
        if 'cr_document_id' in vals and self.cr_document_id:
            for partner in self.cr_document_id.cr_partner_ids:
                client_line = partner.client_contact_rel_ids.filtered(lambda o: o.client_id.id == self.id)
                if client_line:
                    client_line.with_context({'doc_chng': True}).write({'is_shareholder': False})
            for manager in self.cr_document_id.cr_managers_ids:
                client_line = manager.client_contact_rel_ids.filtered(lambda o: o.client_id.id == self.id)
                if client_line:
                    client_line.with_context({'doc_chng': True}).write({'is_manager_cr': False})

        # Remove Client contact relation for CL manager
        if 'cl_document_id' in vals and self.cl_document_id:
            client_line = self.cl_document_id.cl_partner_id.client_contact_rel_ids.filtered(
                lambda o: o.client_id.id == self.id)
            if client_line:
                client_line.with_context({'doc_chng': True}).write({'is_manager_cl': False})
        # Remove Client contact relation for AOA financer
        if 'aoa_document_id' in vals and self.aoa_document_id:
            for partner in self.aoa_document_id.aoa_partner_ids:
                client_line = partner.client_contact_rel_ids.filtered(lambda o: o.client_id.id == self.id)
                if client_line:
                    client_line.with_context({'doc_chng': True}).write({'is_aoa_partner': False})
            # Financial Link Partner
            client_line = self.aoa_document_id.financial_link_partner.client_contact_rel_ids.filtered(
                lambda o: o.client_id.id == self.id)
            if client_line:
                client_line.with_context({'doc_chng': True}).write({'is_aoa_finance_contact': False})
            # General Manager
            client_line = self.aoa_document_id.general_manager.client_contact_rel_ids.filtered(
                lambda o: o.client_id.id == self.id)
            if client_line:
                client_line.with_context({'doc_chng': True}).write({'is_general_manager': False})
            # General Secretary
            client_line = self.aoa_document_id.general_secretary.client_contact_rel_ids.filtered(
                lambda o: o.client_id.id == self.id)
            if client_line:
                client_line.with_context({'doc_chng': True}).write({'is_general_secretary': False})
            # Admin Manager
            client_line = self.aoa_document_id.admin_manager.client_contact_rel_ids.filtered(
                lambda o: o.client_id.id == self.id)
            if client_line:
                client_line.with_context({'doc_chng': True}).write({'is_admin_manager': False})
            # Banking Signatory
            client_line = self.aoa_document_id.banking_signatory.client_contact_rel_ids.filtered(
                lambda o: o.client_id.id == self.id)
            if client_line:
                client_line.with_context({'doc_chng': True}).write({'is_corporate_banking_signatory': False})
            # Liaison Officer
            client_line = self.aoa_document_id.liaison_officer.client_contact_rel_ids.filtered(
                lambda o: o.client_id.id == self.id)
            if client_line:
                client_line.with_context({'doc_chng': True}).write({'is_liaison_officer': False})
        # Remove client contact relation for EC authorises
        if 'ec_document_id' in vals and self.ec_document_id:
            for authorizer in self.ec_document_id.cr_authorizers_ids:
                client_line = authorizer.client_contact_rel_ids.filtered(lambda o: o.client_id.id == self.id)
                if client_line:
                    client_line.with_context({'doc_chng': True}).write({'is_manager_ec': False})

    def write(self, vals):
        res = super(Contacts_Contacts, self).write(vals)
        if 'name' in vals:
            if 'shareholder_contact_ids' in vals:
                if vals['shareholder_contact_ids'][0][0] == 6 and vals['shareholder_contact_ids'][0][2] == []:
                    value = vals.pop('shareholder_contact_ids')
        self.remove_client_contact_rel(vals, self)
        self.get_client_contact_rel(vals, self)
        # Write permission in client contact rel line
        if vals.get('permission'):
            client_line = self.client_contact_rel_ids.filtered(lambda o: o.client_id.id in [
                self._context.get('active_id') or self._context.get('partner_id') or self._context.get('parent_id')])
            client_line.write({'permission': vals.get('permission')})
        # write email in client contact rel line
        if vals.get('email'):
            client_line = self.client_contact_rel_ids.filtered(lambda o: o.client_id.id in [
                self._context.get('active_id') or self._context.get('partner_id') or self._context.get('parent_id')])
            client_line.write({'email': vals.get('email')})
        if vals.get('arabic_name'):
            if self.ps_passport_serial_no_id:
                self.ps_passport_serial_no_id.write({'arabic_name': vals.get('arabic_name')})
            if self.qid_residency_id:
                self.qid_residency_id.write({'arabic_name': vals.get('arabic_name')})
            if self.cr_document_id:
                self.cr_document_id.write({'arabic_name': vals.get('arabic_name')})
            if self.cl_document_id:
                self.cl_document_id.write({'arabic_name': vals.get('arabic_name')})
            if self.ec_document_id:
                self.ec_document_id.write({'arabic_name': vals.get('arabic_name')})
        if vals.get('name'):
            if self.ps_passport_serial_no_id:
                self.ps_passport_serial_no_id.write({'passport_name': vals.get('name')})
            if self.qid_residency_id:
                self.qid_residency_id.write({'qid_name': vals.get('name')})
            if self.cr_document_id:
                self.cr_document_id.write({'cr_trade_name': vals.get('name')})
            if self.cl_document_id:
                self.cr_document_id.write({'cl_name': vals.get('name')})
            if self.ec_document_id:
                self.ec_document_id.write({'est_name_en': vals.get('name')})

        if vals.get('ps_passport_serial_no_id'):
            self.ps_passport_serial_no_id.write(
                {'passport_name': self.name, 'arabic_name': self.arabic_name, 'partner_id': self.id})
        if vals.get('qid_residency_id'):
            self.qid_residency_id.write({'qid_name': self.name, 'arabic_name': self.arabic_name, 'partner_id': self.id})
        if vals.get('cr_document_id') and self.is_branch == False:
            self.cr_document_id.write(
                {'cr_trade_name': self.name, 'arabic_name': self.arabic_name, 'partner_id': self.id})
        if vals.get('cl_document_id'):
            self.cl_document_id.write({'cl_name': self.name, 'arabic_name': self.arabic_name, 'partner_id': self.id})
        if vals.get('aoa_document_id'):
            self.aoa_document_id.write({'partner_id': self.id})
        if vals.get('ec_document_id'):
            self.ec_document_id.write(
                {'est_name_en': self.name, 'arabic_name': self.arabic_name, 'partner_id': self.id})

        return res

    @api.onchange('visa_file_id')
    def onchange_visa_file_id(self):
        for rec in self:
            if rec.visa_file_id:
                rec.visa_ref_no = rec.visa_file_id.visa_ref_no
                rec.visa_expiry_date = rec.visa_file_id.expiry_date

    def action_notify_client_missing_data(self):
        self.ensure_one()
        template = self.env.ref('ebs_fusion_contacts.email_template_notify_client_missing_data', False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='res.partner',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
        )
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    def compute_products(self):
        self.product_ids = False
        companies = self.env['res.company'].search([])
        for company in companies:
            if company.partner_id.id == self.id:
                products = self.env['product.template'].search([('company_id', '=', company.id)])
                self.product_ids = [(6, 0, products.ids)]

    def compute_user_ids(self):
        self.infotech_user_ids = False
        partner_company = False
        companies = self.env['res.company'].search([])
        for company in companies:
            if company.partner_id.id == self.id:
                partner_company = company.id

        users = self.env['res.users'].search([])
        for user in users:
            for company in user.company_ids:
                if company.id == partner_company:
                    self.infotech_user_ids = [(4, user.id)]

    def compute_tenders(self):
        self.tender_ids = False
        for tender in self.env['crm.lead'].search([('tender_type', '=', 'tender')]):
            print(tender, "PPPPPPPPPPPPPPPPPPPP")
            if tender.owner_id.id == self.id:
                self.tender_ids = [(4, tender.id)]

    def compute_key_contact_ids(self):
        for rec in self:

            rec.key_contact_ids = False
            rec.board_contact_ids = False
            rec.shareholder_contact_ids = False
            rec.primary_contact_ids = False
            rec.head_office_contact_id = False

            contact_ids = self.env['res.partner'].search([('parent_id', '=', rec.id), ('address_type', 'not in',
                                                                                       ['head_office', 'local_office',
                                                                                        'Work_sites',
                                                                                        'labor_accommodation',
                                                                                        'national_address'])])
            for child in contact_ids:
                if child.is_chairman or child.is_ceo or child.is_cfo or child.is_clo or child.is_chro \
                        or child.is_cmo:
                    rec.primary_contact_ids = [(4, child.id)]
                if child.is_general_manager or child.is_legal_contact:
                    rec.key_contact_ids = [(4, child.id)]
                if child.is_board_member:
                    rec.board_contact_ids = [(4, child.id)]
                if child.is_shareholder:
                    rec.shareholder_contact_ids = [(4, child.id)]

            if rec.child_ids:
                print(rec.child_ids, "@@@@@@@@@@@@")
                for child in rec.child_ids:
                    if child.address_type == 'head_office':
                        rec.head_office_contact_id = child.id
                    print(child.address_type, "###")

    @api.depends('is_chairman', 'is_ceo', 'is_cfo', 'is_clo', 'is_chro', 'is_cmo', 'is_general_manager')
    def _compute_kanban_view_name(self):
        diff = dict(show_address=None, show_address_only=None, show_email=None, html_format=None, show_vat=None)
        names = dict(self.with_context(**diff).name_get())
        for partner in self:
            string = ''
            if partner.is_chairman == True:
                string += '-Chairman'
            if partner.is_ceo == True:
                string += '-CEO'
            if partner.is_cfo == True:
                string += '-CFO'
            if partner.is_clo == True:
                string += '-CLO'
            if partner.is_chro == True:
                string += '-CHRO'
            if partner.is_cmo == True:
                string += '-CMO'
            if partner.is_general_manager == True:
                string += '-GM'
            partner.kanban_view_name = names.get(partner.id) + string

    def _address_as_string(self):
        self.ensure_one()
        addr = []
        if self.street:
            addr.append(self.street)
        if self.street2:
            addr.append(self.street2)
        if self.city:
            addr.append(self.city)
        if self.state_id:
            addr.append(self.state_id.name)
        if self.country_id:
            addr.append(self.country_id.name)
        if not addr:
            raise UserError(_("Address missing on partner '%s'.") % self.name)
        return " ".join(addr)

    def open_google_route(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'https://www.google.com/maps?saddr=' + self.env.user.partner_id._address_as_string() + '&daddr=' + self._address_as_string() + '&directionsmode=driving',
            'target': 'new'
        }

    def open_google_url(self):
        self.geo_localize()
        if self.partner_latitude and self.partner_longitude:
            return {
                'type': 'ir.actions.act_url',
                'url': 'https://www.google.com/maps/search/?api=1&query=' + str(self.partner_latitude) + ',' + str(
                    self.partner_longitude),
                'target': 'new'
            }
        return False

    def preview_document(self):
        self.ensure_one()
        if self.name:
            action = {
                'type': "ir.actions.act_url",
                'target': "_blank",
                'url': '/documents/content/preview/%s' % self.id
            }
            return action

    def access_content(self):
        if self.name:
            self.ensure_one()
            action = {
                'type': "ir.actions.act_url",
                'target': "new",
            }
            if self.name.url:
                action['url'] = self.name.url
            elif self.name.type == 'binary':
                action['url'] = '/documents/content/%s' % self.id
            return action

    @api.depends('document_o2m')
    def _compute_expiring_document_count(self):
        doc_list = []
        for rec in self.document_o2m:
            if rec.expiry_date:
                days = (rec.expiry_date - date.today()).days
                if days <= 30 and days > 0:
                    doc_list.append(rec.id)
        self.document_expiring_count = len(doc_list)

    def _compute_tender_count(self):
        for rec in self:
            deals = self.env['crm.lead'].search([('partner_id', '=', rec.id), ('type', '=', 'opportunity')])
            if deals:
                rec.tender_count = len(deals)
            else:
                rec.tender_count = 0

    @api.depends('document_o2m')
    def _compute_expired_document_count(self):
        doc_list = []
        for rec in self.document_o2m:
            if rec.expiry_date:
                days = (rec.expiry_date - date.today()).days
                if days <= 0:
                    doc_list.append(rec.id)
        self.document_expired_count = len(doc_list)

    def expiring_document(self):
        doc_list = []
        print("testtttttttttt", doc_list)

        for rec in self.document_o2m:
            if rec.expiry_date:
                days = (rec.expiry_date - date.today()).days
                if days <= 30 and days > 0:
                    doc_list.append(rec.id)
        self.document_expiring_count = len(doc_list)

        return {
            'name': _('Documents'),
            'res_model': 'documents.document',
            'type': 'ir.actions.act_window',
            'views': [(False, 'kanban'), (False, 'tree'), (False, 'form')],
            'view_mode': 'kanban',
            'context': {
                "search_default_partner_id": self.id,
                "default_partner_id": self.id,
                "searchpanel_default_folder_id": False,
                "hide_contact": True,
                "hide_service": True
            },
            'domain': [('id', 'in', doc_list), ('partner_id', '=', self.id), ('partner_id', '!=', False)],
        }

    def expired_documents(self):
        doc_list = []
        for rec in self.document_o2m:
            if rec.expiry_date:
                days = (rec.expiry_date - date.today()).days
                if days <= 0:
                    doc_list.append(rec.id)
        return {
            'name': _('Documents'),
            'res_model': 'documents.document',
            'type': 'ir.actions.act_window',
            'views': [(False, 'kanban'), (False, 'tree'), (False, 'form')],
            'view_mode': 'kanban',
            'context': {
                "search_default_partner_id": self.id,
                "default_partner_id": self.id,
                "searchpanel_default_folder_id": False,
                "hide_contact": True,
                "hide_service": True
            },
            'domain': [('id', 'in', doc_list), ('partner_id', '=', self.id), ('partner_id', '!=', False)],
        }

    def view_assets(self):
        self.ensure_one()
        company_id = False
        company_partners = self.env['res.company'].search([])
        for company in company_partners:
            if self.id == company.partner_id.id:
                company_id = company
        return {
            'name': _('Assets'),
            'res_model': 'account.asset',
            'type': 'ir.actions.act_window',
            'views': [(False, 'tree'), (False, 'form')],
            'view_mode': 'tree',
            'context': {
                "search_default_company_id": company_id.id,
                "default_company_id": company_id.id,
                "default_type_of_asset": self._context.get('type'),
            },
            'domain': [('company_id', '=', company_id.id), ('company_id', '!=', False),
                       ('type_of_asset', '=', self._context.get('type'))],
        }

    def view_helpdesk_tickets(self):
        self.ensure_one()
        company_id = False
        company_partners = self.env['res.company'].search([])
        for company in company_partners:
            if self.id == company.partner_id.id:
                company_id = company
        return {
            'name': _('Complaints'),
            'res_model': 'helpdesk.ticket',
            'type': 'ir.actions.act_window',
            'views': [(False, 'tree'), (False, 'form')],
            'view_mode': 'tree',
            'context': {
                "search_default_company_id": company_id.id,
                "default_company_id": company_id.id
            },
            'domain': [('company_id', '=', company_id.id), ('company_id', '!=', False)],
        }

    def view_budgets(self):
        self.ensure_one()
        company_id = False
        company_partners = self.env['res.company'].search([])
        for company in company_partners:
            if self.id == company.partner_id.id:
                company_id = company
        return {
            'name': _('Budgets'),
            'res_model': 'crossovered.budget.lines',
            'type': 'ir.actions.act_window',
            'views': [(False, 'tree'), (False, 'form')],
            'view_mode': 'tree',
            'context': {
                "search_default_company_ids": company_id.id,
                "default_company_ids": company_id.id,
                "default_type_of_budget": self._context.get('type'),
            },
            'domain': [('company_ids', 'in', company_id.id), ('company_ids', '!=', False),
                       ('type_of_budget', '=', self._context.get('type'))],
        }

    def view_attendance(self):
        department_ids = self.env['hr.department'].search([('type_of_department', '=', self._context.get('type'))])
        employees = self.env['hr.employee'].search(
            [('partner_parent_id', '=', self.id), ('department_id', 'in', department_ids.ids)]).ids
        action = self.env.ref('hr_attendance.hr_attendance_action').read([])[0]
        action['domain'] = [('employee_id', 'in', employees)]
        action['context'] = {'create': False,
                             'edit': False}
        return action

    def view_work_status(self):
        company_id = self.env['res.company'].search([('partner_id', '=', self.id)])
        department_ids = self.env['hr.department'].search([('type_of_department', '=', self._context.get('type')),
                                                           ('company_id', '=', company_id.id)])
        action = self.env.ref('hr.action_hr_job').read([])[0]
        action['domain'] = [('department_id', 'in', department_ids.ids)]
        action['context'] = {'create': False,
                             'edit': False}
        return action

    def view_vehicle_maintenance(self):
        action = self.env.ref('fleet.fleet_vehicle_costs_action').read([])[0]
        action['context'] = {'create': False,
                             'edit': False}
        return action

    def view_vendor_database(self):
        action = self.env.ref('ebs_fusion_contacts.action_suppliers').read([])[0]
        action['context'] = {'create': False,
                             'edit': False}
        return action

    def view_purchase_order_report(self):
        company_id = self.env['res.company'].search([('partner_id', '=', self.id)])
        action = self.env.ref('purchase.purchase_form_action').read([])[0]
        action['domain'] = [('company_id', '=', company_id.id)]
        action['context'] = {'create': False,
                             'edit': False}
        return action

    def view_grn_report(self):
        company_id = self.env['res.company'].search([('partner_id', '=', self.id)])
        action = self.env.ref('stock.action_picking_tree_all').read([])[0]
        action['domain'] = [('company_id', '=', company_id.id), ('state', '=', 'done')]
        action['context'] = {'create': False,
                             'edit': False}
        return action

    def view_social_media_activities(self):
        action = self.env.ref('social.action_social_post').read([])[0]
        action['context'] = {'create': False,
                             'edit': False}
        return action

    def view_news_letter(self):
        action = self.env.ref('mass_mailing.action_view_mass_mailing_lists').read([])[0]
        action['context'] = {'create': False,
                             'edit': False}
        return action

    def view_cases_fgh(self):
        action = self.env.ref('ebs_fusion_legal.action_ebs_legal_case').read([])[0]
        action['context'] = {'create': False,
                             'edit': False}
        return action

    def view_cases_client(self):
        action = self.env.ref('ebs_fusion_legal.action_ebs_legal_case').read([])[0]
        action['domain'] = [('partner_id', '=', self.id), ('case_type', '=', 'client')]
        action['context'] = {'create': False,
                             'edit': False}
        return action

    def view_cases_employee(self):
        employee_ids = self.env['hr.employee'].search([('partner_parent_id', '=', self.id)])
        action = self.env.ref('ebs_fusion_legal.action_ebs_legal_case').read([])[0]
        action['domain'] = [('case_type', '=', 'employee'), ('employee_id', 'in', employee_ids.ids)]
        action['context'] = {'create': False,
                             'edit': False}
        return action

    def open_dependents(self):
        self.ensure_one()
        action = self.env.ref('ebs_fusion_contacts.action_dependents').read()[0]
        if self.parent_id:
            action['context'] = {
                'default_is_dependent': True,
                'default_parent_id': self.id,
                'default_dependent_id': self.sponsored_company_id.id,
                'default_main_parent_id': self.parent_id.id,
            }
            action['domain'] = [('parent_id', '=', self.id), (
                'address_type', 'not in',
                ['head_office', 'local_office', 'Work_sites', "labor_accommodation", "national_address"])]
        else:
            action['context'] = {
                'default_dependent_id': self.id,
                'default_parent_id': self.id,
                'default_is_dependent': True,
                'default_main_parent_id': self.id,
            }
            action['domain'] = [('dependent_id', '=', self.id), (
                'address_type', 'not in',
                ['head_office', 'local_office', 'Work_sites', "labor_accommodation", "national_address"])]
        return action

    def open_contacts(self):
        self.ensure_one()
        action = self.env.ref('contacts.action_contacts').read()[0]
        action['context'] = {
            'default_parent_id': self.id,
        }
        action['domain'] = [('parent_id', '=', self.id), ('address_type', 'not in',
                                                          ['head_office', 'local_office', 'Work_sites',
                                                           'labor_accommodation', 'national_address'])]
        return action

    def action_see_documents(self):
        self.ensure_one()
        return {
            'name': _('Documents'),
            'res_model': 'documents.document',
            'type': 'ir.actions.act_window',
            'views': [(False, 'kanban'), (False, 'tree'), (False, 'form')],
            'view_mode': 'kanban',
            'context': {
                "search_default_partner_id": self.id,
                "default_partner_id": self.id,
                "searchpanel_default_folder_id": False,
                "hide_contact": True,
                "hide_service": True
            },
            'domain': [('partner_id', '=', self.id), ('partner_id', '!=', False)],
        }

    def action_see_contract(self):
        self.ensure_one()
        return {
            'name': _('Tenders'),
            'res_model': 'ebs.crm.proposal',
            'type': 'ir.actions.act_window',
            'views': [(False, 'tree'), (False, 'form')],
            'view_mode': 'tree',
            'context': {

                "default_type": "proposal",
            },
            'domain': [('contact_id', '=', self.id), ('type', '=', 'proposal'), ('contact_id', '!=', False)],
        }

    def action_see_tenders(self):
        self.ensure_one()
        form_view_ref = self.env.ref('crm.crm_lead_view_form', False)
        tree_view_ref = self.env.ref('crm.crm_case_tree_view_oppor', False)
        return {
            'name': _('Deals'),
            'res_model': 'crm.lead',
            'type': 'ir.actions.act_window',
            'views': [(tree_view_ref.id, 'tree'), (form_view_ref.id, 'form')],
            'view_mode': 'tree',
            'context': {
                "default_type": "opportunity",
            },
            'domain': [('partner_id', '=', self.id), ('type', '=', 'opportunity'), ('partner_id', '!=', False)],
        }

    def action_see_pricelist(self):
        self.ensure_one()
        proposal_lines = self.env['ebs.crm.proposal.line'].search([('contact_id', '=', self.id)])
        form_view_ref = self.env.ref('ebs_fusion_services.view_ebs_crm_proposal_line_form', False)
        tree_view_ref = self.env.ref('ebs_fusion_services.view_ebs_crm_proposal_line_tree', False)

        return {
            'domain': [('id', 'in', proposal_lines.ids)],
            'name': 'Pricelist',
            'res_model': 'ebs.crm.proposal.line',
            'type': 'ir.actions.act_window',
            'views': [(tree_view_ref.id, 'tree'), (form_view_ref.id, 'form')],
            'view_mode': 'tree',
        }

    def search(self, args, **kwargs):

        results = super(Contacts_Contacts, self).search(args, **kwargs)
        for conditions in args:
            if 'email' in conditions:
                for email_addresses in self.env['email.addresses'].search([('email', 'ilike', conditions[2])]):
                    if email_addresses.partner_id:
                        results += email_addresses.partner_id
                break

        return results

    def search_companies(self):
        print("##############")
        partners = self.env['res.company'].search([]).mapped('partner_id')
        print(partners)
        return {
            'name': _('Companies'),
            'res_model': 'res.partner',
            'type': 'ir.actions.act_window',

            'view_mode': 'kanban',

        }

    def import_update(self):
        partners = self.env['res.company'].search([]).mapped('partner_id')
        for rec in partners:
            rec.onchange_name()
            rec.company_partner = True
            rec.is_company = True
            rec.is_customer = False

    @api.depends('name')
    def compute_company_partner(self):
        for rec in self:
            partners = self.env['res.company'].search([]).mapped('partner_id')
            if rec.id in partners.ids:
                rec.company_partner = True
            else:
                rec.company_partner = False

    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(Contacts_Contacts, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                             submenu=submenu)
        if self._context.get("our_companies"):
            doc = etree.XML(res['arch'])

            for node in doc.xpath("//form"):
                node.set('create', 'false')
            for node in doc.xpath("//kanban"):
                node.set('create', 'false')
            res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

    @api.onchange('company_type')
    def onchange_clients(self):
        if self._context.get("display_stages_type") == 'clients':
            if self.company_type == 'company':
                self.is_customer = True
        if self._context.get("display_stages_type") == 'suppliers':
            if self.company_type == 'company':
                self.is_vendor = True

    def action_open_helpdesk_ticket(self):
        action = self.env.ref('helpdesk.helpdesk_ticket_action_main_tree').read()[0]
        action['context'] = {}
        if self.company_partner == True:
            action['domain'] = [('company_id', '=', self.company_id.id)]
        else:
            action['domain'] = [('partner_id', 'child_of', self.ids)]
        return action

    def action_see_employee_attendance(self):
        employees = self.env['hr.employee'].search([('partner_parent_id', '=', self.id)]).ids
        action = self.env.ref('hr_attendance.hr_attendance_action').read([])[0]
        action['domain'] = [('employee_id', 'in', employees)]
        action['context'] = {'create': False,
                             'edit': False}
        return action

    def view_hr_assets(self):
        employee_ids = self.env['hr.employee'].search([('partner_parent_id', '=', self.id)])
        action = self.env.ref('hr_custody.action_hr_custody').read([])[0]
        action['domain'] = [('employee', 'in', employee_ids.ids)]
        action['context'] = {'create': False,
                             'edit': False}
        return action

    def view_penalty(self):
        employee_ids = self.env['hr.employee'].search([('partner_parent_id', '=', self.id)])
        action = self.env.ref('ebs_fusion_hr_employee.employee_penalty_act_window').read([])[0]
        action['domain'] = [('employee_id', 'in', employee_ids.ids)]
        action['context'] = {'create': False,
                             'edit': False}
        return action

    def action_account_invoice_report_all(self):
        self.ensure_one()
        action = self.env.ref('account.action_account_invoice_report_all').read()[0]
        company_id = self.env['res.company'].search([('partner_id', '=', self.id)])
        action['domain'] = [('company_id', '=', company_id.id)]
        return action

    def act_crossovered_budget_lines_view(self):
        self.ensure_one()
        action = self.env.ref('account_budget.act_crossovered_budget_lines_view').read()[0]
        company_id = self.env['res.company'].search([('partner_id', '=', self.id)])
        action['domain'] = [('company_id', '=', company_id.id)]
        return action


class AOAShareholder(models.Model):
    _name = 'aoa.shareholder'
    _description = 'AOA Shareholder'

    name = fields.Char('Name')
    partner_id = fields.Many2one('res.partner')
    document_id = fields.Many2one('documents.document', 'Document', required=1)
    doc_type_id = fields.Many2one(related='document_id.document_type_id', string='Document Type')
    total_share_holders = fields.Char('Total Share Holders')
    share_capital = fields.Char('Share Capital')
    share_percent = fields.Char('Share Percentage')

    def preview_document(self):
        self.ensure_one()
        if self.name:
            action = {
                'type': "ir.actions.act_url",
                'target': "_blank",
                'url': '/documents/content/preview/%s' % self.id
            }
            return action

    def access_content(self):
        if self.name:
            self.ensure_one()
            action = {
                'type': "ir.actions.act_url",
                'target': "new",
            }
            if self.name.url:
                action['url'] = self.name.url
            elif self.name.type == 'binary':
                action['url'] = '/documents/content/%s' % self.id
            return action


class AOAProfitShare(models.Model):
    _name = 'aoa.profit.share'
    _description = 'AOA Profit Share'

    partner_id = fields.Many2one('res.partner')
    name = fields.Char('Name')
    document_id = fields.Many2one('documents.document', 'Document', required=1)
    doc_type_id = fields.Many2one(related='document_id.document_type_id', string='Document Type')
    total_share_holders = fields.Char('Total Share Holders')
    share_capital = fields.Char('Share Capital')
    share_percent = fields.Char('Share Percentage')

    def preview_document(self):
        self.ensure_one()
        if self.name:
            action = {
                'type': "ir.actions.act_url",
                'target': "_blank",
                'url': '/documents/content/preview/%s' % self.id
            }
            return action

    def access_content(self):
        if self.name:
            self.ensure_one()
            action = {
                'type': "ir.actions.act_url",
                'target': "new",
            }
            if self.name.url:
                action['url'] = self.name.url
            elif self.name.type == 'binary':
                action['url'] = '/documents/content/%s' % self.id
            return action


class DependentsType(models.Model):
    _name = 'dependent.type'
    _description = 'Dependent Type'

    name = fields.Char("Name")


class ContactData(models.Model):
    _name = 'contact'
    _description = 'Contact'

    name = fields.Char(string='Name')
    operations_report = fields.Selection([('type_of_services_service_orders', 'Type of Services / Service Orders'),
                                          ('complaints_by_client', 'Complaints By Client'),
                                          ('complaints_by_employees', 'Complaints By Employees'),
                                          ('policies_and_procedures', 'Policies and Procedures'),
                                          ('timesheet_services', 'Timesheet - Services')],
                                         string='Operations-Report')

    human_resources_report = fields.Selection([('hr_assets', 'HR Assets'),
                                               ('penalty', 'Penalty'),
                                               ('assets', 'Assets'),
                                               ('employee_status', 'Employee Status'),
                                               ('work_status', 'Work Status'),
                                               ('human_resources_policy', 'Human Resources Policy'),
                                               ('timesheet', 'Timesheet')],
                                              string='Human Resources-Report')

    legal_reports = fields.Selection([('cases_of_fgh', 'Cases Of FGH'),
                                      ('cases_of_client', 'Cases Of Client'),
                                      ('cases_of_employee', 'Cases Of Employee'),
                                      ('client_liquidation_disollution', 'Client Liquidation & Disollution'),
                                      ('court_closure', 'Court Closure'),
                                      ('legal_complaints', 'Legal Complaints'),
                                      ('legal_budget', 'Legal Budget'),
                                      ('work_status', 'Work Status'),
                                      ('legal_assets', 'Legal Assets'),
                                      ('policies_and_procedures', 'Policies and Procedures'),
                                      ('timesheet', 'Timesheet')],
                                     string='Legal - Reports')

    accounts_report = fields.Selection([('complaints', 'Complaints'),
                                        ('profit_and_loss', 'Profit And Loss'),
                                        ('audit_report', 'Audit Report'),
                                        ('total_income', 'Total Income'),
                                        ('total_profit', 'Total Profit'),
                                        ('penalty', 'Penalty'),
                                        ('total_expense', 'Total Expense'),
                                        ('total', 'Total'),
                                        ('total_expense_by_yype', 'Total Expense By Type'),
                                        ('wps_report', 'Wps Report'),
                                        ('loan_report', 'Loan Report'),
                                        ('asset', 'Asset'),
                                        ('vehicle_maintenance', 'Vehicle Maintenance'),
                                        ('asset_depreciation', 'Asset Depreciation'),
                                        ('timesheet', 'Timesheet'),
                                        ('ageing_report_p', 'Ageing Report (Payables)'),
                                        ('ageing_report_r', 'Ageing Report (Recievables)'),
                                        ('invoice_status', 'Invoice Status'),
                                        ('accounts_budget', 'Accounts Budget'),
                                        ('budget_consolidated', 'Budget Consolidated'),
                                        ('work_status', 'Work Status'),
                                        ('accounts_assets', 'Accounts Assets'),
                                        ('policies_and_procedures', 'Policies and Procedures')],
                                       string='Accounts -  Report')

    information_technology_report = fields.Selection([('it_system_usage_feedback', 'IT System Usage Feedback'),
                                                      ('it_assist', 'IT Assist'),
                                                      ('complaints', 'Complaints'),
                                                      ('it_assets', 'IT Assets'),
                                                      ('it_department_budget', 'IT Department Budget'),
                                                      ('work_status', 'Work Status'),
                                                      ('assets', 'Assets'),
                                                      ('policies_and_procedures', 'Policies and Procedures'),
                                                      ('timesheet', 'Timesheet')],
                                                     string='Information Technology - Report')

    marketing_client_communications_research_reports = fields.Selection([('clientProfile', 'Client Profile'),
                                                                         ('complaints_marketing',
                                                                          'Complaints - Marketing'),
                                                                         ('marketing_budget', 'Marketing Budget'),
                                                                         ('timesheet_marketing', 'Timesheet-Marketing'),
                                                                         ('marketing_work_status',
                                                                          'Marketing-Work Status'),
                                                                         ('marketing_assets', 'Marketing Assets'),
                                                                         ('policies_and_procedures',
                                                                          'Policies and Procedures')],
                                                                        string='Marketing Client Communications And Research - Reports')

    sales_seport = fields.Selection([('lead', 'Lead'),
                                     ('proposal_after_signing', 'Proposal after signing'),
                                     ('opportunity', 'Opportunity'),
                                     ('client_appraisal_after_sr', 'Client Appraisal - After Sales Reporting'),
                                     ('client_appraisal_after_m', 'Client Appraisal - After Maintenance'),
                                     ('sales_department_budget', 'Sales Department Budget'),
                                     ('work_status', 'Work Status'),
                                     ('sales_assets', 'Sales Assets'),
                                     ('policies_and_procedures', 'Policies and Procedures'),
                                     ('tender_submission', 'Tender Submission')],
                                    string='Sales - Report')

    social_media_report = fields.Selection([('complaints', 'Complaints'),
                                            ('social_media_budget', 'Social Media Budget'),
                                            ('social_media_activities', 'Social Media Activities'),
                                            ('blogs', 'Blogs'),
                                            ('news_letter', 'News Letter'),
                                            ('work_status', 'Work Status'),
                                            ('social_media_assets', 'Social Media Assets'),
                                            ('policies_and_procedures', 'Policies and Procedures'),
                                            ('timesheet', 'Timesheet')],
                                           string='Social Media - Report')

    procurement_report = fields.Selection([('purchase_requsition', 'Purchase Requsition'),
                                           ('vendor_database', 'Vendor Database'),
                                           ('purchase_order_report', 'Purchase Order Report'),
                                           ('grn_report', 'Grn Report'),
                                           ('procurement_report', 'Procurement Report'),
                                           ('procurement_budget', 'Procurement Budget'),
                                           ('procurement_work_status', 'Procurement-Work Status'),
                                           ('procurement_assets', 'Procurement Assets'),
                                           ('policies_and_procedures', 'Policies and Procedures'),
                                           ('timesheet', 'Timesheet')],
                                          string='Procurement - Report')


class Country_State(models.Model):
    _inherit = 'res.country.state'

    name = fields.Char(string='State Name', required=True, translate=True,
                       help='Administrative divisions of a country. E.g. Fed. State, Departement, Canton')


class EbsClientContact(models.Model):
    _name = 'ebs.client.contact'
    _description = 'EBS Client Contact'
    _rec_name = 'client_id'

    partner_id = fields.Many2one('res.partner')
    client_id = fields.Many2one('res.partner', string='Client',
                                domain=[('is_customer', '=', True), ('is_company', '=', True),
                                        ('parent_id', '=', False)])
    related_company_ids = fields.Many2many(related='client_id.related_company_ids',
                                           string='Related Main company Companies')
    partner_company = fields.Selection(string='Company Type',
                                       selection=[('person', 'Individual'), ('company', 'Company')],
                                       compute='_compute_company_type', inverse='_write_company_type',
                                        readonly=True, store=True)
    partner_email = fields.Char(related='partner_id.email', store=True)
    partner_mobile = fields.Char(related='partner_id.mobile', store=True)
    is_primary_contact = fields.Boolean(string='Primary Contact')
    is_secondary_contact = fields.Boolean(string='Secondary Contact')
    is_hr_contact = fields.Boolean(string='HR Contact')
    is_manager_cr = fields.Boolean("Manager CR")
    is_manager_ec = fields.Boolean("Manager EC")
    is_manager_cl = fields.Boolean('Manager Cl')
    is_deliver_partner = fields.Boolean("Deliver Partner")
    is_chairman = fields.Boolean(string='Chairman')
    is_ceo = fields.Boolean(string='CEO')
    is_cfo = fields.Boolean(string='CFO')
    is_clo = fields.Boolean(string='CLO')
    is_chro = fields.Boolean(string='CHRO')
    is_cmo = fields.Boolean(string='CMO')
    is_board_member = fields.Boolean('Is Board Member')
    is_shareholder = fields.Boolean(string="Shareholder")
    is_aoa_partner = fields.Boolean(string="AOA Partner")
    is_authorised_signatory = fields.Boolean(string="Is Authorised Signatory")
    is_legal_contact = fields.Boolean("Legal Contact")
    is_auditor_contact = fields.Boolean("Auditor Contact")
    is_corporate_banking_signatory = fields.Boolean('Corporate Banking Signatory')
    is_general_manager = fields.Boolean("General Manager")
    is_general_secretary = fields.Boolean("General Secretary")
    is_admin_manager = fields.Boolean("Administration Manager")
    is_liaison_officer = fields.Boolean("Liaison Officer")
    is_client_finance_ac = fields.Boolean("Client Finance/Accounts")
    permission = fields.Selection([('approver', 'Approver'), ('requester', 'Requester')], string="Permission")
    phone = fields.Char(string="Phone")
    email = fields.Char(string="Email")
    percentage = fields.Float('Percentage')
    profit_share = fields.Float('Profit Share')
    is_aoa_finance_contact = fields.Boolean()
    tawtheeq_username = fields.Char('Username')
    tawtheeq_password = fields.Char('Password')
    moci_username = fields.Char('Username')
    moci_password = fields.Char('Password')
    smart_card_password = fields.Char('Smart Card Password')
    mobile_phone = fields.Char('Mobile Phone under his/her name')

    _sql_constraints = [
        ('uniqe_partner_client_rel', 'unique(partner_id, client_id)',
         'Relation Line Already Exist For This Client And Contact.'),
    ]

    @api.onchange('client_id')
    def check_clint_contact_rel(self):
        # Raise error if try to create duplicate line for same client
        for rec in self:
            client_lines = rec.partner_id.client_contact_rel_ids.filtered(lambda o: o.client_id.id == rec.client_id.id)
            if (client_lines._origin.id - rec._origin.id):
                raise UserError(_("Relation Line Already Exist For This Client And Contact."))

    @api.constrains('is_primary_contact', 'is_secondary_contact')
    def check_contact_primary_secondary(self):
        # Raise Error if same contact has primary contact and secondary contact boolean true.
        for rec in self:
            if rec.is_primary_contact == True and rec.is_secondary_contact == True:
                raise UserError(_("Same Contact Can\'t Be Set As Primary And Secondary Contact For Same Client."))

    def delete_context_data(self):
        keys_to_remove = ["rmv_ec_mngr", "add_ec_mngr",
                          "rmv_cl_mngr", "add_cl_mngr",
                          "rmv_aoa_prtnr", "add_aoa_prtnr",
                          "rmv_cr_mngr", "add_cr_mngr",
                          "rmv_cr_ptnr", "add_cr_ptnr",
                          "rmv_aoa_ptnr", "add_aoa_ptnr",
                          "rmv_prmry_cntct", "add_prmry_cntct",
                          'rmv_scndr_cntct', 'add_scndr_cntct',
                          'rmv_hr_cntct', 'add_hr_cntct',
                          'rmv_finance_cntct', 'add_finance_cntct',
                          'add_shareholder', 'rmv_shareholder',
                          'rmv_auditor', 'add_auditor',
                          'rmv_signatory', 'add_signatory',
                          ]
        local_dict = self._context.copy()
        for key in keys_to_remove:
            if key in local_dict:
                del local_dict[key]
        self.env.context = local_dict

    @api.model
    def create(self, vals):
        res = super(EbsClientContact, self).create(vals)
        # Add contact in selected client as per relation boolean is set true from line
        for record in res:
            if record.is_primary_contact and not 'add_prmry_cntct' in self._context:
                record.client_id.with_context({'add_prmry_cntct': True}).sudo().write(
                    {'contact_child_ids': [(4, record.partner_id.id)]})
            if record.is_secondary_contact and not 'add_scndr_cntct' in self._context:
                record.client_id.with_context({'add_scndr_cntct': True}).sudo().write(
                    {'secondary_contact_child_ids': [(4, record.partner_id.id)]})
            if record.is_auditor_contact and not 'add_auditor' in self._context:
                record.client_id.with_context({'add_auditor': True}).sudo().write(
                    {'auditor_contact_child_ids': [(4, record.partner_id.id)]})
            if record.is_corporate_banking_signatory and not 'add_signatory' in self._context:
                record.client_id.with_context({'add_signatory': True}).sudo().write(
                    {'signatory_contact_child_ids': [(4, record.partner_id.id)]})
            if record.is_hr_contact and not 'add_hr_cntct' in self._context:
                record.client_id.with_context({'add_hr_cntct': True}).sudo().write(
                    {'hr_contact_child_ids': [(4, record.partner_id.id)]})
            if record.is_client_finance_ac and not 'add_finance_cntct' in self._context:
                record.client_id.with_context({'add_finance_cntct': True}).sudo().write(
                    {'accounting_contact_ids': [(4, record.partner_id.id)]})
            if record.is_shareholder and not self._context.get('add_shareholder') and not self._context.get(
                    'aoa_document'):
                record.client_id.with_context({'add_shareholder': True}).sudo().write(
                    {'shareholder_contact_ids': [(4, record.partner_id.id)]})
                if not self._context.get('cr_document') and not self._context.get('add_cr_ptnr'):
                    cr_doc_type = record.client_id.document_o2m.filtered(
                        lambda
                            x: x.is_client_rel and x.document_type_name == 'Commercial Registration (CR) Application')
                    if not record.client_id.cr_document_id and (
                            not self._context.get('default_is_client_rel') and not cr_doc_type):
                        raise ValidationError(
                            _("This record does not have commercial registration document or may be does not have client."))
                    record.client_id.cr_document_id.with_context({'add_cr_ptnr': True}).sudo().write(
                        {'cr_partner_ids': [(4, record.partner_id.id)]})

            if record.is_manager_cr and not self._context.get('cr_document') and not self._context.get('add_cr_mngr'):
                cr_doc_type = record.client_id.document_o2m.filtered(
                    lambda x: x.is_client_rel and x.document_type_name == 'Commercial Registration (CR) Application')
                if not record.client_id.cr_document_id and (
                        not self._context.get('default_is_client_rel') and not cr_doc_type):
                    raise ValidationError(
                        _("This record does not have commercial registration document or may be does not have client."))
                record.client_id.cr_document_id.with_context({'add_cr_mngr': True}).sudo().write(
                    {'cr_managers_ids': [(4, record.partner_id.id)]})
            if record.is_manager_cl and not self._context.get('cl_document') and not self._context.get('add_cl_mngr'):
                cl_doc_type = record.client_id.document_o2m.filtered(
                    lambda x: x.is_client_rel and x.document_type_name == 'Commercial License')
                if not record.client_id.cl_document_id and (
                        not self._context.get('default_is_client_rel') and not cl_doc_type):
                    raise ValidationError(
                        _("This record does not have commercial license document or may be does not have client."))
                record.client_id.cl_document_id.with_context({'add_cl_mngr': True}).sudo().write(
                    {'cl_partner_id': record.partner_id.id})
            if record.is_aoa_finance_contact and not self._context.get('aoa_document') and not self._context.get(
                    'add_aoa_prtnr'):
                aoa_doc_type = record.client_id.document_o2m.filtered(
                    lambda x: x.is_client_rel and x.document_type_name == 'articles of association')
                if not record.client_id.aoa_document_id and (
                        not self._context.get('default_is_client_rel') and not aoa_doc_type):
                    raise ValidationError(
                        _("This record does not have Article of Association document or may be does not have client."))
                record.client_id.aoa_document_id.with_context({'add_aoa_prtnr': True}).sudo().write(
                    {'financial_link_partner': record.partner_id.id})
            if record.is_general_manager and not self._context.get('aoa_document') and not self._context.get(
                    'add_aoa_prtnr'):
                record.client_id.aoa_document_id.with_context({'add_aoa_prtnr': True}).sudo().write(
                    {'general_manager': record.partner_id.id})
            if record.is_general_secretary and not self._context.get('aoa_document') and not self._context.get(
                    'add_aoa_prtnr'):
                record.client_id.aoa_document_id.with_context({'add_aoa_prtnr': True}).sudo().write(
                    {'general_secretary': record.partner_id.id})
            if record.is_admin_manager and not self._context.get('aoa_document') and not self._context.get(
                    'add_aoa_prtnr'):
                record.client_id.aoa_document_id.with_context({'add_aoa_prtnr': True}).sudo().write(
                    {'admin_manager': record.partner_id.id})
            if record.is_corporate_banking_signatory and not self._context.get(
                    'aoa_document') and not self._context.get('add_aoa_prtnr'):
                record.client_id.aoa_document_id.with_context({'add_aoa_prtnr': True}).sudo().write(
                    {'banking_signatory': record.partner_id.id})
            if record.is_liaison_officer and not self._context.get('aoa_document') and not self._context.get(
                    'add_aoa_prtnr'):
                record.client_id.aoa_document_id.with_context({'add_aoa_prtnr': True}).sudo().write(
                    {'liaison_officer': record.partner_id.id})
            if record.is_manager_ec and not self._context.get('ec_document') and not self._context.get('add_ec_mngr'):
                ec_doc_type = record.client_id.document_o2m.filtered(
                    lambda x: x.is_client_rel and x.document_type_name == 'Establishment Card')
                if not record.client_id.ec_document_id and (
                        not self._context.get('default_is_client_rel') and not ec_doc_type):
                    raise ValidationError(
                        _("This record does not have establishment card document or may be does not have client."))
                record.client_id.ec_document_id.with_context({'add_ec_mngr': True}).sudo().write(
                    {'cr_authorizers_ids': [(4, record.partner_id.id)]})

        self.delete_context_data()
        return res

    def unlink(self):
        # Delete all records from client if line is unlink from contact form view.
        for record in self:
            record.partner_id.write({'last_client_id': False})
            if record.is_primary_contact and not 'rmv_prmry_cntct' in self._context:
                record.client_id.with_context({'rmv_prmry_cntct': True}).sudo().write(
                    {'contact_child_ids': [(3, record.partner_id.id)]})
            if record.is_secondary_contact and not 'rmv_scndr_cntct' in self._context:
                record.client_id.with_context({'rmv_scndr_cntct': True}).sudo().write(
                    {'secondary_contact_child_ids': [(3, record.partner_id.id)]})
            if record.is_auditor_contact and not 'rmv_auditor' in self._context:
                record.client_id.with_context({'rmv_auditor': True}).sudo().write(
                    {'auditor_contact_child_ids': [(3, record.partner_id.id)]})
            if record.is_corporate_banking_signatory and not 'rmv_signatory' in self._context:
                record.client_id.with_context({'rmv_signatory': True}).sudo().write(
                    {'signatory_contact_child_ids': [(3, record.partner_id.id)]})
            if record.is_hr_contact and not 'rmv_hr_cntct' in self._context:
                record.client_id.with_context({'rmv_hr_cntct': True}).sudo().write(
                    {'hr_contact_child_ids': [(3, record.partner_id.id)]})
            if record.is_client_finance_ac and not 'rmv_finance_cntct' in self._context:
                record.client_id.with_context({'rmv_finance_cntct': True}).sudo().write(
                    {'accounting_contact_ids': [(3, record.partner_id.id)]})
            if record.is_shareholder and not 'rmv_shareholder' in self._context:
                record.client_id.with_context({'rmv_shareholder': True}).sudo().write(
                    {'shareholder_contact_ids': [(3, record.partner_id.id)]})
            elif record.is_shareholder and not 'rmv_cr_ptnr' in self._context:
                if record.client_id.cr_document_id:
                    record.client_id.cr_document_id.with_context({'rmv_cr_ptnr': True}).sudo().write(
                        {'cr_partner_ids': [(3, record.partner_id.id)]})
            if record.is_manager_cr and not 'rmv_cr_mngr' in self._context:
                if record.client_id.cr_document_id:
                    record.client_id.cr_document_id.with_context({'rmv_cr_mngr': True}).sudo().write(
                        {'cr_managers_ids': [(3, record.partner_id.id)]})
            if record.is_manager_cl and not 'rmv_cl_mngr' in self._context:
                if record.client_id.cl_document_id:
                    record.client_id.cl_document_id.with_context({'rmv_cl_mngr': True}).sudo().write(
                        {'cl_partner_id': False})
            if record.is_aoa_finance_contact and not 'rmv_aoa_prtnr' in self._context:
                if record.client_id.aoa_document_id:
                    record.client_id.aoa_document_id.with_context({'rmv_aoa_prtnr': True}).sudo().write(
                        {'financial_link_partner': False})
            if record.is_general_manager and not 'rmv_aoa_prtnr' in self._context:
                if record.client_id.aoa_document_id:
                    record.client_id.aoa_document_id.with_context({'rmv_aoa_prtnr': True}).sudo().write(
                        {'general_manager': False})
            if record.is_general_secretary and not 'rmv_aoa_prtnr' in self._context:
                if record.client_id.aoa_document_id:
                    record.client_id.aoa_document_id.with_context({'rmv_aoa_prtnr': True}).sudo().write(
                        {'general_secretary': False})
            if record.is_admin_manager and not 'rmv_aoa_prtnr' in self._context:
                if record.client_id.aoa_document_id:
                    record.client_id.aoa_document_id.with_context({'rmv_aoa_prtnr': True}).sudo().write(
                        {'admin_manager': False})
            if record.is_corporate_banking_signatory and not 'rmv_aoa_prtnr' in self._context:
                if record.client_id.aoa_document_id:
                    record.client_id.aoa_document_id.with_context({'rmv_aoa_prtnr': True}).sudo().write(
                        {'banking_signatory': False})
            if record.is_liaison_officer and not 'rmv_aoa_prtnr' in self._context:
                if record.client_id.aoa_document_id:
                    record.client_id.aoa_document_id.with_context({'rmv_aoa_prtnr': True}).sudo().write(
                        {'liaison_officer': False})
            if record.is_manager_ec and not 'rmv_ec_mngr' in self._context:
                if record.client_id.ec_document_id:
                    record.client_id.ec_document_id.with_context({'rmv_ec_mngr': True}).sudo().write(
                        {'cr_authorizers_ids': [(3, record.partner_id.id)]})
        res = super(EbsClientContact, self).unlink()

        self.delete_context_data()
        return res

    def write(self, vals):
        for record in self:
            # If client is change, remove contacts from old client.
            if 'client_id' in vals:
                record.partner_id.write({'last_client_id': False})
                if record.partner_id.id in record.client_id.contact_child_ids.ids and not 'rmv_prmry_cntct' in self._context:
                    record.client_id.with_context({'rmv_prmry_cntct': True}).sudo().write(
                        {'contact_child_ids': [(3, record.partner_id.id)]})

                if record.partner_id.id in record.client_id.secondary_contact_child_ids.ids and not 'rmv_scndr_cntct' in self._context:
                    record.client_id.with_context({'rmv_scndr_cntct': True}).sudo().write(
                        {'secondary_contact_child_ids': [(3, record.partner_id.id)]})

                if record.partner_id.id in record.client_id.hr_contact_child_ids.ids and not 'rmv_hr_cntct' in self._context:
                    record.client_id.with_context({'rmv_hr_cntct': True}).sudo().write(
                        {'hr_contact_child_ids': [(3, record.partner_id.id)]})
                if record.partner_id.id in record.client_id.auditor_contact_child_ids.ids and not 'rmv_auditor' in self._context:
                    record.client_id.with_context({'rmv_auditor': True}).sudo().write(
                        {'auditor_contact_child_ids': [(3, record.partner_id.id)]})
                if record.partner_id.id in record.client_id.signatory_contact_child_ids.ids and not 'rmv_signatory' in self._context:
                    record.client_id.with_context({'rmv_signatory': True}).sudo().write(
                        {'signatory_contact_child_ids': [(3, record.partner_id.id)]})
                if record.partner_id.id in record.client_id.accounting_contact_ids.ids and not 'rmv_finance_cntct' in self._context:
                    record.client_id.with_context({'rmv_finance_cntct': True}).sudo().write(
                        {'accounting_contact_ids': [(3, record.partner_id.id)]})

                if record.partner_id.id in record.client_id.cr_document_id.cr_partner_ids.ids and not 'rmv_cr_ptnr' in self._context:
                    record.client_id.cr_document_id.with_context({'rmv_cr_ptnr': True}).sudo().write(
                        {'cr_partner_ids': [(3, record.partner_id.id)]})
                if record.partner_id.id in record.client_id.aoa_document_id.shareholder_contact_ids.ids and not 'rmv_aoa_ptnr' in self._context:
                    record.client_id.aoa_document_id.with_context({'rmv_aoa_ptnr': True}).sudo().write(
                        {'shareholder_contact_ids': [(3, record.partner_id.id)]})

                if record.partner_id.id in record.client_id.cr_document_id.cr_managers_ids.ids and not 'rmv_cr_mngr' in self._context:
                    record.client_id.cr_document_id.with_context({'rmv_cr_mngr': True}).sudo().write(
                        {'cr_managers_ids': [(3, record.partner_id.id)]})

                if record.partner_id.id == record.client_id.cl_manager_ids.id and not 'rmv_cl_mngr' in self._context:
                    record.client_id.cl_document_id.with_context({'rmv_cl_mngr': True}).sudo().write(
                        {'cl_partner_id': False})

                if record.partner_id.id == record.client_id.financial_link_partner.id and not 'rmv_aoa_prtnr' in self._context:
                    record.client_id.aoa_document_id.with_context({'rmv_aoa_prtnr': True}).sudo().write(
                        {'financial_link_partner': False})
                if record.partner_id.id == record.client_id.general_manager.id and not 'rmv_aoa_prtnr' in self._context:
                    record.client_id.aoa_document_id.with_context({'rmv_aoa_prtnr': True}).sudo().write(
                        {'general_manager': False})
                if record.partner_id.id == record.client_id.general_secretary.id and not 'rmv_aoa_prtnr' in self._context:
                    record.client_id.aoa_document_id.with_context({'rmv_aoa_prtnr': True}).sudo().write(
                        {'general_secretary': False})
                if record.partner_id.id == record.client_id.admin_manager.id and not 'rmv_aoa_prtnr' in self._context:
                    record.client_id.aoa_document_id.with_context({'rmv_aoa_prtnr': True}).sudo().write(
                        {'admin_manager': False})
                if record.partner_id.id == record.client_id.banking_signatory.id and not 'rmv_aoa_prtnr' in self._context:
                    record.client_id.aoa_document_id.with_context({'rmv_aoa_prtnr': True}).sudo().write(
                        {'banking_signatory': False})
                if record.partner_id.id == record.client_id.liaison_officer.id and not 'rmv_aoa_prtnr' in self._context:
                    record.client_id.aoa_document_id.with_context({'rmv_aoa_prtnr': True}).sudo().write(
                        {'liaison_officer': False})
                if record.partner_id.id in record.client_id.ec_document_id.cr_authorizers_ids.ids and not 'rmv_ec_mngr' in self._context:
                    record.client_id.ec_document_id.with_context({'rmv_ec_mngr': True}).sudo().write(
                        {'cr_authorizers_ids': [(3, record.partner_id.id)]})
        res = super(EbsClientContact, self).write(vals)
        # self.delete_context_data()
        for record in self:
            # Add contact in client based on changes done from line.
            if 'is_primary_contact' in vals or ('client_id' in vals and record.is_primary_contact):
                if record.is_primary_contact and not 'add_prmry_cntct' in self._context:
                    record.client_id.with_context({'add_prmry_cntct': True}).sudo().write(
                        {'contact_child_ids': [(4, record.partner_id.id)]})
                elif record.partner_id.id in record.client_id.contact_child_ids.ids and not 'rmv_prmry_cntct' in self._context:
                    record.client_id.with_context({'rmv_prmry_cntct': True}).sudo().write(
                        {'contact_child_ids': [(3, record.partner_id.id)]})
            if 'is_secondary_contact' in vals or ('client_id' in vals and record.is_secondary_contact):
                if record.is_secondary_contact and not 'add_scndr_cntct' in self._context:
                    record.client_id.with_context({'add_scndr_cntct': True}).sudo().write(
                        {'secondary_contact_child_ids': [(4, record.partner_id.id)]})
                elif record.partner_id.id in record.client_id.secondary_contact_child_ids.ids and not 'rmv_scndr_cntct' in self._context:
                    record.client_id.with_context({'rmv_scndr_cntct': True}).sudo().write(
                        {'secondary_contact_child_ids': [(3, record.partner_id.id)]})
            if 'is_auditor_contact' in vals or ('client_id' in vals and record.is_auditor_contact):
                if record.is_auditor_contact and not 'add_auditor' in self._context:
                    record.client_id.with_context({'add_auditor': True}).sudo().write(
                        {'auditor_contact_child_ids': [(4, record.partner_id.id)]})
                elif record.partner_id.id in record.client_id.auditor_contact_child_ids.ids and not 'rmv_auditor' in self._context:
                    record.client_id.with_context({'rmv_auditor': True}).sudo().write(
                        {'auditor_contact_child_ids': [(3, record.partner_id.id)]})
            if 'is_corporate_banking_signatory' in vals or (
                    'client_id' in vals and record.is_corporate_banking_signatory):
                if record.is_corporate_banking_signatory and not 'add_auditor' in self._context:
                    record.client_id.with_context({'add_signatory': True}).sudo().write(
                        {'signatory_contact_child_ids': [(4, record.partner_id.id)]})
                elif record.partner_id.id in record.client_id.signatory_contact_child_ids.ids and not 'rmv_signatory' in self._context:
                    record.client_id.with_context({'rmv_signatory': True}).sudo().write(
                        {'signatory_contact_child_ids': [(3, record.partner_id.id)]})
            if 'is_hr_contact' in vals or ('client_id' in vals and record.is_hr_contact):
                if record.is_hr_contact and not 'add_hr_cntct' in self._context:
                    record.client_id.with_context({'add_hr_cntct': True}).sudo().write(
                        {'hr_contact_child_ids': [(4, record.partner_id.id)]})
                elif record.partner_id.id in record.client_id.hr_contact_child_ids.ids and not 'rmv_hr_cntct' in self._context:
                    record.client_id.with_context({'rmv_hr_cntct': True}).sudo().write(
                        {'hr_contact_child_ids': [(3, record.partner_id.id)]})
            if 'is_client_finance_ac' in vals or ('client_id' in vals and record.is_client_finance_ac):
                if record.is_client_finance_ac and not 'add_finance_cntct' in self._context:
                    record.client_id.with_context({'add_finance_cntct': True}).sudo().write(
                        {'accounting_contact_ids': [(4, record.partner_id.id)]})
                elif record.partner_id.id in record.client_id.accounting_contact_ids.ids and not 'rmv_finance_cntct' in self._context:
                    record.client_id.with_context({'rmv_finance_cntct': True}).sudo().write(
                        {'accounting_contact_ids': [(3, record.partner_id.id)]})
            if ('is_shareholder' in vals or (
                    'client_id' in vals and record.is_shareholder)) and not 'aoa_document' in self._context:

                if not record.is_shareholder:
                    record.client_id.with_context({'rmv_shareholder': True}).write(
                        {'shareholder_contact_ids': [(3, record.partner_id.id)]})

                    if record.partner_id.id in record.client_id.cr_document_id.cr_partner_ids.ids and not 'rmv_cr_ptnr' in self._context:
                        record.client_id.cr_document_id.with_context({'rmv_cr_ptnr': True}).sudo().write(
                            {'cr_partner_ids': [(3, record.partner_id.id)]})

                if record.is_shareholder:
                    if not 'add_cr_ptnr' in self._context:
                        record.client_id.cr_document_id.with_context({'add_cr_ptnr': True}).sudo().write(
                            {'cr_partner_ids': [(4, record.partner_id.id)]})

            if ('is_manager_cr' in vals or ('client_id' in vals and record.is_manager_cr)):
                cr_doc_type = record.client_id.document_o2m.filtered(
                    lambda x: x.is_client_rel and x.document_type_name == 'Commercial Registration (CR) Application')
                if not record.client_id.cr_document_id and (
                        not self._context.get('default_is_client_rel') and not cr_doc_type):
                    raise ValidationError(
                        _("This record does not have commercial registration document or may be does not have client."))
                if record.is_manager_cr and not 'add_cr_mngr' in self._context:
                    record.client_id.cr_document_id.with_context({'add_cr_mngr': True}).sudo().write(
                        {'cr_managers_ids': [(4, record.partner_id.id)]})
                elif record.partner_id.id in record.client_id.cr_document_id.cr_managers_ids.ids and not 'rmv_cr_mngr' in self._context:
                    record.client_id.cr_document_id.with_context({'rmv_cr_mngr': True}).sudo().write(
                        {'cr_managers_ids': [(3, record.partner_id.id)]})
            if ('is_manager_cl' in vals or ('client_id' in vals and record.is_manager_cl)):
                cl_doc_type = record.client_id.document_o2m.filtered(
                    lambda x: x.is_client_rel and x.document_type_name == 'Commercial License')
                if not record.client_id.cl_document_id and (
                        not self._context.get('default_is_client_rel') and not cl_doc_type):
                    raise ValidationError(
                        _("This record does not have commercial license document or may be does not have client."))
                if record.is_manager_cl and not 'add_cl_mngr' in self._context:
                    record.client_id.cl_document_id.with_context({'add_cl_mngr': True}).sudo().write(
                        {'cl_partner_id': record.partner_id.id})
                elif record.partner_id.id == record.client_id.cl_manager_ids.id and not 'rmv_cl_mngr' in self._context:
                    record.client_id.cl_document_id.with_context({'rmv_cl_mngr': True}).sudo().write(
                        {'cl_partner_id': False})
            if ('is_aoa_finance_contact' in vals or ('client_id' in vals and record.is_aoa_finance_contact)):
                aoa_doc_type = record.client_id.document_o2m.filtered(
                    lambda x: x.is_client_rel and x.document_type_name == 'articles of association')
                if not record.client_id.aoa_document_id and (
                        not self._context.get('default_is_client_rel') and not aoa_doc_type):
                    raise ValidationError(
                        _("This record does not have Article of Association document or may be does not have client."))
                if record.is_aoa_finance_contact and not 'add_aoa_prtnr' in self._context:
                    record.client_id.aoa_document_id.with_context({'add_aoa_prtnr': True}).sudo().write(
                        {'financial_link_partner': record.partner_id.id})
                elif record.partner_id.id == record.client_id.financial_link_partner.id and not 'rmv_aoa_prtnr' in self._context:
                    record.client_id.aoa_document_id.with_context({'rmv_aoa_prtnr': True}).sudo().write(
                        {'financial_link_partner': False})
            if ('is_general_manager' in vals or ('client_id' in vals and record.is_general_manager)):
                aoa_doc_type = record.client_id.document_o2m.filtered(
                    lambda x: x.is_client_rel and x.document_type_name == 'articles of association')
                if not record.client_id.aoa_document_id and (
                        not self._context.get('default_is_client_rel') and not aoa_doc_type):
                    raise ValidationError(
                        _("This record does not have Article of Association document or may be does not have client."))
                if record.is_general_manager and not 'add_aoa_prtnr' in self._context:
                    record.client_id.aoa_document_id.with_context({'add_aoa_prtnr': True}).sudo().write(
                        {'general_manager': record.partner_id.id})
                elif record.partner_id.id == record.client_id.general_manager.id and not 'rmv_aoa_prtnr' in self._context:
                    record.client_id.aoa_document_id.with_context({'rmv_aoa_prtnr': True}).sudo().write(
                        {'general_manager': False})
            if ('is_general_secretary' in vals or ('client_id' in vals and record.is_general_secretary)):
                aoa_doc_type = record.client_id.document_o2m.filtered(
                    lambda x: x.is_client_rel and x.document_type_name == 'articles of association')
                if not record.client_id.aoa_document_id and (
                        not self._context.get('default_is_client_rel') and not aoa_doc_type):
                    raise ValidationError(
                        _("This record does not have Article of Association document or may be does not have client."))
                if record.is_general_secretary and not 'add_aoa_prtnr' in self._context:
                    record.client_id.aoa_document_id.with_context({'add_aoa_prtnr': True}).sudo().write(
                        {'general_secretary': record.partner_id.id})
                elif record.partner_id.id == record.client_id.general_secretary.id and not 'rmv_aoa_prtnr' in self._context:
                    record.client_id.aoa_document_id.with_context({'rmv_aoa_prtnr': True}).sudo().write(
                        {'general_secretary': False})
            if ('is_admin_manager' in vals or ('client_id' in vals and record.is_admin_manager)):
                aoa_doc_type = record.client_id.document_o2m.filtered(
                    lambda x: x.is_client_rel and x.document_type_name == 'articles of association')
                if not record.client_id.aoa_document_id and (
                        not self._context.get('default_is_client_rel') and not aoa_doc_type):
                    raise ValidationError(
                        _("This record does not have Article of Association document or may be does not have client."))
                if record.is_admin_manager and not 'add_aoa_prtnr' in self._context:
                    record.client_id.aoa_document_id.with_context({'add_aoa_prtnr': True}).sudo().write(
                        {'admin_manager': record.partner_id.id})
                elif record.partner_id.id == record.client_id.admin_manager.id and not 'rmv_aoa_prtnr' in self._context:
                    record.client_id.aoa_document_id.with_context({'rmv_aoa_prtnr': True}).sudo().write(
                        {'admin_manager': False})
            if ('is_corporate_banking_signatory' in vals or (
                    'client_id' in vals and record.is_corporate_banking_signatory)):
                aoa_doc_type = record.client_id.document_o2m.filtered(
                    lambda x: x.is_client_rel and x.document_type_name == 'articles of association')
                if not record.client_id.aoa_document_id and (
                        not self._context.get('default_is_client_rel') and not aoa_doc_type):
                    raise ValidationError(
                        _("This record does not have Article of Association document or may be does not have client."))
                if record.is_corporate_banking_signatory and not 'add_aoa_prtnr' in self._context:
                    record.client_id.aoa_document_id.with_context({'add_aoa_prtnr': True}).sudo().write(
                        {'banking_signatory': record.partner_id.id})
                elif record.partner_id.id == record.client_id.banking_signatory.id and not 'rmv_aoa_prtnr' in self._context:
                    record.client_id.aoa_document_id.with_context({'rmv_aoa_prtnr': True}).sudo().write(
                        {'banking_signatory': False})
            if ('is_liaison_officer' in vals or ('client_id' in vals and record.is_liaison_officer)):
                aoa_doc_type = record.client_id.document_o2m.filtered(
                    lambda x: x.is_client_rel and x.document_type_name == 'articles of association')
                if not record.client_id.aoa_document_id and (
                        not self._context.get('default_is_client_rel') and not aoa_doc_type):
                    raise ValidationError(
                        _("This record does not have Article of Association document or may be does not have client."))
                if record.is_liaison_officer and not 'add_aoa_prtnr' in self._context:
                    record.client_id.aoa_document_id.with_context({'add_aoa_prtnr': True}).sudo().write(
                        {'liaison_officer': record.partner_id.id})
                elif record.partner_id.id == record.client_id.liaison_officer.id and not 'rmv_aoa_prtnr' in self._context:
                    record.client_id.aoa_document_id.with_context({'rmv_aoa_prtnr': True}).sudo().write(
                        {'liaison_officer': False})
            if ('is_manager_ec' in vals or ('client_id' in vals and record.is_manager_ec)):
                ec_doc_type = record.client_id.document_o2m.filtered(
                    lambda x: x.is_client_rel and x.document_type_name == 'Establishment Card')
                if not record.client_id.ec_document_id and (
                        not self._context.get('default_is_client_rel') and not ec_doc_type):
                    raise ValidationError(
                        _("This record does not have establishment card document or may be does not have client."))
                if record.is_manager_ec and not 'add_ec_mngr' in self._context:
                    record.client_id.ec_document_id.with_context({'add_ec_mngr': True}).sudo().write(
                        {'cr_authorizers_ids': [(4, record.partner_id.id)]})
                elif record.partner_id.id in record.client_id.ec_document_id.cr_authorizers_ids.ids and not 'r_ec_m' in self._context:
                    record.client_id.ec_document_id.with_context({'rmv_ec_mngr': True}).sudo().write(
                        {'cr_authorizers_ids': [(3, record.partner_id.id)]})

        self.delete_context_data()
        return res
