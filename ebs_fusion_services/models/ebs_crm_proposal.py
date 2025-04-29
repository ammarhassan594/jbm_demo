from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from datetime import datetime

# from googletrans import Translator, constants
import logging

_logger = logging.getLogger(__name__)

try:
    from num2words import num2words
except ImportError:
    _logger.warning("The num2words python library is not installed, amount-to-text features won't be fully available.")
    num2words = None


class ebsCrmProposal(models.Model):
    _name = 'ebs.crm.proposal'
    _description = 'Contract'
    _rec_name = 'contract_no'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'

    name = fields.Char("Name")
    lead_id = fields.Many2one('crm.lead', string="Deal")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    proposal_company_ids = fields.Many2many('res.company', string='Proposal Company')

    start_date = fields.Date('Start Date', default=datetime.today(), required=1)
    end_date = fields.Date('End Date', readonly=1)
    duration = fields.Integer('Duration (in Months)', default=12)
    date = fields.Date('Date', required=1, default=datetime.today())
    contact_id = fields.Many2one('res.partner', string='Client', required=1,
                                 domain="[ ('is_company', '=', True),('parent_id', '=', False)]")
    amount = fields.Float('Contract Amount', compute='compute_amount')

    real_revenue = fields.Float("Total Invoice Amount", compute='compute_real_revenue')

    state = fields.Selection([('draft', 'Draft'), ('active', 'Active'), ('termination', 'Under Termination'),
                              ('cancelled', 'Cancelled')], default='draft', string="Status")
    proposal_lines = fields.One2many('ebs.crm.proposal.line', 'proposal_id', 'Proposal Service Lines', copy=True)
    invoice_id = fields.Many2one('account.move', 'Invoice', copy=False, readonly=True,
                                 domain=[('move_type', '=', 'out_invoice')])
    invoice_count = fields.Integer('Invoice Count', compute='_compute_invoice_count')
    original_proposal_id = fields.Many2one('ebs.crm.proposal', 'Original Proposal')

    type = fields.Selection([('proposal', 'Proposal'), ('agreement', 'Agreement')], string='Type')
    contract_types = fields.Selection([('liability', 'Limited Liability Company'), ('pro', 'PRO Services Agreement'),
                                       ('closure', 'Company Closure'), ('foreign', 'Foreign Branch Office'),
                                       ('trade', 'Trade Representative Office'),
                                       ('outsourcing', 'Fusion Outsourcing Sponsored Employee'),
                                       ('other', 'Other')], string='Contract Details')

    further_info = fields.Text('Further Information')
    is_limited = fields.Boolean('Limited')
    number_of_individuals = fields.Integer('Number of Individuals', default=0)
    fos_employee_ids = fields.One2many('ebs.crm.proposal.employee.line', 'proposal_id', string='FOS Employees')

    legal_contact_id = fields.Many2one('res.partner', 'Legal Contact',
                                       domain="[('parent_id','=',contact_id),('parent_id','!=',False)]")
    auditor_contact_id = fields.Many2one('res.partner', 'Auditor Contact',
                                         domain="[('parent_id','=',contact_id),('parent_id','!=',False)]")
    referral_contact_id = fields.Many2one('res.partner', 'Referral Contact',
                                          domain="[('parent_id','=',contact_id),('parent_id','!=',False)]")
    shareholder_contact_id = fields.Many2one('res.partner', 'Shareholder Contact',
                                             domain="[('parent_id','=',contact_id),('is_shareholder','=',True),('parent_id','!=',False)]")
    authorised_contact_id = fields.Many2one('res.partner', 'Authorised Representative',
                                            domain="[('parent_id','=',contact_id),('is_authorised_signatory','=',True),('parent_id','!=',False)]")
    general_manager_id = fields.Many2one('res.partner', 'General Manager',
                                         domain="[('parent_id','=',contact_id),('parent_id','!=',False)]")
    country_manager_id = fields.Many2one('res.partner', 'Country Manager',
                                         domain="[('parent_id','=',contact_id),('parent_id','!=',False)]")
    manager_cr_id = fields.Many2one('res.partner', 'Manager CR',
                                    domain="[('parent_id','=',contact_id),('parent_id','!=',False)]")
    manager_ec_id = fields.Many2one('res.partner', 'Manager EC',
                                    domain="[('parent_id','=',contact_id),('parent_id','!=',False)]")
    client_hr_id = fields.Many2one('res.partner', 'Client HR',
                                   domain="[('parent_id','=',contact_id),('parent_id','!=',False)]")
    client_finance_id = fields.Many2one('res.partner', 'Client Finance/Accounts')
    other_contact_id = fields.Many2one('res.partner', 'Other',
                                       domain="[('parent_id','=',contact_id),('parent_id','!=',False)]")
    further_info_contact = fields.Text('Further Information')
    share_capital_amount = fields.Float('Share Capital Amount')
    shareholding_percentage = fields.Float('Shareholding Percentage')
    profit_share_percentage = fields.Float('Profit Share Percentage')
    fme = fields.Boolean('FME')
    fss = fields.Boolean('FSS')
    fos = fields.Boolean('FOS')
    is_invoiced = fields.Boolean(compute='compute_is_invoiced')
    contract_type = fields.Selection([
        ('fme', 'FME'),
        ('fss', 'FSS'),
        ('fos', 'FOS'),
    ], string="Contract Type", default="fme")
    formation_fees = fields.Many2one('ebs.crm.contract.fees', 'Formation Fees')
    annual_service_fees = fields.Many2one('ebs.crm.contract.fees', 'Annual Service Fees', domain="[('fme','=',True)]")
    annual_service_fees_first = fields.Many2one('ebs.crm.contract.fees', 'Annual Service Fees First Year',
                                                domain="[('fme','=',True)]")
    annual_service_fees_second = fields.Many2one('ebs.crm.contract.fees', 'Annual Service Fees Second Year',
                                                 domain="[('fme','=',True)]")
    annual_service_fees_third = fields.Many2one('ebs.crm.contract.fees', 'Annual Service Fees Third Year',
                                                domain="[('fme','=',True)]")
    turnover = fields.Float('Annual Turnover')
    annual_payment = fields.Float('Annual Payment')
    annual_license_renewal_fees = fields.Many2one('ebs.crm.contract.fees', 'Annual License Renewal Fees')
    pro_service_fees = fields.Many2one('ebs.crm.contract.fees', 'PRO Service Fees')
    payment_terms = fields.Selection([('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('halfyearly', 'Half Yearly'),
                                      ('yearlyupfront', 'Yearly Upfront'), ('other', 'Other')], string='Payment Terms')
    payment_terms_id = fields.Many2one('account.payment.term', string='Payment Terms')
    mode_of_payment = fields.Char('Mode of Payment')
    payment_comments = fields.Text('Comments')
    fees_ids = fields.One2many('ebs.crm.employee.onetime.fees', 'proposal_id', 'Fees')
    contract_fees_ids = fields.One2many('ebs.contract.proposal.fees', 'contract_id', 'Fees')
    invoice_month_list = fields.Char('Monthly Invoice List')
    contract_no = fields.Char('Contract Number')
    penalty_amount_percentage = fields.Char('Penalty Amount', translate=True)
    penalty_amount = fields.Float('Penalty Amount')
    Obligations_service_provider = fields.Boolean("Obligations Service Provider")
    complaint_response_time = fields.Integer("Complaint Response Time")
    complaint_response_word = fields.Char("Complaint Response in Word")
    transfer_personnel_employment = fields.Boolean("Transfer of Personnel’s Employment to the Company")
    general_description = fields.Boolean("General Description")
    general_description_of_the_services = fields.Html("General Description of the Services")
    deposit_amount = fields.Float("Deposit Amount")
    insurance_amount = fields.Float("Insurance Amount")
    total_service_fee = fields.Float("Total Service Fee")
    total_service_fee_word = fields.Char("Total Service Fee in word")
    monthly_service_fee = fields.Float("Monthly Service Fee")
    monthly_service_fee_word = fields.Char("Monthly Service Fee in Word", translate=True)
    advance_payment_amount_percentage = fields.Float("Advance Payment Amount")
    advance_payment_amount_percentage_in_word = fields.Char("Advance Payment Amount In Word", translate=True)
    company_currency_id = fields.Many2one('res.currency', string="Currency")
    contract_id = fields.Many2one('ebs.crm.proposal')
    penalty_amount_total_words = fields.Char("Penalty Amount In Words", translate=True)
    related_contact_ids = fields.One2many('contract.client.contacts', 'contract_id', string="Related Contacts",
                                          compute='compute_related_contact_ids')
    submitted_by_client = fields.Boolean(string="Confirmed By Client", default=False)
    deferred_revenues_count = fields.Integer(compute='deferred_revenues_compute_count')
    payments_count = fields.Integer(compute='payments_compute_count')
    document_count = fields.Integer(compute='compute_document_count')
    email = fields.Char(string="Email")
    fos_fee_structure_ids = fields.One2many('ebs.proposal.fos.fee.structure', 'contract_id',
                                            string="FOS Fees Structure")
    salary_structure_ids = fields.One2many('ebs.proposal.salary.structure', 'contract_id',
                                           string="Monthly Salary Breakdown")
    permit_issuance_ids = fields.One2many('ebs.proposal.permit.issuance', 'contract_id', string="Work Permit Issuance")
    service_fee_per_employee = fields.Float(string="Service Fee Per Employee")

    @api.onchange('client_finance_id')
    def onchange_client_finance_id(self):
        if self.client_finance_id:
            self.email = self.client_finance_id.email
        else:
            self.email = False

    @api.depends('contract_fees_ids')
    def compute_is_invoiced(self):
        for rec in self:
            rec.is_invoiced = False

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

    def open_send_mail_wizard(self):
        if not self.email:
            raise UserError(_('Email Is Required To Send Contract.'))
        mail_template = self.env.ref('ebs_fusion_services.mail_template_contract')
        ctx = {
            'model': 'ebs.crm.proposal',
            'res_id': self.id,
            'default_email_to': self.email,
            'document_ids': self.env['documents.document'].search([('proposal_id', '=', self.id)]).ids,
            'template_id': mail_template.id,
            'contract_send': True
        }
        return {
            'name': ('Send Contract'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'send.mail.wizard',
            'target': 'new',
            'context': ctx,
        }

    def get_document(self):
        action = self.env.ref('documents.document_action').read()[0]
        action['domain'] = [('proposal_id', '=', self.id)]
        action['context'] = {
            'create': 0,
        }

        return action

    def compute_document_count(self):
        for record in self:
            record.document_count = self.env['documents.document'].search_count(
                [('proposal_id', '=', self.id)])

    @api.model
    def default_get(self, fields):
        res = super(ebsCrmProposal, self).default_get(fields)
        if res.get('lead_id') or 'lead_id' in self._context:
            if res.get('lead_id'):
                lead_id = self.env['crm.lead'].browse(res.get('lead_id'))
            if 'lead_id' in self._context:
                lead_id = self.env['crm.lead'].browse(self._context.get('lead_id'))
            currency_id = self.env['res.currency'].search([('name', '=', 'QAR')])
            res.update({
                'email': lead_id.email_from,
                'total_service_fee': lead_id.total_service_fee,
                'monthly_service_fee': lead_id.monthly_service_fee,
                'advance_payment_amount_percentage': lead_id.advance_payment_amount_percentage,
                'deposit_amount': lead_id.deposit_amount,
                'penalty_amount': lead_id.penalty_amount,
                'insurance_amount': lead_id.insurance_amount,
                'turnover': lead_id.annual_turnover,
                'annual_payment': lead_id.annual_payment,
                'company_currency_id': currency_id.id
            })
        return res

    def deferred_revenues_compute_count(self):
        for record in self:
            record.deferred_revenues_count = self.env['account.asset'].search_count(
                [('contract_id', '=', self.id), ('asset_type', '=', 'sale'), ('state', '!=', 'model'),
                 ('parent_id', '=', False)])

    def payments_compute_count(self):
        for record in self:
            record.payments_count = self.env['account.payment'].search_count(
                [('contract_id', '=', self.id)])

    def get_deferred_revenue(self):
        action = self.env.ref('account_asset.action_account_revenue_form').read()[0]
        action['context'] = {
            'default_contract_id': self.id,
            'asset_type': 'sale',
            'default_asset_type': 'sale'
        }
        action['domain'] = [('contract_id', '=', self.id), ('asset_type', '=', 'sale'), ('state', '!=', 'model'),
                            ('parent_id', '=', False)]
        return action

    def get_payments(self):
        action = self.env.ref('account.action_account_payments_payable').read()[0]
        action['context'] = {
            'default_contract_id': self.id,
        }
        action['domain'] = [('contract_id', '=', self.id)]
        return action

    def confirm_contract(self):
        for rec in self:
            rec.write({'state': 'active'})

    @api.depends('contact_id')
    def compute_related_contact_ids(self):
        for rec in self:
            realtion_lines = self.env['contract.client.contacts'].search([('contract_id', '=', rec.id)])
            if realtion_lines:
                realtion_lines.write({'contract_id': False})
            client_contact_rel_lines = self.env['ebs.client.contact'].search([('client_id', '=', rec.contact_id.id)])
            lines = []
            for line in client_contact_rel_lines:
                line_val = {}
                line_val.update({'partner_id': line.partner_id.id, 'contract_id': rec.id})
                tag_ids = []
                if line.is_primary_contact:
                    tag = self.env['client.contact.relation.tags'].search([('name', '=', 'Primary Contact')])
                    tag_ids.append(tag.id)
                if line.is_secondary_contact:
                    tag = self.env['client.contact.relation.tags'].search([('name', '=', 'Secondary Contact')])
                    tag_ids.append(tag.id)
                if line.is_manager_cr:
                    tag = self.env['client.contact.relation.tags'].search([('name', '=', 'Manager CR')])
                    tag_ids.append(tag.id)
                if line.is_manager_ec:
                    tag = self.env['client.contact.relation.tags'].search([('name', '=', 'Manager EC')])
                    tag_ids.append(tag.id)
                if line.is_manager_cl:
                    tag = self.env['client.contact.relation.tags'].search([('name', '=', 'Manager CL')])
                    tag_ids.append(tag.id)
                if line.is_deliver_partner:
                    tag = self.env['client.contact.relation.tags'].search([('name', '=', 'Deliver Partner')])
                    tag_ids.append(tag.id)
                if line.is_shareholder:
                    tag = self.env['client.contact.relation.tags'].search([('name', '=', 'Shareholder')])
                    tag_ids.append(tag.id)
                if line.is_authorised_signatory:
                    tag = self.env['client.contact.relation.tags'].search([('name', '=', 'Authorised Signatory')])
                    tag_ids.append(tag.id)
                if line.is_legal_contact:
                    tag = self.env['client.contact.relation.tags'].search([('name', '=', 'Legal Contact')])
                    tag_ids.append(tag.id)
                if line.is_auditor_contact:
                    tag = self.env['client.contact.relation.tags'].search([('name', '=', 'Auditor Contact')])
                    tag_ids.append(tag.id)
                if line.is_general_manager:
                    tag = self.env['client.contact.relation.tags'].search([('name', '=', 'General Manager')])
                    tag_ids.append(tag.id)
                if line.is_client_finance_ac and line.partner_id.id == rec.client_finance_id.id:
                    tag = self.env['client.contact.relation.tags'].search([('name', '=', 'Client Finance/Accounts')])
                    tag_ids.append(tag.id)
                if len(tag_ids) > 0:
                    line_val.update({'relation_tag_ids': [(6, 0, tag_ids)]})
                    line_id = self.env['contract.client.contacts'].create(line_val)
                    lines.append(line_id.id)
            if lines:
                rec.related_contact_ids = lines
            else:
                rec.related_contact_ids = False

    @api.onchange('total_service_fee', 'monthly_service_fee', 'advance_payment_amount_percentage', 'contact_id')
    def _onchange_amount_arabic(self):
        for rec in self.company_currency_id:
            self.total_service_fee_word = rec.amount_to_text(self.total_service_fee)
            self.monthly_service_fee_word = rec.amount_to_text(self.monthly_service_fee)
            self.advance_payment_amount_percentage_in_word = rec.amount_to_text(self.advance_payment_amount_percentage)

    @api.onchange('penalty_amount')
    def _onchange_penalty_amount(self):
        for rec in self.company_currency_id:
            penalty = rec.amount_to_text(self.penalty_amount).lower()
            self.penalty_amount_total_words = "".join(penalty.split()[:1])

    @api.onchange('complaint_response_time')
    def _onchange_complaint_response(self):
        for rec in self.company_currency_id:
            complaint_response = rec.amount_to_text(self.complaint_response_time).lower()
            self.complaint_response_word = "".join(complaint_response.split()[:1])
            print("complaint response", self.complaint_response_word)

    @api.model
    def create(self, vals):
        if vals.get('lead_id') and vals.get('type') == 'agreement':
            proposal_ids = self.env['ebs.crm.proposal'].search(
                [('lead_id', '=', vals.get('lead_id')), ('type', '=', 'agreement')])
            if proposal_ids:
                proposal_ids.write({'state': 'cancelled'})

        res = super(ebsCrmProposal, self).create(vals)
        if res.type == 'proposal':
            if not res.company_id.company_code:
                raise UserError(_("Please Fill Company Code."))
            rec_name = res.company_id.company_code + str(datetime.now().hour + 3) + date.today().strftime("%d%m%Y")
            res.write({'contract_no': rec_name})
            # if contact added in contract, create client contact relation for client finance ac
            if vals.get('client_finance_id'):
                partner = self.env['res.partner'].browse([vals.get('client_finance_id')])
                available_client_line = partner.client_contact_rel_ids.filtered(
                    lambda o: o.client_id.id == vals.get('contact_id'))
                if available_client_line:
                    available_client_line.write({'is_client_finance_ac': True})
                else:
                    partner.write({'client_contact_rel_ids': [(0, 0, {
                        'client_id': vals.get('contact_id'),
                        'is_client_finance_ac': True
                    })]})
        return res

    def write(self, vals):
        print("====================", vals)
        # if contact added in contract, create client contact relation for client finance ac
        if self.type == 'proposal' and 'client_finance_id' in vals:
            if vals.get('client_finance_id') == False:
                available_client_line = self.client_finance_id.client_contact_rel_ids.filtered(
                    lambda o: o.client_id.id in [vals.get('contact_id') or self.contact_id.id])
                if available_client_line:
                    available_client_line.write({'is_client_finance_ac': False})

            else:
                if self.client_finance_id:
                    available_past_client_line = self.client_finance_id.client_contact_rel_ids.filtered(
                        lambda o: o.client_id.id in [vals.get('contact_id') or self.contact_id.id])
                    if available_past_client_line:
                        available_past_client_line.write({'is_client_finance_ac': False})
                partner = self.env['res.partner'].browse([vals.get('client_finance_id')])
                available_client_line = partner.client_contact_rel_ids.filtered(
                    lambda o: o.client_id.id in [vals.get('contact_id') or self.contact_id.id])
                if available_client_line:
                    available_client_line.write({'is_client_finance_ac': True})
                else:
                    partner.write({'client_contact_rel_ids': [
                        (0, 0, {'client_id': self.contact_id.id, 'is_client_finance_ac': True})]})

        if vals.get('state') == 'cancelled':
            lq_sublines = self.env['labor.quota.subline'].search([('contract_id', '=', self.id)])
            if lq_sublines:
                for line in lq_sublines:
                    line.unlink()

        res = super(ebsCrmProposal, self).write(vals)
        if self.state == 'active':
            invoices = self.env['account.move'].sudo().search([('prop_id', '=', self.id)])
            payments = self.env['account.payment'].sudo().search([('contract_id', '=', self.id)])
            for line in self.contract_fees_ids:
                if not line.next_invoice_date or (not line.invoice_ids.ids and not line.payment_ids.ids):
                    line.write({'next_invoice_date': self.start_date})
        return res

    def compute_amount(self):
        for rec in self:
            amount = 0.0
            if rec.proposal_lines:
                amount = sum(rec.proposal_lines.mapped('govt_fees')) + sum(rec.proposal_lines.mapped('fusion_fees'))
            rec.amount = amount

    @api.onchange('contract_type')
    def onchange_contract_type(self):
        for rec in self:
            rec.fme = False
            rec.fss = False
            rec.fos = False
            if rec.contract_type == 'fme':
                rec.fme = True
            elif rec.contract_type == 'fss':
                rec.fss = True
            elif rec.contract_type == 'fos':
                rec.fos = True

    def action_view_contract(self):
        self.ensure_one()
        action = self.env.ref('ebs_fusion_services.action_ebs_crm_proposal').read()[0]
        contract_ids = self.env['ebs.crm.proposal'].search(
            [('contact_id', '=', self.contact_id.id), ('type', '=', 'proposal')])
        if contract_ids:
            action['context'] = {'default_type': 'proposal',
                                 'default_lead_id': self.lead_id.id,
                                 'default_contact_id': self.contact_id.id,
                                 'default_company_id': self.lead_id.company_id.id,
                                 'default_date': date.today(),
                                 'proposal_id': self.id,
                                 }
            action['views'] = [(self.env.ref('ebs_fusion_services.view_ebs_crm_contract_tree').id, 'tree'),
                               (self.env.ref('ebs_fusion_services.view_ebs_crm_proposal_form').id, 'form')]
            action['view_mode'] = 'tree'
            action['domain'] = [('id', 'in', contract_ids.ids)]
            return action
        action['views'] = [(self.env.ref('ebs_fusion_services.view_ebs_crm_proposal_form').id, 'form')]
        action['view_mode'] = 'form'
        action['target'] = 'self'
        action['context'] = {'default_type': 'proposal',
                             'default_lead_id': self.lead_id.id,
                             'default_contact_id': self.contact_id.id,
                             'default_company_id': self.lead_id.company_id.id,
                             'default_date': date.today(),
                             'proposal_id': self.id,
                             }
        return action

    def fetch_child_id_address(self):
        partner_id = self.env['res.partner'].search(
            [('parent_id', '=', self.contact_id.id), ('address_type', '=', 'national_address')])
        if partner_id:
            partner_id = partner_id[0]
        return partner_id

    def _get_eng_to_arabic(self, field, model, id):
        rec = self.env['ir.translation'].search(
            [('name', '=', model + ',' + field), ('lang', '=', 'ar_SY'), ('res_id', '=', id)])
        print("recccccccccccccccccccccccccccccccccccccccccccc", rec.name)
        return rec.value or ''

    def get_translate_text(self, translator, word):
        translation = translator.translate(word, src="en", dest="ar")
        print("translation_translationtranslationtranslation", translation)
        return translation.text

    @api.onchange('company_id')
    def onchange_currency(self):
        for rec in self:
            if rec.type == 'proposal':
                if rec.company_id.currency_id:
                    rec.company_currency_id = rec.company_id.currency_id
            else:
                rec.company_currency_id = False

    @api.onchange('duration', 'start_date')
    def onchange_duration(self):
        for rec in self:
            if rec.start_date:
                if rec.duration == 0:
                    rec.end_date = ''
                else:
                    rec.end_date = rec.start_date + relativedelta(months=rec.duration)

    @api.onchange('end_date')
    def onchange_end_date(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                if rec.end_date <= rec.start_date:
                    rec.end_date = False
                    raise ValidationError('End Date should be greater than start date')
                rec.duration = (rec.end_date.year - rec.start_date.year) * 12 + (
                        rec.end_date.month - rec.start_date.month)

    @api.onchange('state')
    def onchange_status(self):
        for rec in self:

            if rec.state == 'active':
                contract_ids = self.env['ebs.crm.proposal'].search(
                    [('lead_id', '=', rec.lead_id.id), ('type', '=', 'proposal')]) - rec._origin
                stage_id = self.env['crm.stage'].search([('code', '=', 8)])
                if contract_ids:
                    if all(contract.state == 'active' for contract in contract_ids) and rec.lead_id.stage_code == 7:
                        rec.lead_id.stage_id = stage_id.id
                else:
                    rec.lead_id.stage_id = stage_id.id

    @api.onchange('lead_id')
    def _onchange_lead(self):
        self.total_service_fee = self.lead_id.total_service_fee
        self.monthly_service_fee = self.lead_id.monthly_service_fee
        self.advance_payment_amount_percentage = self.lead_id.advance_payment_amount_percentage
        self.deposit_amount = self.lead_id.deposit_amount
        self.penalty_amount = self.lead_id.penalty_amount
        self.insurance_amount = self.lead_id.insurance_amount
        self.turnover = self.lead_id.annual_turnover
        self.annual_payment = self.lead_id.annual_payment

    @api.onchange('contact_id')
    def onchange_contact_id(self):
        for prop in self:

            if not prop.contact_id:
                prop.legal_contact_id = False
                prop.auditor_contact_id = False
                prop.referral_contact_id = False
                prop.shareholder_contact_id = False
                prop.authorised_contact_id = False
                prop.general_manager_id = False
                prop.country_manager_id = False
                prop.manager_cr_id = False
                prop.manager_ec_id = False
                prop.client_hr_id = False
                prop.client_finance_id = False
                prop.other_contact_id = False

    def action_created_invoice(self):
        self.ensure_one()
        invoices = self.env['account.move'].sudo().search([('prop_id', '=', self.id)])
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        action["context"] = {"create": False}
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def _compute_invoice_count(self):
        Invoice = self.env['account.move']

        for proposal in self:
            proposal.invoice_count = Invoice.search_count(
                [('prop_id', '=', proposal.id)]) or 0

    def compute_real_revenue(self):
        for prop in self:
            invoices = self.env['account.move'].sudo().search([('prop_id', '=', prop.id)])
            total = 0
            for invoice in invoices:
                if invoice.state == 'posted':
                    total += invoice.amount_total
            prop.real_revenue = total

    def draft_proposal(self):
        self.write({'state': 'draft'})

    def generate_onetime_invoice(self, fees):
        print("##############")
        partner_invoice = self.contact_id
        if not partner_invoice:
            raise UserError(_('You have to select an invoice address in the service form.'))
        company = self.env.user.company_id

        journal = self.env['account.move'].with_context(force_company=company.id,
                                                        move_type='out_invoice').sudo()._get_default_journal()
        if not journal:
            raise UserError(_('Please define an accounting sales journal for the company %s (%s).') % (
                self.company_id.name, self.company_id.id))
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': partner_invoice.id,
            'invoice_payment_term_id': self.payment_terms_id.id,
            'invoice_origin': self.name,
            'invoice_line_ids': [],
            'prop_id': self.id,
        }
        for fee in fees.filtered(lambda o: o.fusion_fees_id.type != 'proforma'):
            if fee.amount_to_be_paid == 0:
                continue
            name = fee.label
            product_id = self.env['product.product'].search(
                [('product_tmpl_id', '=', fee.fusion_fees_id.product_id.id)])
            account = fee.fusion_fees_id.product_id._get_product_accounts()['income']
            if not account:
                raise UserError(_('No account defined for product "%s".') % product_id.name)
            invoice_line_vals = {
                'name': name,
                'account_id': account.id,
                'quantity': 1,
                'price_unit': fee.amount_to_be_paid,
                'product_id': product_id[0].id,
                'analytic_account_id': fee.fusion_fees_id.account_analytic_id.id,
                'contract_fees_id': fee.id,

            }

            balance = -(fee.amount_to_be_paid)
            invoice_line_vals.update({
                'debit': balance > 0.0 and balance or 0.0,
                'credit': balance < 0.0 and -balance or 0.0,
            })
            invoice_vals['invoice_line_ids'] = [(0, 0, invoice_line_vals)]

            if not len(invoice_vals['invoice_line_ids']) == 0:
                invoice_vals.update({'invoice_date': fee.invoice_date})
                self.env['account.move'].with_context(default_move_type='out_invoice').sudo().create(invoice_vals)

        if fees.filtered(lambda o: o.fusion_fees_id.type == 'proforma').ids:
            for line in fees.filtered(lambda o: o.fusion_fees_id.type == 'proforma'):
                if line.amount_to_be_paid != 0:
                    self.env['account.payment'].create({
                        'payment_type': 'inbound',
                        'payment_method_id': 1,
                        'partner_type': 'customer',
                        'is_proforma': True,
                        'partner_id': self.contact_id.id,
                        'amount': line.amount_to_be_paid,
                        'date': line.invoice_date,
                        'journal_id': journal.id,
                        'contract_id': self.id,
                        'contract_fees_id': line.id,
                        'communication': line.label
                    })

        for fee in fees:
            if fee.fusion_fees_id.invoice_period == 'yearly' and fee.next_invoice_date and fee.remaining_amount == 0:
                fee.next_invoice_date = self.check_next_invoice_date(self.start_date,
                                                                     self.start_date + relativedelta(years=1), fee)
            if fee.fusion_fees_id.invoice_period == 'monthly' and fee.next_invoice_date and fee.remaining_amount == 0:
                fee.next_invoice_date = self.check_next_invoice_date(self.start_date,
                                                                     self.start_date + relativedelta(months=1), fee)

    def check_next_invoice_date(self, start_date, end_date, fee_line):
        if fee_line.type == 'proforma':
            paid_amount = sum(fee_line.payment_ids.filtered(
                lambda o: o.date >= start_date and o.date < end_date and o.state != 'cancelled').mapped('amount'))
        else:
            paid_amount = sum(fee_line.move_line_ids.filtered(
                lambda
                    o: o.move_id.invoice_date >= start_date and o.move_id.invoice_date < end_date and o.move_id.state != 'cancel').mapped(
                'price_subtotal'))
        if paid_amount != fee_line.amount:
            return start_date
        else:
            if fee_line.invoice_period == 'yearly':
                date_diff = relativedelta(years=1)
            else:
                date_diff = relativedelta(months=1)
            next_start_date = start_date + date_diff
            next_end_date = end_date + date_diff
            return self.check_next_invoice_date(next_start_date, next_end_date, fee_line)

    def generate_invoice(self):
        partner_invoice = self.contact_id
        if not partner_invoice:
            raise UserError(_('You have to select an invoice address in Contract.'))
        company = self.env.user.company_id

        journal = self.env['account.move'].with_context(force_company=company.id,
                                                        move_type='out_invoice').sudo()._get_default_journal()
        if not journal:
            raise UserError(_('Please define an accounting sales journal for the company %s (%s).') % (
                self.company_id.name, self.company_id.id))
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': partner_invoice.id,
            'invoice_origin': self.name,
            'invoice_line_ids': [],
            'prop_id': self.id,
        }

        for pline in self.proposal_lines:
            govt_account = pline.service_option_id.govt_product_id.product_tmpl_id._get_product_accounts()['income']
            if not govt_account:
                raise UserError(
                    _('No account defined for product "%s".') % pline.service_option_id.govt_product_id.name)
            govt_line_vals = {
                'name': pline.service_option_id.govt_product_id.name,
                'account_id': govt_account.id,
                'quantity': pline.quantity,
                'price_unit': pline.govt_fees,
                'product_id': pline.service_option_id.govt_product_id.id,
            }

            balance = -(pline.govt_fees)
            govt_line_vals.update({
                'debit': balance > 0.0 and balance or 0.0,
                'credit': balance < 0.0 and -balance or 0.0,
            })
            invoice_vals['invoice_line_ids'].append((0, 0, govt_line_vals))

            fusion_account = pline.service_option_id.fusion_product_id.product_tmpl_id._get_product_accounts()['income']
            if not fusion_account:
                raise UserError(
                    _('No account defined for product "%s".') % pline.service_option_id.fusion_product_id.name)
            fusion_line_vals = {
                'name': pline.service_option_id.fusion_product_id.name,
                'account_id': fusion_account.id,
                'quantity': pline.quantity,
                'price_unit': pline.fusion_fees,
                'product_id': pline.service_option_id.fusion_product_id.id,
            }

            balance = -(pline.fusion_fees)
            fusion_line_vals.update({
                'debit': balance > 0.0 and balance or 0.0,
                'credit': balance < 0.0 and -balance or 0.0,
            })
            invoice_vals['invoice_line_ids'].append((0, 0, fusion_line_vals))

        if not len(invoice_vals['invoice_line_ids']) == 0:
            self.env['account.move'].with_context(default_move_type='out_invoice').sudo().create(invoice_vals)
        else:
            raise UserError(_('No invoiceable lines remaining'))


class AccountPayment(models.Model):
    """Account Payment Model."""

    _inherit = 'account.payment'

    contract_id = fields.Many2one(
        comodel_name='ebs.crm.proposal',
        string='Contract',
    )
    service_id = fields.Many2one('ebs.crm.service.process', 'Service Process ')

    contract_fees_id = fields.Many2one('ebs.contract.proposal.fees', 'Contract Fees')

    def write(self, vals):
        res = super(AccountPayment, self).write(vals)
        if vals.get('state') == 'cancelled' and self.contract_fees_id:
            self.check_contract_next_invoice_date()
        return res

    def unlink(self):
        for rec in self:
            if rec.state != 'cancelled' and rec.contract_fees_id:
                rec.check_contract_next_invoice_date()
        return super(AccountPayment, self).unlink()

    def check_contract_next_invoice_date(self):
        if self.contract_fees_id.invoice_period == 'yearly':
            years = relativedelta(self.contract_fees_id.next_invoice_date,
                                  self.contract_fees_id.contract_id.start_date).years
            i = 1
            for period in range(years):
                start_date = self.contract_fees_id.contract_id.start_date + relativedelta(years=i - 1)
                end_date = self.contract_fees_id.contract_id.start_date + relativedelta(years=i)
                payment_ids = self.search([('date', '>=', start_date), ('date', '<', end_date),
                                           ('contract_fees_id', '=', self.contract_fees_id.id),
                                           ('state', '!=', 'cancelled')]) - self
                if sum(payment_ids.mapped('amount')) != self.contract_fees_id.amount:
                    self.contract_fees_id.next_invoice_date = start_date
                    break
                i += 1
        if self.contract_fees_id.invoice_period == 'monthly':
            months = relativedelta(self.contract_fees_id.next_invoice_date,
                                   self.contract_fees_id.contract_id.start_date).months
            i = 1
            for period in range(months):
                start_date = self.contract_fees_id.contract_id.start_date + relativedelta(months=i - 1)
                end_date = self.contract_fees_id.contract_id.start_date + relativedelta(months=i)
                payment_ids = self.search([('date', '>=', start_date), ('date', '<', end_date),
                                           ('contract_fees_id', '=', self.contract_fees_id.id),
                                           ('state', '!=', 'cancelled')]) - self
                if sum(payment_ids.mapped('amount')) != self.contract_fees_id.amount:
                    self.contract_fees_id.next_invoice_date = start_date
                    break
                i += 1


class ebsCrmProposalLines(models.Model):
    _name = 'ebs.crm.proposal.line'
    _description = 'EBS Proposal Lines'

    service_id = fields.Many2one('ebs.crm.service', 'Service')
    service_template_id = fields.Many2one('ebs.crm.service.template', 'Service Template')
    proposal_id = fields.Many2one('ebs.crm.proposal')

    govt_fees = fields.Float('Govt. Fees')
    fusion_fees = fields.Float('Fusion. Fees')

    quantity = fields.Integer('Quantity', default=1)
    service_process_count = fields.Integer(string='Service Order Count', compute='compute_service_process_count')
    add_service_process = fields.Boolean(compute='compute_service_process_count')

    service_process_ids = fields.One2many('ebs.crm.service.process', 'proposal_line_id', string='Service Orders',
                                          copy=True)
    invoice_line_id = fields.Many2one('account.move.line', 'Invoice Line', copy=False, readonly=True)
    prop_state = fields.Selection(related='proposal_id.state')

    service_option_id = fields.Many2one('ebs.service.option', string='Service Option',
                                        domain="[('service_id', '=', service_id)]")
    govt_product_id = fields.Many2one('product.product', string='Govt Product')
    fusion_product_id = fields.Many2one('product.product', string='Fusion Product')

    @api.onchange('service_option_id')
    def onchange_service_option_id(self):
        self.ensure_one()
        if self.service_option_id:
            self.govt_product_id = self.service_option_id.govt_product_id.id
            self.govt_fees = self.service_option_id.govt_fees
            self.fusion_product_id = self.service_option_id.fusion_product_id.id
            self.fusion_fees = self.service_option_id.fusion_fees

    @api.onchange('service_id')
    def onchange_service_id(self):
        self.ensure_one()
        self.service_option_id = False
        domain = [('state', '=', 'ready')]
        count = 0
        if self.proposal_id.contract_type == 'fme':
            count += 1
            domain.append(('fme', '=', True))
        if self.proposal_id.contract_type == 'fss':
            count += 1
            domain.append(('fss', '=', True))
        if self.proposal_id.contract_type == 'fos':
            count += 1
            domain.append(('fos', '=', True))
        if count == 2:
            domain.insert(0, '|')
        if count == 3:
            domain.insert(0, '|')
            domain.insert(1, '|')
        return {'domain': {'service_id': domain}}

    @api.onchange('service_id')
    def onchange_service(self):
        for rec in self:
            if rec.service_id:
                service_templates = self.env['ebs.crm.service.template'].search(
                    [('service_id', '=', rec.service_id.id)])

                return {'domain': {
                    'service_template_id': [('id', 'in', service_templates.ids)],
                }}

    def compute_service_process_count(self):
        for rec in self:
            rec.service_process_count = len(rec.service_process_ids.ids)
            if rec.quantity == 0:
                rec.add_service_process = False
            else:

                if rec.service_process_count >= rec.quantity:
                    rec.add_service_process = True
                else:
                    rec.add_service_process = False

    @api.onchange('quantity')
    def onchange_quantity(self):
        for rec in self:
            if rec.quantity == 0:
                rec.add_service_process = False
            else:
                rec.service_process_count = len(rec.service_process_ids.ids)
                if rec.service_process_count >= rec.quantity:
                    rec.add_service_process = True
                else:
                    rec.add_service_process = False

    def action_create_service_process(self):
        if len(self.env['ebs.crm.service.process'].search([('proposal_line_id', '=', self.id)]).ids) >= self.quantity:
            fusion_fees = self.fusion_fees
        else:
            fusion_fees = 0
        service_process_id = self.env['ebs.crm.service.process'].create({
            'service_order_type': self.service_option_id.service_order_type,
            'proposal_line_id': self.id,
            'client_id': self.proposal_id.contact_id.id,
            'partner_id': self.proposal_id.contact_id.id,
            'service_id': self.service_id.id,
            'option_id': self.service_option_id.id,
            'govt_product_id': self.service_option_id.govt_product_id.id,
            'fusion_product_id': self.service_option_id.fusion_product_id.id,
            'fusion_fees': fusion_fees,
            'service_template_id': self.service_template_id.id,
        })

        service = self.service_id
        service_template = self.service_template_id
        for type in service_template.document_type_ids:
            if type.output:
                out_doc_line = self.env['ebs.add_service_processcrm.proposal.out.documents'].search(
                    [('doc_type_id', '=', type.document_type_id.id),
                     ('service_process_id', '=', service_process_id.id)])
                if not out_doc_line:
                    self.env['ebs.crm.proposal.out.documents'].create({
                        'doc_type_id': type.document_type_id.id,
                        'service_process_id': service_process_id.id,
                    })
            if type.input:
                in_doc_line = self.env['ebs.crm.proposal.in.documents'].search(
                    [('doc_type_id', '=', type.document_type_id.id),
                     ('service_process_id', '=', service_process_id.id)])
                if not in_doc_line:
                    line_id = self.env['ebs.crm.proposal.in.documents'].create({
                        'doc_type_id': type.document_type_id.id,
                        'service_process_id': service_process_id.id,
                    })
                    if type.individual:
                        contact = self.proposal_id.contact_id
                        for doc in contact.document_o2m:
                            if doc.document_type_id.id == type.document_type_id.id:
                                line_id.write({'name': doc.id})

        for line in service_template.workflow_lines:
            flag = False
            for pline in service_process_id.proposal_workflow_line_ids:
                if line.name.name == pline.name and line.stage_id.id == pline.stage_id.id and line.output == pline.output and \
                        line.replacement_id.id == pline.replacement_id.id:
                    flag = True

            if not flag:
                self.check_dependancy(line, service_process_id)

        form_view = self.env.ref('ebs_fusion_services.view_ebs_crm_service_process_form')
        tree_view = self.env.ref('ebs_fusion_services.view_ebs_crm_service_process_tree')
        return {
            'name': _('Service Orders'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'ebs.crm.service.process',
            'views': [(form_view.id, 'form')],
            'view_id': form_view.id,
            'target': 'current',
            'res_id': service_process_id.id,
            'domain': [('proposal_line_id', '=', self.id)]
        }

    def action_show_service_process(self):
        self.ensure_one()
        form_view = self.env.ref('ebs_fusion_services.view_ebs_crm_service_process_form')
        tree_view = self.env.ref('ebs_fusion_services.view_ebs_crm_service_process_tree')
        search_view = self.env.ref('ebs_fusion_services.view_ebs_crm_service_process_search')
        return {
            'name': _('Service Orders'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'res_model': 'ebs.crm.service.process',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'view_id': tree_view.id,
            'target': 'current',
            'search_view_id': search_view.id,
            'domain': [('proposal_line_id', '=', self.id)]

        }


class ebsCrmProposalEmployeeLines(models.Model):
    _name = 'ebs.crm.proposal.employee.line'
    _description = 'EBS Proposal Employee Lines'

    proposal_id = fields.Many2one('ebs.crm.proposal')
    proposal_state = fields.Selection(related='proposal_id.state')
    employee_name = fields.Char('Name')
    partner_parent_id = fields.Many2one('res.partner', 'Contact')
    name = fields.Many2one('hr.employee', string="Employee", domain="[('partner_parent_id','=',partner_parent_id)]")
    employee_state = fields.Selection(related='name.state')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female'), ('other', 'Other')], string="Gender")
    job_id = fields.Many2one('hr.job', string="Job Position")
    labor_quota_id = fields.Many2one('ebs.labor.quota', string='Labor Quota')
    expiry_date = fields.Date('Expiry Date', related='labor_quota_id.expiry_date')
    lq_is_expired = fields.Boolean('Expired', compute='compute_lq_is_expired')
    arrival_date = fields.Date(related='name.arrival_date')
    cancelled_date = fields.Date(related='name.cancelled_date')
    nationality_id = fields.Many2one('res.country', string="Nationality")
    total_salary_package = fields.Integer("Basic Salary")
    monthly_eos = fields.Integer("Accommodation Allowance")
    monthly_service_fees = fields.Integer("Transportation Allowance")
    food_allowance = fields.Integer("Food Allowance")
    other_allowance = fields.Integer("Other Allowance")
    monthly_fee_ids = fields.One2many('ebs.crm.employee.monthly.fees', 'employee_line_id', 'Monthly Fees')
    one_time_fee_ids = fields.One2many('ebs.crm.employee.onetime.fees', 'employee_line_id', 'One-time Fees')
    employee_labor_quota_subline_ids = fields.One2many('ebs.crm.employee.labor.quota.line', 'employee_line_id',
                                                       'Labor Quota Sublines')
    default_line_available = fields.Boolean()
    fos_fees_line_id = fields.Many2one('ebs.proposal.fos.fee.structure')
    structure_type_id = fields.Many2one('hr.payroll.structure.type', string="Salary Structure Type")
    contract_id = fields.Many2one('hr.contract', string="Contract",
                                  domain="[('employee_id', '=', name), ('state', '=', 'open')]")
    contact_id = fields.Many2one(related='proposal_id.contact_id')
    service_fees = fields.Float("Service Fees")
    private_medical_insurance = fields.Float(string="Private Medical Insurance ")
    air_ticket_deposit = fields.Float(string="Air Ticket Deposit")
    workmen_compensation = fields.Float(string="Workmen's Compensation")

    @api.model
    def default_get(self, fields):
        res = super(ebsCrmProposalEmployeeLines, self).default_get(fields)
        if self._context.get('proposal_id'):
            contract_id = self.env['ebs.crm.proposal'].browse(self._context.get('proposal_id'))
            if contract_id.salary_structure_ids:
                salary_line_id = contract_id.salary_structure_ids[0]
            res.update({
                'total_salary_package': salary_line_id.monthly_gross,
                'monthly_eos': salary_line_id.housing_allowance,
                'monthly_service_fees': salary_line_id.transportation_allowance,
                'other_allowance': salary_line_id.other_allowance,
            })
        return res

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            self.employee_name = self.name.name

    def create_employee(self):
        if self.employee_name == 'New Employee':
            raise UserError(_('Employee Name Should Not Be New Employee!!!'))
        else:
            employee_id = self.env['hr.employee'].create({'name': self.employee_name,
                                                          'job_id': self.job_id.id,
                                                          'nationality_id': self.nationality_id.id,
                                                          'gender': self.gender,
                                                          'company_id': self.env.user.company_id.id,
                                                          'partner_parent_id': self.partner_parent_id.id,
                                                          'sponsored_company_id': self.env.user.company_id.partner_id.id,
                                                          'employee_type': 'fos_employee',
                                                          'service_fee': self.service_fees,
                                                          'private_medical_insurance': self.private_medical_insurance,
                                                          'air_ticket_deposit': self.air_ticket_deposit,
                                                          'workmen_compensation': self.workmen_compensation,
                                                          })
            self.write({'name': employee_id.id})

    @api.depends('expiry_date')
    def compute_lq_is_expired(self):
        for rec in self:
            if rec.expiry_date and rec.expiry_date < date.today():
                rec.lq_is_expired = True

        else:
            rec.lq_is_expired = False

    @api.onchange('labor_quota_id', 'nationality_id', 'job_id', 'gender')
    def onchange_labor_quota_id_lines(self):
        self.ensure_one()
        self.employee_labor_quota_subline_ids = [(5, 0, 0)]
        if self.expiry_date:
            if self.labor_quota_id and self.expiry_date >= date.today():
                employee_lines = []
                lines = self.labor_quota_id.labor_quota_line_id.filtered(lambda o: o.qty_remaining != 0)
                if not lines:
                    raise UserError(_('In This Labor Quota There Is No Available Labor Quota Lines.'))

                default_lines = lines.filtered(lambda
                                                   o: o.nationality_id.id == self.nationality_id.id and o.job_id.id == self.job_id.id and o.gender == self.gender)
                if default_lines:
                    self.default_line_available = True
                else:
                    self.default_line_available = False
                for line in lines:
                    vals = {
                        'labor_quota_line_id': line.id,
                        'ref_no': line.ref_no,
                        'nationality_id': line.nationality_id.id,
                        'job_id': line.job_id.id,
                        'gender': line.gender,
                        'qty_remaining': line.qty_remaining,
                    }
                    if default_lines:
                        if line == default_lines[0]:
                            vals.update({'is_default': True})
                    employee_lines.append((0, 0, vals))
                self.write({'employee_labor_quota_subline_ids': employee_lines})

    @api.onchange('labor_quota_id')
    def onchange_labor_quota_id(self):
        self.ensure_one()
        if self.expiry_date:
            if self.labor_quota_id and self.expiry_date < date.today():
                raise UserError(_('Selected Labor Quota Is Expired.'))

    @api.onchange('contract_id')
    def onchange_contract(self):
        for rec in self:
            if rec.name:
                if rec.name.contract_id.id == rec.contract_id.id:
                    current_contract = rec.name.contract_id
                    rec.total_salary_package = current_contract.wage
                    rec.monthly_eos = current_contract.accommodation
                    rec.monthly_service_fees = current_contract.transport_allowance
                    rec.food_allowance = current_contract.food_allowance
                    rec.other_allowance = current_contract.other_allowance
                    rec.structure_type_id = current_contract.structure_type_id.id

    @api.onchange('name')
    def onchange_employee(self):
        for rec in self:
            if rec.name:
                rec.nationality_id = rec.name.nationality_id.id
                rec.job_id = rec.name.job_id.id
                rec.gender = rec.name.gender
                if rec.name.contract_id:
                    current_contract = rec.name.contract_id
                    rec.contract_id = current_contract.id
                    rec.total_salary_package = current_contract.wage
                    rec.monthly_eos = current_contract.accommodation
                    rec.monthly_service_fees = current_contract.transport_allowance
                    rec.food_allowance = current_contract.food_allowance
                    rec.other_allowance = current_contract.other_allowance
                    rec.structure_type_id = current_contract.structure_type_id.id

    @api.model
    def create(self, vals):
        res = super(ebsCrmProposalEmployeeLines, self).create(vals)
        if res.contract_id:
            res.contract_id.wage = res.total_salary_package
            res.contract_id.accommodation = res.monthly_eos
            res.contract_id.transport_allowance = res.monthly_service_fees
            res.contract_id.food_allowance = res.food_allowance
            res.contract_id.other_allowance = res.other_allowance
            res.contract_id.structure_type_id = res.structure_type_id.id
        return res

    def write(self, vals):
        res = super(ebsCrmProposalEmployeeLines, self).write(vals)
        if self.contract_id:
            self.contract_id.wage = self.total_salary_package
            self.contract_id.accommodation = self.monthly_eos
            self.contract_id.transport_allowance = self.monthly_service_fees
            self.contract_id.food_allowance = self.food_allowance
            self.contract_id.other_allowance = self.other_allowance
            self.contract_id.structure_type_id = self.structure_type_id.id
        return res


class EbsCrmEmployeeMonthlyFees(models.Model):
    _name = 'ebs.crm.employee.monthly.fees'
    _description = 'Ebs Crm Employee Monthly Fees'

    employee_line_id = fields.Many2one('ebs.crm.proposal.employee.line')
    employee_id = fields.Many2one('hr.employee')
    proposal_id = fields.Many2one('ebs.crm.proposal')
    remaining_amount = fields.Float('Remaining Amount')
    is_invoiced = fields.Boolean('Invoiced')
    name = fields.Many2one('ebs.crm.contract.fees', 'Fees', required=1,
                           domain="['|',('one_time','=',one_time),'|',('fme','=',fme),('fss','=',fss)]")
    invoice_line_ids = fields.One2many('account.move.line', 'monthly_fee_line_id', 'Invoice Lines')
    amount = fields.Float('Amount')
    total_amount = fields.Float('Amount')
    fme = fields.Boolean()
    fss = fields.Boolean()
    one_time = fields.Boolean()

    @api.onchange('name')
    def onchange_name(self):
        for rec in self:
            if rec.name:
                rec.amount = rec.name.amount
                rec.remaining_amount = rec.amount
                rec.employee_id = rec.employee_line_id.name.id
            else:
                rec.amount = 0

    @api.onchange('total_amount')
    def onchange_total_amount(self):
        if self.total_amount:
            self.remaining_amount = self.total_amount


class EbsCrmEmployeeOneTimeFees(models.Model):
    _name = 'ebs.crm.employee.onetime.fees'
    _description = 'Ebs Crm Employee OneTime Fees'

    employee_line_id = fields.Many2one('ebs.crm.proposal.employee.line')
    total_amount = fields.Float('Amount')
    employee_id = fields.Many2one('hr.employee')
    employee_name = fields.Char(related='employee_line_id.name.name')
    proposal_id = fields.Many2one('ebs.crm.proposal')
    is_invoiced = fields.Boolean('Invoiced')
    remaining_amount = fields.Float('Remaining Amount', readonly=0)
    name = fields.Many2one('ebs.crm.contract.fees', 'Fees', required=1)
    amount = fields.Float('Amount')
    monthly = fields.Boolean()
    one_time = fields.Boolean()
    fme = fields.Boolean()
    fss = fields.Boolean()
    invoice_line_ids = fields.One2many('account.move.line', 'onetime_fee_line_id', 'Invoice Lines')

    @api.onchange('name')
    def onchange_name(self):
        for rec in self:
            if rec.name:
                rec.amount = rec.name.amount
                rec.total_amount = rec.amount
                rec.remaining_amount = rec.amount
                rec.employee_id = rec.employee_line_id.name.id
            else:
                rec.amount = 0

    @api.onchange('total_amount')
    def onchange_total_amount(self):
        for rec in self:
            rec.remaining_amount = rec.total_amount


class EbsCrmEmployeeLaborQuotaLine(models.Model):
    _name = 'ebs.crm.employee.labor.quota.line'
    _description = 'EBS CRM Employee Labor Quota Line'

    is_default = fields.Boolean("Default")
    employee_line_id = fields.Many2one('ebs.crm.proposal.employee.line')
    labor_quota_line_id = fields.Many2one('labor.quota.line')

    ref_no = fields.Char("Reference Number", related='labor_quota_line_id.ref_no')
    nationality_id = fields.Many2one('res.country', "Nationality", related='labor_quota_line_id.nationality_id')
    job_id = fields.Many2one('hr.job', "Job Title", related='labor_quota_line_id.job_id')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Gender',
                              related='labor_quota_line_id.gender')
    qty_remaining = fields.Integer(related='labor_quota_line_id.qty_remaining', string='Quantity Available')


class Res_Currency(models.Model):
    _inherit = 'res.currency'

    currency_word = fields.Char("Currency in Word")
    currency_unit_label = fields.Char(string="Currency Unit", help="Currency Unit Name", translate=True)
    currency_subunit_label = fields.Char(string="Currency Subunit", help="Currency Subunit Name", translate=True)

    def amount_to_text_arabic(self, amount):
        self.ensure_one()

        def _num2words(number, lang):
            try:
                return num2words(number, lang=lang).title()
            except NotImplementedError:
                return num2words(number, lang='en').title()

        if num2words is None:
            logging.getLogger(__name__).warning("The library 'num2words' is missing, cannot render textual amounts.")
            return ""

        formatted = "%.{0}f".format(self.decimal_places) % amount
        parts = formatted.partition('.')
        integer_value = int(parts[0])
        fractional_value = int(parts[2] or 0)
        currency_unit_label = self.env['ebs.crm.proposal']._get_eng_to_arabic('currency_unit_label', 'res.currency',
                                                                              self.id)
        currency_subunit_label = self.env['ebs.crm.proposal']._get_eng_to_arabic('currency_subunit_label',
                                                                                 'res.currency',
                                                                                 self.id)

        lang = self.env['res.lang'].with_context(active_test=False).search([('code', '=', 'ar_SY')])
        amount_words = tools.ustr('{amt_value} {amt_word}').format(
            amt_value=_num2words(integer_value, lang=lang.iso_code),
            amt_word=currency_unit_label,
        )
        if not self.is_zero(amount - integer_value):
            amount_words += ' ' + _('و') + tools.ustr(' {amt_value} {amt_word}').format(
                amt_value=_num2words(fractional_value, lang=lang.iso_code),
                amt_word=currency_subunit_label,
            )
        return amount_words


class ResCompanyInherit(models.Model):
    _inherit = 'res.company'

    company_code = fields.Char(string='Code')
    company_report_header = fields.Binary(string="Letter Head")
    company_report_footer = fields.Binary(string="Letter Foot")


class ContractClientContacts(models.Model):
    _name = 'contract.client.contacts'
    _description = 'Contract Client Contacts'

    contract_id = fields.Many2one('ebs.crm.proposal')
    partner_id = fields.Many2one('res.partner', string="Contact")
    relation_tag_ids = fields.Many2many('client.contact.relation.tags', string="Relation")

    def _cron_delete_records(self):
        records = self.search([('contract_id', '=', False)])
        records.unlink()


class ClinetContactRelationTags(models.Model):
    _name = 'client.contact.relation.tags'
    _description = 'Client Contact Relation Tags'

    name = fields.Char(string="Name")
