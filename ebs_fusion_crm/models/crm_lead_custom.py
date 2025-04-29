from odoo import api, fields, models, _
from datetime import datetime, timedelta, date
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, config
from odoo.exceptions import UserError
import base64
from odoo.tools.safe_eval import safe_eval


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    hubspot_id = fields.Char("Hubspot ID")
    mobile = fields.Char("Mobile")
    partner_address_mobile = fields.Char('Partner Contact Mobile', related='partner_id.mobile', )

    industry_id = fields.Many2one('res.partner.industry', string="Industry")
    sub_sectors_ids = fields.Many2many('res.partner.industry', string="Sub-Sectors")
    marketing_subject_matter_expert_id = fields.Many2one('res.partner', string="Subject Matter Expert")
    delivery_partner_id = fields.Many2one('res.partner', string="Delivery Partner")

    partner_id = fields.Many2one('res.partner', string='Client', index=True,
                                 domain="[('is_company', '=', True),('parent_id', '=', False)]",
                                 help="Linked partner (optional). Usually created when converting the lead. You can find a partner by its Name, TIN, Email or Internal Reference.")
    contact_ids = fields.Many2many('res.partner', string="Contact")
    partner_name = fields.Char('Client Name')
    contact_name = fields.Char('Contact Name')
    show_partner_name = fields.Boolean()
    show_contact_name = fields.Boolean()
    stage_code = fields.Integer(compute='compute_stage_code')

    cost = fields.Float("Cost")
    opportunity_type = fields.Selection([
        ('corporate_services', 'Corporate Services'),
        ('product_representation_opportunity', 'Product Representation Opportunity'),
        ('advisory', 'Advisory'),
    ])
    formation_fee = fields.Monetary('Formation Fees', currency_field='company_currency', )
    service_fees_monthly = fields.Monetary('Service Fees Monthly', currency_field='company_currency', )

    # Tender fields
    tender_type = fields.Selection([('deal', 'Deal'), ('tender', 'Tender')], string="Tender Type", default='deal')
    tender_no = fields.Char("Tender Number")
    tender_name = fields.Char("Tender Name")
    tender_description = fields.Text("Tender Description")
    tender_category = fields.Char("Tender Category")
    tender_of = fields.Selection([('government', 'Government'), ('semi government', 'Semi Government'),
                                  ('private', 'Private'), ('global', 'Global'), ('other', 'Other')
                                  ], string="Tender Of")
    tender_organization_name = fields.Char("Tender Organization Name")
    tender_comm_contact_person_name = fields.Char("Tender Committee Contact Person Name")
    tender_comm_contact_person_desig = fields.Char("Tender Committee Contact Person Designation")
    tender_comm_contact_person_eamil = fields.Char("Tender Committee Contact Person Email")
    tender_comm_contact_person_phone = fields.Char("Tender Committee Contact Person Phone")
    country_id = fields.Many2one('res.country', string="Country")

    tender_published_on = fields.Selection([('news paper', 'News Paper'), ('portal', 'Portal'),
                                            ('invitation', 'Invitation'), ('reference', 'Reference'), ('other', 'Other')
                                            ], string="Tender Published On")
    date_published = fields.Date("Date of Tender Publishing")
    tender_value = fields.Float("Tender Value")
    approx_cost = fields.Float("Approx Cost")
    approx_profit = fields.Float("Approx Profit")
    participating_tender = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                                            string="Are we participating in the tender?")
    tender_purchase_value = fields.Selection([('free', 'Free'), ('qar', 'QAR'),
                                              ('usd', 'USD'), ('subscription', 'Subscription')],
                                             string="Tender Purchase Value")
    tender_submission_method = fields.Selection([('online', 'Online'), ('by hand', 'By Hand'),
                                                 ('post', 'Post'), ('other', 'Other')],
                                                string="Method of Tender Submission")
    tender_submission_before_date = fields.Date("Tender Submission Before Date")
    tender_bond_value = fields.Float("Tender Bond Value")
    bank_guarantee = fields.Char("Bank Guarantee")
    bank_name = fields.Char("Bank Name")
    tender_wining_probability = fields.Selection([('high', 'High'), ('medium', 'Medium'), ('low', 'Low')],
                                                 string="Tender Wining Probability")
    tender_opening_date = fields.Date("Tender Opening Date")
    tender_opening_location = fields.Char("Tender Opening Location")
    state = fields.Selection([('pipline', 'Pipeline'), ('award', 'Awarded'), ('ongoing', 'Ongoing'),
                              ('lost', 'Lost'), ('other', 'Other')], default='pipline', copy=False, string='Status')
    close_date = fields.Date("Closed Date")
    referred_by_id = fields.Many2one('res.partner', string='Referred by',
                                     domain=[('address_type', '=', False), '|', ('is_shareholder', '=', True),
                                             ('is_company', '!=', True), ('is_referral', '=', True)])

    meeting_count_tender = fields.Integer('# Meetings', compute='_compute_meeting_count_tender')
    owner_id = fields.Many2one(related='company_id.partner_id', string='Owner', store=True)
    proposal_doc_id = fields.Many2one('documents.document', 'Proposal Document')

    lead_document_count = fields.Integer(compute='lead_document_compute_count')

    def create_client(self):
        action = self.env.ref('ebs_fusion_contacts.action_clients_review').read()[0]
        action['views'] = [(self.env.ref('ebs_fusion_contacts.view_clients_review_form').id, 'form')]
        action['view_mode'] = 'form'
        action_context = safe_eval(action['context'])
        action_context['lead_id'] = self.id
        action['context'] = action_context
        return action

    def lead_document_compute_count(self):
        for record in self:
            record.lead_document_count = self.env['documents.document'].search_count(
                [('lead_id', '=', self.id)])

    def get_document(self):
        action = self.env.ref('documents.document_action').read()[0]
        action['domain'] = [('lead_id', '=', self.id)]
        action['context'] = {
            'default_lead_id': self.id,
        }

        return action

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
        stage_id = self.env['crm.stage'].search([('code', '=', 4)])
        self.write({'stage_id': stage_id.id})

    def open_send_mail_wizard(self):
        if not self.email_from:
            raise UserError(_('Email Is Required To Send Proposal.'))
        email_temp = self.env['ir.config_parameter'].sudo().get_param('proposal_email_temp_id')
        if email_temp:
            mail_template = self.env['mail.template'].browse(int(email_temp))
        else:
            mail_template = self.env.ref('ebs_fusion_crm.mail_template_stage_proposal_lead')

        print("==============================", self.proposal_doc_id.attachment_id.ids)

        ctx = {
            'model': 'crm.lead',
            'res_id': self.id,
            'default_email_to': self.email_from,
            'document_ids': self.env['documents.document'].search([('lead_id', '=', self.id)]).ids,
            'template_id': mail_template.id,
            'proposal_send': True
        }

        return {
            'name': ('Send Proposal'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'send.mail.wizard',
            'target': 'new',
            'context': ctx,
        }

    @api.depends('stage_id')
    def compute_stage_code(self):
        for rec in self:
            rec.stage_code = rec.stage_id.code

    def generate_contract(self):
        if not self.partner_id:
            raise UserError("Please select/create a client before generating a contract.")
        else:
            if any(line.state == 'draft' for line in self.opportunity_type_service_mapping_ids):
                raise UserError("Please approve/reject each opportunity type line before generating a contract.")
            if 'confirm' not in self._context:
                return {
                    'name': _('Generate Contract'),
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'warning.wizard',
                    'target': 'new',
                    'context': {
                        'model': 'crm.lead',
                        'object_id': self.id,
                        'kwargs': {},
                        'confirm': True,
                        'method': 'generate_contract',
                        'message': 'Press confirm to continue.'
                    }
                }
            else:
                list_of_line = []
                service_lines = self.opportunity_type_service_mapping_ids.filtered(lambda o: o.state == 'approved')

                if not service_lines:
                    raise UserError("Please add opportunity type line before generating a contract.")
                proposal_lines = []
                for opp_line in service_lines:
                    proposal_lines.append((0, 0, {
                        'service_id': opp_line.service_id.id,
                        'service_option_id': opp_line.service_option_id.id,
                        'quantity': opp_line.qty,
                        'govt_product_id': opp_line.service_option_id.govt_product_id.id,
                        'govt_fees': opp_line.govt_fees,
                        'fusion_product_id': opp_line.service_option_id.fusion_product_id.id,
                        'fusion_fees': opp_line.fusion_fees,
                    }))

                contract_vals = {
                    'type': 'proposal',
                    'lead_id': self.id,
                    'contact_id': self.partner_id.id,
                    'company_id': self.company_id.id,
                    'payment_terms_id': self.payment_terms_id.id,
                    'date': date.today(),
                    'proposal_lines': proposal_lines,
                    'turnover': self.annual_turnover if self.company_type == 'fme' else 0.0,

                }

                contract_id = self.env['ebs.crm.proposal'].with_context({'lead_id': self.id}).create(contract_vals)

                # Adding fee lines
                if self.company_type == 'fme':
                    contract_id.write({'fme': True})
                    contract_id.write({'contract_type': 'fme'})
                    fme_fees = self.contract_proposal_fee_ids.filtered(lambda o: o.fme == True)
                    for line in fme_fees:
                        line.write({'contract_id': contract_id.id, 'remaining_amount': line.amount})
                if self.company_type == 'fss':
                    contract_id.write({'fss': True})
                    contract_id.write({'contract_type': 'fss'})
                    fss_fees = self.contract_proposal_fee_ids.filtered(lambda o: o.fss == True)
                    for line in fss_fees:
                        line.write({'contract_id': contract_id.id, 'remaining_amount': line.amount})
                if self.company_type == 'fos':
                    contract_id.write({'fos': True})
                    contract_id.write({'contract_type': 'fos'})
                    fos_fees = self.contract_proposal_fee_ids.filtered(lambda o: o.fos == True)
                    salary_line_id = self.env['ebs.proposal.salary.structure']
                    if self.salary_structure_ids:
                        salary_line_id = self.salary_structure_ids[0]
                    for line in fos_fees:
                        line.write({'contract_id': contract_id.id, 'remaining_amount': line.amount})
                    for line in self.fos_fee_structure_ids:
                        line.write({'contract_id': contract_id.id})
                        for record in range(line.number_employees):
                            self.env['ebs.crm.proposal.employee.line'].create({
                                'proposal_id': contract_id.id,
                                'fos_fees_line_id': line.id,
                                'employee_name': 'New Employee',
                                'nationality_id': line.nationality_id.id,
                                'job_id': line.job_position.id,
                                'gender': line.gender,
                                'labor_quota_id': line.labor_quota_id.id,
                                'partner_parent_id': self.partner_id.id,
                                'service_fees': line.fee_person_month,
                                'total_salary_package': salary_line_id.monthly_gross,
                                'monthly_eos': salary_line_id.housing_allowance,
                                'monthly_service_fees': salary_line_id.transportation_allowance,
                                'other_allowance': salary_line_id.other_allowance,
                            })
                    for line in self.salary_structure_ids:
                        line.write({'contract_id': contract_id.id})
                    for line in self.permit_issuance_ids:
                        line.write({'contract_id': contract_id.id})

                contract_id._onchange_lead()
                contract_id._onchange_amount_arabic()
                contract_id._onchange_penalty_amount()
                contract_id._onchange_complaint_response()
                self.stage_id = self.env['crm.stage'].search([('code', '=', 7)]).id

    def _compute_meeting_count_tender(self):
        meeting_data = self.env['calendar.event'].read_group([('opportunity_id', 'in', self.ids)], ['opportunity_id'],
                                                             ['opportunity_id'])
        mapped_data = {m['opportunity_id'][0]: m['opportunity_id_count'] for m in meeting_data}
        for lead in self:
            lead.meeting_count_tender = mapped_data.get(lead.id, 0)

    def action_schedule_meeting_tender(self):
        """ Open meeting's calendar view to schedule meeting on current opportunity.
            :return dict: dictionary value for created Meeting view
        """
        self.ensure_one()
        action = self.env.ref('calendar.action_calendar_event').read()[0]
        partner_ids = self.env.user.partner_id.ids
        if self.partner_id:
            partner_ids.append(self.partner_id.id)
        action['context'] = {
            'default_opportunity_id': self.id,
            'default_partner_id': self.partner_id.id,
            'default_partner_ids': partner_ids,
            'default_team_id': self.team_id.id,
            'default_name': self.name,
        }
        return action

    @api.onchange('expected_revenue')
    def _onchange_opportunity_type(self):
        if self.opportunity_type == 'corporate_services':
            self.expected_revenue = self.formation_fee + 12 * self.service_fees_monthly

    @api.onchange('contact_ids')
    def onchange_contact_ids(self):
        if self.contact_ids:
            self.show_contact_name = False
        else:
            self.show_contact_name = True

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        res = {}
        self.referred_by_id = False
        self.email_from = False
        if self.partner_id:
            self.show_partner_name = False
            contact_ids = self.env['ebs.client.contact'].search([('client_id', '=', self.partner_id.id)]).mapped(
                'partner_id')
            res['domain'] = {'contact_ids': [('id', 'in', contact_ids.ids)]}
            self.contact_ids = [(6, 0, contact_ids.ids)]
            if contact_ids:
                self.email_from = contact_ids[0].email
        else:
            self.show_partner_name = True
            res['domain'] = {'contact_ids': [('id', 'in', [])]}
            self.contact_ids = [(6, 0, [])]
        return res

    @api.model
    def _onchange_stage_id_values(self, stage_id):
        """ returns the new values when stage_id has changed """
        if not stage_id:
            return {}
        stage = self.env['crm.stage'].browse(stage_id)
        return {'probability': stage.probability}

    @api.onchange('stage_id')
    def _onchange_stage_id(self):
        if self.stage_id.code == 2:
            count = 0
            domain = []
            if self.company_type == 'fme':
                count += 1
                domain.append(('is_fme', '=', True))
            if self.company_type == 'fss':
                count += 1
                domain.append(('is_fss', '=', True))
            if self.company_type == 'fos':
                count += 1
                domain.append(('is_fos', '=', True))
            if count == 2:
                domain.insert(0, '|')
            if count == 3:
                domain.insert(0, '|')
                domain.insert(1, '|')
            if domain:
                fusion_fees = self.env['ebs.fusion.fees'].search(domain)
                fee_lines = []
                for fee in fusion_fees:
                    existing_fee_line = self.contract_proposal_fee_ids.filtered(lambda l: l.fusion_fees_id.id == fee.id)
                    if not existing_fee_line:
                        fee_lines.append(self.env['ebs.contract.proposal.fees'].create({
                            'fusion_fees_id': fee.id,
                            'type': fee.type,
                            'lead_id': self.id,
                            'label': fee.name,
                        }).id)
                    else:
                        fee_lines.append(existing_fee_line.id)
                    self.write({'contract_proposal_fee_ids': [(6, 0, fee_lines)]})
            else:
                self.write({'contract_proposal_fee_ids': [(6, 0, [])]})

        contract_ids = self.env['ebs.crm.proposal'].search(
            [('lead_id', '=', self._origin.id), ('type', '=', 'proposal')])
        if not self._context.get('email_send') and self.stage_id.code == 4:
            raise UserError(_('Please Send Email To Client To Set This Stage.'))
        if self.stage_id.code == 7:
            if self.partner_id.client_state != 'active':
                raise UserError(_('Client Is Not Active.'))
            if not contract_ids:
                raise UserError(_('Please Create Contract From Generate Contract Button.'))
        if self.stage_id.code == 8 and any(contract.state != 'active' for contract in contract_ids):
            raise UserError(_('Please Activate All Contracts.'))
        values = self._onchange_stage_id_values(self.stage_id.id)

        self.update(values)

    @api.onchange('formation_fee', 'service_fees_monthly')
    def _onchange_formation_service(self):
        self.expected_revenue = self.formation_fee + self.service_fees_monthly

    def action_set_lost(self, **additional_values):
        for lead in self:
            stage_id = lead._stage_find(domain=[('is_lost', '=', True)])
            result = lead.write({'stage_id': stage_id.id, 'active': True, 'probability': 0, **additional_values})
            lead._rebuild_pls_frequency_table_threshold()
        return result

    def action_set_won_rainbowman(self):
        res = super(CrmLead, self).action_set_won_rainbowman()
        self.close_date = datetime.date.today().strftime(DEFAULT_SERVER_DATE_FORMAT)
        self.ensure_one()
        if self.partner_id:
            self.partner_id.is_customer = True
            action = self.env.ref('base.action_partner_form').read()[0]
            form_view = [(False, 'form')]
            action['views'] = form_view
            action['res_id'] = self.partner_id.id
            action['context'] = {'form_view_initial_mode': 'edit'}
            return action
        return res


class Crm_Lead_Lost(models.TransientModel):
    _inherit = 'crm.lead.lost'

    def action_lost_reason_apply(self):
        leads = self.env['crm.lead'].browse(self.env.context.get('active_ids'))
        for res in leads:
            res.close_date = datetime.date.today().strftime(DEFAULT_SERVER_DATE_FORMAT)
        return leads.action_set_lost(lost_reason=self.lost_reason_id.id)


class portal_wizard(models.TransientModel):
    _inherit = 'portal.wizard'

    def _default_user_ids(self):
        # for each partner, determine corresponding portal.wizard.user records
        partner_ids = self.env.context.get('active_ids', [])
        if self.env.context.get('active_model') == 'crm.lead':
            lead = self.env['crm.lead'].browse(self.env.context.get('active_ids'))
            if lead and lead.contact_ids:
                primary_contact = []
                for primary in lead.contact_ids:
                    if primary.is_primary_contact:
                        primary_contact.append(primary.id)
                partner_ids = primary_contact
            else:
                partner_ids = []
            contact_ids = set()
            user_changes = []
            for partner in self.env['res.partner'].sudo().browse(partner_ids):
                in_portal = False
                if partner.user_ids:
                    in_portal = self.env.ref('base.group_portal') in partner.user_ids[0].groups_id
                user_changes.append((0, 0, {
                    'partner_id': partner.id,
                    'email': partner.email,
                    'in_portal': in_portal,
                }))
        else:
            contact_ids = set()
            user_changes = []
            for partner in self.env['res.partner'].sudo().browse(partner_ids):
                contact_partners = partner.child_ids.filtered(lambda p: p.type in ('contact', 'other')) | partner
                for contact in contact_partners:
                    # make sure that each contact appears at most once in the list
                    if contact.id not in contact_ids:
                        contact_ids.add(contact.id)
                        in_portal = False
                        if contact.user_ids:
                            in_portal = self.env.ref('base.group_portal') in contact.user_ids[0].groups_id
                        user_changes.append((0, 0, {
                            'partner_id': contact.id,
                            'email': contact.email,
                            'in_portal': in_portal,
                        }))
        return user_changes

    user_ids = fields.One2many('portal.wizard.user', 'wizard_id', string='Users', default=_default_user_ids)
