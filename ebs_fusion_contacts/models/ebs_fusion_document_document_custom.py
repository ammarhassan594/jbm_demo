from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class DocumentsCustom(models.Model):
    
    _inherit = 'documents.document'
    shareholder_id = fields.Many2one('share.holder')
    has_expiry_date = fields.Selection(related="document_type_id.has_expiry_date", string='Has Expiry Date')
    has_issue_date = fields.Selection(related="document_type_id.has_issue_date", string='Has Issue Date')
    has_reminder_for_renewal = fields.Selection(related="document_type_id.has_reminder_for_renewal", string='Has Reminder for Renewal')
    has_passport_serial_number = fields.Selection(related="document_type_id.has_passport_serial_number", string='Has Passport Serial Number')
    has_qid_serial_number = fields.Selection(related="document_type_id.has_qid_serial_number", string='Has QID Serial Number')
    has_po_box = fields.Selection(related="document_type_id.has_po_box", string=' Has PO Box')
    has_email_address = fields.Selection(related="document_type_id.has_email_address", string='Has Email Address')
    has_phone_number = fields.Selection(related="document_type_id.has_phone_number", string='Has Phone Number')
    has_reference_number = fields.Selection(related="document_type_id.has_reference_number", string='Has Reference Number')
    has_power_of_attorney_name = fields.Selection(related="document_type_id.has_power_of_attorney_name", string='Has Power of Attorney Name')
    has_tax_identification_no = fields.Selection(related="document_type_id.has_tax_identification_no", string='Has Tax Identification No.')
    has_title_of_license = fields.Selection(related="document_type_id.has_title_of_license", string='Has Title of Licence')
    has_membership_no = fields.Selection(related="document_type_id.has_membership_no", string='Has Membership No')
    has_civil_defense_license = fields.Selection(related="document_type_id.has_civil_defense_license", string='Has Civil Defense Licence')
    has_trade_license = fields.Selection(related="document_type_id.has_trade_license", string='Has Trade Licence')
    is_completed = fields.Selection(related="document_type_id.is_completed", string='Completed')
    
    has_articles_of_association_notarization_date = fields.Selection(related="document_type_id.has_articles_of_association_notarization_date")
    has_amendments_of_association_notarization_date = fields.Selection(related="document_type_id.has_amendments_of_association_notarization_date", string='Has Amendments of Association Notarization Date')
    has_sspa_execution_date = fields.Selection(related="document_type_id.has_sspa_execution_date")
    has_shareholders_agreement_date = fields.Selection(related="document_type_id.has_shareholders_agreement_date", string='Has Shareholders Agreement Date')
    has_service_agreement_date = fields.Selection(related="document_type_id.has_service_agreement_date", string='Has Service Agreement Date')
    has_loan_agreement = fields.Selection(related="document_type_id.has_loan_agreement")
    has_other_agreement_date = fields.Selection(related="document_type_id.has_other_agreement_date", string='has Other Agreement Date')
    
    
    expiry_date = fields.Date(string='Expiry Date')
    issue_date = fields.Date(string='Issue Date')
    reminder_for_renewal = fields.Boolean(string='Reminder for Renewal')
    passport_serial_number = fields.Char(string='Passport Serial Number')
    qid_serial_number = fields.Char(string='QID Serial Number')
    po_box = fields.Char(string='PO Box')
    email_address = fields.Char(string='Email Address')
    phone_number = fields.Char(string='Phone Number')
    reference_number = fields.Char(string='Reference Number')
    power_of_attorney_name = fields.Char(string='Power of Attorney Name')
    tax_identification_no = fields.Char(string='Tax Identification No.')
    title_of_license = fields.Char(string='Title of Licence')
    membership_no = fields.Char(string='Membership No')
    civil_defense_license = fields.Char(string='Civil Defense Licence')
    trade_license = fields.Char(string='Trade Licence')
    completed = fields.Boolean(string='Completed')
    
    articles_of_association_notarization_date = fields.Date(string='Articles of Association Notarization_Date')
    amendments_of_association_notarization_date = fields.Date(string='Amendments of Association Notarization Date')
    sspa_execution_date = fields.Date(string='SSPA Execution Date')
    shareholders_agreement_date = fields.Date(string='Shareholders Agreement Date')
    service_agreement_date = fields.Date(string='Service Agreement Date')
    loan_agreement = fields.Date(string='Loan Agreement Date')
    other_agreement_date = fields.Date(string='Other Agreement Date')
    hide_job_sponsor = fields.Boolean(string='Hide', compute="_compute_hide_job_sponsor")
    name = fields.Char(string="Name")
    is_main_boolean = fields.Boolean(compute='check_if_main_boolean', default=True)
    view_sequence = fields.Integer(string="Sequence Number", related="document_type_id.view_sequence")

    def upload_file(self):
        action = self.env.ref('ebs_fusion_documents.document_button_action').read()[0]
        context = {
            'default_service_process_id': self.service_process_id.id,
            'default_proposal_id': self.service_process_id.proposal_line_id.proposal_id.id,
            'default_document_type_id': self.doc_type_id.id,
            'hide_field': 1,
        }
        action['context'] = context
        return action

    @api.onchange('name')
    def onchange_name(self):
        for rec in self:
            rec.description = rec.name


    @api.depends('partner_id')
    def check_if_main_boolean(self):
        if self._context.get('client_parent_id') and self.partner_id.id == self._context.get('client_parent_id'):
            self.is_main_boolean = False
        else:
            self.is_main_boolean = True

    @api.onchange('passport_name', 'date_of_birth', 'country_passport_id', 'qid_name')
    def check_available_contact(self):
        for rec in self:
            if (rec.passport_name or rec.qid_name) and rec.date_of_birth and rec.country_passport_id:
                contacts = self.env['res.partner'].search([('name', '=', rec.passport_name or rec.qid_name), ('dob', '=', rec.date_of_birth), ('nationality_id', '=', rec.country_passport_id.id)])
                if contacts and (contacts - rec.partner_id):
                    raise ValidationError('Contact Must have different Name, DOB and Nationality.')

    def unlink(self):
        # If delete document than remove all client contact relation if document is link in clint.
        if self.document_type_name in ['Articles of Association', 'Commercial Registration (CR) Application', 'Commercial License', 'Establishment Card']:
            if self.cr_partner_ids:
                for partner in self.cr_partner_ids:
                    line = partner.client_contact_rel_ids.filtered(lambda o: o.client_id.id == self.partner_id.id)
                    if line:
                        line.write({'is_shareholder': False})
            if self.cr_managers_ids:
                for partner in self.cr_managers_ids:
                    line = partner.client_contact_rel_ids.filtered(lambda o: o.client_id.id == self.partner_id.id)
                    if line:
                        line.write({'is_manager_cr': False})
            if self.cl_partner_id:
                line = self.cl_partner_id.client_contact_rel_ids.filtered(lambda o: o.client_id.id == self.partner_id.id)
                if line:
                    line.write({'is_manager_cl': False})
            if self.financial_link_partner:
                line = self.financial_link_partner.client_contact_rel_ids.filtered(lambda o: o.client_id.id == self.partner_id.id)
                if line:
                    line.write({'is_aoa_finance_contact': False})
            if self.general_manager:
                line = self.general_manager.client_contact_rel_ids.filtered(lambda o: o.client_id.id == self.partner_id.id)
                if line:
                    line.write({'is_general_manager': False})
            if self.general_secretary:
                line = self.general_secretary.client_contact_rel_ids.filtered(lambda o: o.client_id.id == self.partner_id.id)
                if line:
                    line.write({'is_general_secretary': False})
            if self.admin_manager:
                line = self.admin_manager.client_contact_rel_ids.filtered(lambda o: o.client_id.id == self.partner_id.id)
                if line:
                    line.write({'is_admin_manager': False})
            if self.banking_signatory:
                line = self.banking_signatory.client_contact_rel_ids.filtered(lambda o: o.client_id.id == self.partner_id.id)
                if line:
                    line.write({'is_corporate_banking_signatory': False})
            if self.liaison_officer:
                line = self.liaison_officer.client_contact_rel_ids.filtered(lambda o: o.client_id.id == self.partner_id.id)
                if line:
                    line.write({'is_liaison_officer': False})
            if self.cr_authorizers_ids:
                for partner in self.cr_authorizers_ids:
                    line = partner.client_contact_rel_ids.filtered(lambda o: o.client_id.id == self.partner_id.id)
                    if line:
                        line.write({'is_manager_ec': False})
            if self.aoa_partner_ids:
                for partner in self.aoa_partner_ids:
                    line = partner.client_contact_rel_ids.filtered(lambda o: o.client_id.id == self.partner_id.id)
                    if line:
                        line.write({'is_aoa_partner': False})
        return super(DocumentsCustom, self).unlink()


    @api.depends('country_passport_id')
    def _compute_hide_job_sponsor(self):
        if self.env.ref('base.qa') == self.country_passport_id:
             self.hide_job_sponsor = True
             self.job_title = False
             self.sponsor_name = False
        else:
             self.hide_job_sponsor = False

    @api.model
    def create(self, vals):
        if 'cr_partner_ids' in vals and vals['cr_partner_ids'][0][2]:
            print(vals['cr_partner_ids'][0][2])
            partner_ids = vals['cr_partner_ids'][0][2]
            partners = self.env['res.partner'].browse(partner_ids)
            for partner in partners:
                partner.is_shareholder = True

                if partner.cr_partner_is_client == True and partner.company_type == 'company':
                    partner.is_customer = True
                    partner.parent_id = False
        if 'aoa_partner_ids' in vals and vals['aoa_partner_ids'][0][2]:
            print(vals['aoa_partner_ids'][0][2])
            partner_ids = vals['aoa_partner_ids'][0][2]
            partners = self.env['res.partner'].browse(partner_ids)

        if 'cr_managers_ids' in vals and vals['cr_managers_ids'][0][2]:
            manager_ids = vals['cr_managers_ids'][0][2]
            managers = self.env['res.partner'].browse(manager_ids)
            for manager in managers:
                manager.is_manager_cr = True
        if 'cl_partner_id' in vals and vals['cl_partner_id']:
            manager_ids = vals['cl_partner_id']
            managers = self.env['res.partner'].browse(manager_ids)
            managers.is_manager_cl = True
        if 'financial_link_partner' in vals and vals['financial_link_partner']:
            manager_ids = vals['financial_link_partner']
            managers = self.env['res.partner'].browse(manager_ids)
            managers.is_aoa_finance_contact = True
        if 'general_manager' in vals and vals['general_manager']:
            manager_ids = vals['general_manager']
            managers = self.env['res.partner'].browse(manager_ids)
            managers.is_general_manager = True
        if 'general_secretary' in vals and vals['general_secretary']:
            manager_ids = vals['general_secretary']
            managers = self.env['res.partner'].browse(manager_ids)
            managers.is_general_secretary = True
        if 'admin_manager' in vals and vals['admin_manager']:
            manager_ids = vals['admin_manager']
            managers = self.env['res.partner'].browse(manager_ids)
            managers.is_admin_manager = True
        if 'banking_signatory' in vals and vals['banking_signatory']:
            manager_ids = vals['banking_signatory']
            managers = self.env['res.partner'].browse(manager_ids)
            managers.is_corporate_banking_signatory = True
        if 'liaison_officer' in vals and vals['liaison_officer']:
            manager_ids = vals['liaison_officer']
            managers = self.env['res.partner'].browse(manager_ids)
            managers.is_liaison_officer = True
        if 'cr_authorizers_ids' in vals and vals['cr_authorizers_ids'][0][2]:
            manager_ids = vals['cr_authorizers_ids'][0][2]
            managers = self.env['res.partner'].browse(manager_ids)
            for manager in managers:
                manager.is_manager_ec = True
        if 'aoa_partner_ids' in vals and vals['aoa_partner_ids'][0][2]:
            manager_ids = vals['aoa_partner_ids'][0][2]
            managers = self.env['res.partner'].browse(manager_ids)
            for manager in managers:
                manager.is_aoa_partner = True

        res = super(DocumentsCustom, self).create(vals)
        if vals.get('agreement_party1'):
            partner = self.env['res.partner'].browse([vals.get('agreement_party1')])
            available_client_line = partner.client_contact_rel_ids.filtered(
                lambda o: o.client_id.id in [vals.get('res_id')])
            if not available_client_line:
                partner.write({'client_contact_rel_ids': [(0, 0, {'client_id': vals.get('res_id')})]})
        if vals.get('agreement_party2'):
            partner = self.env['res.partner'].browse([vals.get('agreement_party2')])
            available_client_line = partner.client_contact_rel_ids.filtered(
                lambda o: o.client_id.id in [vals.get('res_id')])
            if not available_client_line:
                partner.write({'client_contact_rel_ids': [(0, 0, {'client_id': vals.get('res_id')})]})
        if vals.get('power_of_attorney_contact_person'):
            partner = self.env['res.partner'].browse([vals.get('power_of_attorney_contact_person')])
            available_client_line = partner.client_contact_rel_ids.filtered(
                lambda o: o.client_id.id in [vals.get('res_id')])
            if not available_client_line:
                partner.write({'client_contact_rel_ids': [(0, 0, {'client_id': vals.get('res_id')})]})
        return res
    
    def write(self, vals):
        # if changes is done from document form view, create or remove client contact relation based on changes.
        if vals.get('cr_partner_ids') and not ('rmv_cr_ptnr' in self._context or 'add_cr_ptnr' in self._context) and self._context.get('display_stages_type') != 'contacts':
            if self.id == self.partner_id.cr_document_id.id:
                self.partner_id.with_context({'add_shareholder':True}).write({'shareholder_contact_ids':[(6,0,vals.get('cr_partner_ids')[0][2])]})
                self.remove_client_contact_rel(self.cr_partner_ids.ids, vals.get('cr_partner_ids')[0], 'is_shareholder', self.partner_id)
                self.create_client_contact_rel(vals, vals.get('cr_partner_ids')[0], {'is_shareholder': True}, True)
        if vals.get('cr_managers_ids') and not any(k in self._context for k in ("rmv_cr_mngr","add_cr_mngr")) and self._context.get('display_stages_type') != 'contacts':
            if self.id == self.partner_id.cr_document_id.id:
                self.remove_client_contact_rel(self.cr_managers_ids.ids, vals.get('cr_managers_ids')[0], 'is_manager_cr', self.partner_id)
                self.create_client_contact_rel(vals, vals.get('cr_managers_ids')[0], {'is_manager_cr': True}, True)
        if (vals.get('cl_partner_id') or vals.get('cl_partner_id') == False) and not any(k in self._context for k in ("rmv_cl_mngr","add_cl_mngr")) and self._context.get('display_stages_type') != 'contacts':
            if self.id == self.partner_id.cl_document_id.id:
                self.remove_client_contact_rel(self.cl_partner_id.ids, [vals.get('cl_partner_id')], 'is_manager_cl', self.partner_id)
                self.create_client_contact_rel(vals, [vals.get('cl_partner_id')], {'is_manager_cl': True}, True)
        if (vals.get('financial_link_partner') or vals.get('financial_link_partner') == False) and not any(k in self._context for k in ("rmv_aoa_prtnr","add_aoa_prtnr")) and self._context.get('display_stages_type') != 'contacts':
            if self.id == self.partner_id.aoa_document_id.id:
                self.remove_client_contact_rel(self.financial_link_partner.ids, [vals.get('financial_link_partner')], 'is_aoa_finance_contact', self.partner_id)
                self.create_client_contact_rel(vals, [vals.get('financial_link_partner')], {'is_aoa_finance_contact': True}, True)
        if (vals.get('general_manager') or vals.get('general_manager') == False) and not any(k in self._context for k in ("rmv_aoa_prtnr","add_aoa_prtnr")) and self._context.get('display_stages_type') != 'contacts':
            if self.id == self.partner_id.aoa_document_id.id:
                self.remove_client_contact_rel(self.general_manager.id, [vals.get('general_manager')], 'is_general_manager', self.partner_id)
                self.create_client_contact_rel(vals, [vals.get('general_manager')], {'is_general_manager': True}, True)
        if (vals.get('general_secretary') or vals.get('general_secretary') == False) and not any(k in self._context for k in ("rmv_aoa_prtnr","add_aoa_prtnr")) and self._context.get('display_stages_type') != 'contacts':
            if self.id == self.partner_id.aoa_document_id.id:
                self.remove_client_contact_rel(self.general_secretary.id, [vals.get('general_secretary')], 'is_general_secretary', self.partner_id)
                self.create_client_contact_rel(vals, [vals.get('general_secretary')], {'is_general_secretary': True}, True)
        if (vals.get('admin_manager') or vals.get('admin_manager') == False) and not any(k in self._context for k in ("rmv_aoa_prtnr","add_aoa_prtnr")) and self._context.get('display_stages_type') != 'contacts':
            if self.id == self.partner_id.aoa_document_id.id:
                self.remove_client_contact_rel(self.admin_manager.id, [vals.get('admin_manager')], 'is_admin_manager', self.partner_id)
                self.create_client_contact_rel(vals, [vals.get('admin_manager')], {'is_admin_manager': True}, True)
        if (vals.get('banking_signatory') or vals.get('banking_signatory') == False) and not any(k in self._context for k in ("rmv_aoa_prtnr","add_aoa_prtnr")) and self._context.get('display_stages_type') != 'contacts':
            if self.id == self.partner_id.aoa_document_id.id:
                self.remove_client_contact_rel(self.banking_signatory.id, [vals.get('banking_signatory')], 'is_corporate_banking_signatory', self.partner_id)
                self.create_client_contact_rel(vals, [vals.get('banking_signatory')], {'is_corporate_banking_signatory': True}, True)
        if (vals.get('liaison_officer') or vals.get('liaison_officer') == False) and not any(k in self._context for k in ("rmv_aoa_prtnr","add_aoa_prtnr")) and self._context.get('display_stages_type') != 'contacts':
            if self.id == self.partner_id.aoa_document_id.id:
                self.remove_client_contact_rel(self.liaison_officer.id, [vals.get('liaison_officer')], 'is_liaison_officer', self.partner_id)
                self.create_client_contact_rel(vals, [vals.get('liaison_officer')], {'is_liaison_officer': True}, True)
        if vals.get('cr_authorizers_ids') and not any(k in self._context for k in ("add_ec_mngr","rmv_ec_mngr")) and self._context.get('display_stages_type') != 'contacts':
            if self.id == self.partner_id.ec_document_id.id:
                self.remove_client_contact_rel(self.cr_authorizers_ids.ids, vals.get('cr_authorizers_ids')[0], 'is_manager_ec', self.partner_id)
                self.create_client_contact_rel(vals, vals.get('cr_authorizers_ids')[0], {'is_manager_ec': True}, True)
        if vals.get('aoa_partner_ids') and not any(k in self._context for k in ("add_aoa_ptnr","rmv_aoa_ptnr")) and self._context.get('display_stages_type') != 'contacts':
            if self.id == self.partner_id.aoa_document_id.id:
                self.remove_client_contact_rel(self.aoa_partner_ids.ids, vals.get('aoa_partner_ids')[0], 'is_aoa_partner', self.partner_id)
                self.create_client_contact_rel(vals, vals.get('aoa_partner_ids')[0], {'is_aoa_partner': True}, True)
        if vals.get('agreement_party1') or vals.get('agreement_party1') == False:
            partner = self.env['res.partner'].browse([vals.get('agreement_party1')])
            available_client_line = partner.client_contact_rel_ids.filtered(
                lambda o: o.client_id.id in [vals.get('partner_id') or self.partner_id.id])
            if not available_client_line:
                partner.write({'client_contact_rel_ids': [(0, 0, {'client_id': vals.get('partner_id') or self.partner_id.id})]})
            if vals.get('agreement_party1') == False:
                available_client_line = self.agreement_party1.client_contact_rel_ids.filtered(
                    lambda o: o.client_id.id in [vals.get('partner_id') or self.partner_id.id])
                if available_client_line:
                    available_client_line.unlink()
        if vals.get('agreement_party2') or vals.get('agreement_party2') == False:
            partner = self.env['res.partner'].browse([vals.get('agreement_party2')])
            available_client_line = partner.client_contact_rel_ids.filtered(
                lambda o: o.client_id.id in [vals.get('partner_id') or self.partner_id.id])
            if not available_client_line:
                partner.write({'client_contact_rel_ids': [(0, 0, {'client_id': vals.get('partner_id') or self.partner_id.id})]})
            if vals.get('agreement_party2') == False:
                available_client_line = self.agreement_party2.client_contact_rel_ids.filtered(
                    lambda o: o.client_id.id in [vals.get('partner_id') or self.partner_id.id])
                if available_client_line:
                    available_client_line.unlink()
        if vals.get('power_of_attorney_contact_person') or vals.get('power_of_attorney_contact_person') == False:
            partner = self.env['res.partner'].browse([vals.get('power_of_attorney_contact_person')])
            available_client_line = partner.client_contact_rel_ids.filtered(
                lambda o: o.client_id.id in [vals.get('partner_id') or self.partner_id.id])
            if not available_client_line:
                partner.write({'client_contact_rel_ids': [(0, 0, {'client_id': vals.get('partner_id') or self.partner_id.id})]})
            if vals.get('power_of_attorney_contact_person') == False:
                available_client_line = self.power_of_attorney_contact_person.client_contact_rel_ids.filtered(
                    lambda o: o.client_id.id in [vals.get('partner_id') or self.partner_id.id])
                if available_client_line:
                    available_client_line.unlink()


        res = super(DocumentsCustom, self).write(vals)
        # If link existing document in client, create client contact relation.
        if vals.get('partner_id') or self.is_client_rel or (vals.get('cr_partner_ids') or vals.get('cr_managers_ids') or vals.get('cr_authorizers_ids') or vals.get('aoa_partner_ids') or vals.get('cl_partner_id') or vals.get('financial_link_partner') or vals.get('general_manager') or vals.get('banking_signatory') or vals.get('general_manager') or vals.get('admin_manager') or vals.get('general_secretary') or vals.get('liaison_officer')) and not any(k in self._context for k in ("rmv_ec_mngr", "add_ec_mngr","rmv_cl_mngr","add_cl_mngr","rmv_aoa_prtnr","add_aoa_prtnr",
                          "rmv_cr_mngr","add_cr_mngr","rmv_cr_ptnr","add_cr_ptnr","rmv_aoa_ptnr","add_aoa_ptnr","rmv_prmry_cntct"
                          ,"add_prmry_cntct",'rmv_scndr_cntct','add_scndr_cntct', 'add_hr_cntct', 'rmv_hr_cntct', 'add_finance_cntct', 'rmv_finance_cntct','add_auditor'
                          )):
            if self._context.get('display_stages_type') == 'clients':
                self.create_client_contact_rel(vals, self.cr_partner_ids.ids, {'is_shareholder': True}, False)
                self.create_client_contact_rel(vals, self.cr_managers_ids.ids, {'is_manager_cr': True}, False)
                self.create_client_contact_rel(vals, self.cl_partner_id.ids, {'is_manager_cl': True}, False)
                self.create_client_contact_rel(vals, self.financial_link_partner.ids, {'is_aoa_finance_contact': True}, False)
                self.create_client_contact_rel(vals, self.general_manager.ids, {'is_general_manager': True},False)
                self.create_client_contact_rel(vals, self.general_secretary.ids, {'is_general_secretary': True}, False)
                self.create_client_contact_rel(vals, self.admin_manager.ids, {'is_admin_manager': True}, False)
                self.create_client_contact_rel(vals, self.banking_signatory.ids, {'is_corporate_banking_signatory': True}, False)
                self.create_client_contact_rel(vals, self.liaison_officer.ids, {'is_liaison_officer': True}, False)
                self.create_client_contact_rel(vals, self.cr_authorizers_ids.ids, {'is_manager_ec': True}, False)
                self.create_client_contact_rel(vals, self.aoa_partner_ids.ids, {'is_aoa_partner': True}, False)

        return res

    def remove_client_contact_rel(self, field_ids, new_ids, boolean_str, client):
        if new_ids[0] == 3 and len(new_ids) > 1:
            contact = self.env['res.partner'].browse(new_ids[1])
            client_line = contact.client_contact_rel_ids.filtered(lambda o: o.client_id.id == client.id)
            if client_line:
                client_line.write({boolean_str: False})
        elif new_ids[0] == 6 and len(new_ids) > 1:
            for contact_id in field_ids:
                if contact_id not in new_ids[2]:
                    contact = self.env['res.partner'].browse(contact_id)
                    client_line = contact.client_contact_rel_ids.filtered(lambda o: o.client_id.id == client.id)
                    if client_line:
                        client_line.write({boolean_str: False})
        elif len(new_ids) == 1:
            contact = self.env['res.partner'].browse(field_ids)
            client_line = contact.client_contact_rel_ids.filtered(lambda o: o.client_id.id == client.id)
            if client_line:
                client_line.write({boolean_str: False})

    def create_client_contact_rel(self,vals, field_ids, update_dict, check_index):
        partners = False
        if check_index == True:
            if field_ids[0] == 4  and len(field_ids) > 1:
                partner = self.env['res.partner'].browse(field_ids[1])
                available_client_line = partner.client_contact_rel_ids.filtered(
                    lambda o: o.client_id.id in [vals.get('partner_id') or self.partner_id.id])
                if available_client_line:
                    update_dict.update({'permission': partner.permission})
                    available_client_line.write(update_dict)
                else:
                    update_dict.update(
                        {'client_id': vals.get('partner_id') or self.partner_id.id, 'permission': partner.permission})
                    partner.write({'client_contact_rel_ids': [(0, 0, update_dict)]})
            elif field_ids[0] == 6  and len(field_ids) > 1:
                for partner_id in field_ids[2]:
                    partner = self.env['res.partner'].browse(partner_id)
                    available_client_line = partner.client_contact_rel_ids.filtered(
                        lambda o: o.client_id.id in [vals.get('partner_id') or self.partner_id.id])
                    if available_client_line:
                        update_dict.update({'permission': partner.permission})
                        available_client_line.write(update_dict)
                    else:
                        update_dict.update({'client_id': vals.get('partner_id') or self.partner_id.id, 'permission': partner.permission})
                        partner.write({'client_contact_rel_ids': [(0, 0, update_dict)]})
            elif len(field_ids) == 1:
                partner = self.env['res.partner'].browse(field_ids)
                available_client_line = partner.client_contact_rel_ids.filtered(
                    lambda o: o.client_id.id in [vals.get('partner_id') or self.partner_id.id])
                if available_client_line:
                    update_dict.update({'permission': partner.permission})
                    available_client_line.write(update_dict)
                else:
                    update_dict.update(
                        {'client_id': vals.get('partner_id') or self.partner_id.id, 'permission': partner.permission})
                    partner.write({'client_contact_rel_ids': [(0, 0, update_dict)]})
        else:
            for partner_id in field_ids:
                partner = self.env['res.partner'].browse(partner_id)
                available_client_line = partner.client_contact_rel_ids.filtered(
                    lambda o: o.client_id.id in [vals.get('partner_id') or self.partner_id.id])
                if available_client_line:
                    update_dict.update({'permission': partner.permission})
                    available_client_line.write(update_dict)
                else:
                    update_dict.update({'client_id': vals.get('partner_id') or self.partner_id.id, 'permission': partner.permission})
                    partner.write({'client_contact_rel_ids': [(0, 0, update_dict)]})


    @api.model
    def default_get(self, fields):
        res = super(DocumentsCustom, self).default_get(fields)
        print("++++++++++++++++++++++++++++==",self._context)
        str = ''
        if self._context.get('cr_document') == True:
            str = 'Commercial Registration (CR) Application'
            if 'shareholder_contact_ids' in self._context.keys() and self._context.get('shareholder_contact_ids'):
                res.update({'cr_partner_ids': [(6, 0, self._context.get('shareholder_contact_ids')[0][2])]})
        if self._context.get('cl_document'):
            str = 'Commercial License'
        if self._context.get('aoa_document'):
            str = 'articles of association'

        if self._context.get('ec_document'):
            str = 'Establishment Card'
            cr_manager_ids = self.env['documents.document'].browse(self._context.get('cr_document_id')).cr_managers_ids
            res.update({'cr_authorizers_ids': [(6, 0, cr_manager_ids.ids)]})
        if self._context.get('passport'):
            str = 'Passport'
        if self._context.get('qid'):
            str = 'QID'
        if self._context.get('tax_card'):
            str = 'Tax Card'
        if self._context.get('proposal_doc'):
            str = 'Proposal'

        if self._context.get('default_passport_name'):
            res.update({'passport_name': self._context.get('default_passport_name')})
        if self._context.get('client_parent_id') and self._context.get('is_branch_main'):
            partners = self.env['res.partner'].sudo().browse(self._context.get('client_parent_id'))
            if partners:
                res.update({'cr_partner_ids':[(6,0,partners.cr_partner_ids.ids)]})
        if self._context.get('default_name'):
            res.update({'cr_trade_name': self._context.get('default_name')})
            res.update({'cl_name': self._context.get('default_name')})
            res.update({'est_name_en': self._context.get('default_name')})
        if self._context.get('default_arabic_name'):

            res.update({'name': ''})
        document_type_id = self.env['ebs.document.type'].sudo().search([('meta_data_template', '=', str)])
        print("resssssssssssssssssssssssss",res)
        if document_type_id:
            res.update({'document_type_id': document_type_id.id})
        return res
    
    @api.onchange('sponsor_name')
    def onchange_sponsor_name(self):
        for rec in self:
            partner_id = self.env['res.partner'].browse([self._context.get('default_partner_id')])
            if rec.sponsor_name:
                partner_id.dependent_id = rec.sponsor_name.id
            else:
                partner_id.dependent_id = False



    @api.onchange('document_type_id')
    def onchange_document_type_id(self):
        for rec in self:
            if rec.document_number and rec.document_type_id:
                search_record = self.env['documents.document'].sudo().search(
                    [('document_number', '=', rec.document_number),
                     ('document_type_id', '=', rec.document_type_id.id)]) - rec._origin
                if search_record:
                    raise ValidationError("A %s document with this document number %s already exists!"
                                          % (rec.document_type_id.name, rec.document_number))

            res = {}
            if self._context.get('licence'):
                res.update({'domain': {'document_type_id': [('is_license', '=', True)]}})
                res.update({'context': {'partner_id': {'default_partner_id':id, 'default_res_model': self._context.get('active_model'), 'hide_field': 1, }}})
                return res

    @api.onchange('cr_reg_no')
    def onchange_cr_reg_no(self):
        for rec in self:
            if rec.cr_reg_no:
                rec.cr_reg_no = self.translate_doc_no(rec.cr_reg_no)
                rec.document_number = rec.cr_reg_no

    @api.onchange('est_id')
    def onchange_est_id(self):
        for rec in self:
            if rec.est_id:
                rec.est_id = self.translate_doc_no(rec.est_id)
                rec.document_number = rec.est_id

    @api.onchange('license_number')
    def onchange_license_number(self):
        for rec in self:
            if rec.license_number:
                rec.license_number = self.translate_doc_no(rec.license_number)
                rec.document_number = rec.license_number

    @api.onchange('passport_no')
    def onchange_passport_no(self):
        for rec in self:
            if rec.passport_no:
                rec.passport_no = self.translate_doc_no(rec.passport_no)
                rec.document_number = rec.passport_no

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        if 'passport_owner_id' in self._context and self._context.get('passport_owner_id') != False:
            document_type = self.env['ebs.document.type'].search([('meta_data_template', '=', 'Passport')])
            partner_id = self._context.get('passport_owner_id')
            query = """ Select array_agg(id) as owner_id from documents_document where partner_id=%s and document_type_id=%s """ % (partner_id, document_type.id)
            self.env.cr.execute(query)
            query_result = self.env.cr.dictfetchall()
            res = query_result and query_result[0].get('owner_id')
            return res
        if 'qid_owner_id' in self._context and self._context.get('qid_owner_id') != False:
            document_type = self.env['ebs.document.type'].search([('meta_data_template', '=', 'QID')])
            partner_id = self._context.get('qid_owner_id')
            query = """ Select array_agg(id) as owner_id from documents_document where partner_id=%s and document_type_id=%s """ % (partner_id, document_type.id)
            self.env.cr.execute(query)
            query_result = self.env.cr.dictfetchall()
            res = query_result and query_result[0].get('owner_id')
            return res
        if 'visa_owner_id' in self._context and self._context.get('visa_owner_id') != False:
            document_type = self.env['ebs.document.type'].search([('name', '=', 'Visa')])
            partner_id = self._context.get('visa_owner_id')
            query = """ Select array_agg(id) as owner_id from documents_document where partner_id=%s and document_type_id=%s """ % (partner_id, document_type.id)
            self.env.cr.execute(query)
            query_result = self.env.cr.dictfetchall()
            res = query_result and query_result[0].get('owner_id')
            return res
        res = super(DocumentsCustom, self)._search(args=args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)
        return res

    
    