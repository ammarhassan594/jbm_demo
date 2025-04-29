from odoo import api, fields, models, _
from datetime import date
from odoo.exceptions import UserError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    gross_profit = fields.Float("Gross Profit", compute="_compute_gross_profit")
    crm_proposal_ids = fields.One2many('ebs.crm.proposal', 'lead_id', String="CRM Proposal",
                                       context={'active_test': False})
    opportunity_type_service_mapping_ids = fields.One2many('opportunity.type.service.mapping', 'lead_id',
                                                           string='Opportunity Type Service Mapping')
    company_type = fields.Selection([('fme', 'FME'), ('fss', 'FSS'), ('fos', 'FOS')], string='FME/FSS/FOS')
    fme = fields.Boolean('FME')
    fss = fields.Boolean('FSS')
    fos = fields.Boolean('FOS')
    total_service_fee = fields.Float("Total Service Fee")
    monthly_service_fee = fields.Float("Monthly Service Fee")
    advance_payment_amount_percentage = fields.Float("Advance Payment Amount")
    annual_payment = fields.Float("Annual Payment")
    annual_turnover = fields.Float("Annual Turnover")
    deposit_amount = fields.Float("Deposit Amount")
    insurance_amount = fields.Float("Insurance Amount")
    penalty_amount = fields.Float('Penalty Amount')
    contract_count = fields.Integer(compute='contract_compute')
    payment_terms_id = fields.Many2one('account.payment.term', string='Payment Terms')
    contract_proposal_fee_ids = fields.One2many('ebs.contract.proposal.fees', 'lead_id', 'Fees')
    fos_fee_structure_ids = fields.One2many('ebs.proposal.fos.fee.structure', 'lead_id', string="FOS Fees Structure")
    salary_structure_ids = fields.One2many('ebs.proposal.salary.structure', 'lead_id',
                                           string="Monthly Salary Breakdown")
    permit_issuance_ids = fields.One2many('ebs.proposal.permit.issuance', 'lead_id', string="Work Permit Issuance")

    def contract_compute(self):
        for record in self:
            record.contract_count = self.env['ebs.crm.proposal'].search_count(
                [('lead_id', '=', self.id), ('type', '=', 'proposal')])

    def open_contract(self):

        return self.open_contract_action(self.id)

    def open_contract_action(self, lead_id):
        action = self.env.ref('ebs_fusion_services.action_ebs_crm_proposal').read()[0]
        lead = self.env['crm.lead'].browse(lead_id)
        contract_ids = self.env['ebs.crm.proposal'].search([('lead_id', '=', lead_id), ('type', '=', 'proposal')])
        approved_opportunity_type_service_mapping_lines = lead.opportunity_type_service_mapping_ids.filtered(
            lambda o: o.state == 'approved')
        if not self._context.get('generate_button'):
            action['context'] = {
                'create': 0,
                'default_type': 'proposal',
                'default_lead_id': lead_id,
                'default_contact_id': lead.partner_id.id,
                'default_company_id': lead.company_id.id,
                'default_date': date.today(),
                'lead_id': True,

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
                             'default_lead_id': lead_id,
                             'default_contact_id': lead.partner_id.id,
                             'default_company_id': lead.company_id.id,
                             'default_date': date.today(),
                             'lead_id': True,
                             'create': 0,

                             }
        return action

    def open_proposal(self):
        if any(line.state == 'rejected' for line in self.opportunity_type_service_mapping_ids):

            return {
                'name': _('Generate Contract'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'warning.wizard',
                'target': 'new',
                'context': {
                    'model': 'crm.lead',
                    'object_id': self.id,
                    'kwargs': {'lead_id': self.id},
                    'method': 'open_proposal_action',
                    'message': 'Press confirm to continue.'
                }
            }
        else:
            return self.open_proposal_action(self.id)

    def open_proposal_action(self, lead_id):
        lead = self.env['crm.lead'].browse(lead_id)
        action = self.env.ref('ebs_fusion_services.action_ebs_crm_proposal').read()[0]
        action['views'] = [(self.env.ref('ebs_fusion_services.view_ebs_crm_proposal_form').id, 'form')]
        proposal_ids = self.env['ebs.crm.proposal'].search([('lead_id', '=', lead_id), ('type', '=', 'agreement')])
        proposal_lines = []
        approved_opportunity_type_service_mapping_lines = lead.opportunity_type_service_mapping_ids.filtered(
            lambda o: o.state == 'approved')
        for line in approved_opportunity_type_service_mapping_lines:
            vals = {
                'service_id': line.service_id.id,
                'service_option_id': line.service_option_id.id,
                'govt_product_id': line.service_option_id.govt_product_id.id,
                'govt_fees': line.govt_fees,
                'fusion_product_id': line.service_option_id.fusion_product_id.id,
                'fusion_fees': line.fusion_fees,
            }
            proposal_lines.append((0, 0, vals))
        if proposal_ids:
            action['context'] = {'default_type': 'agreement',
                                 'default_lead_id': lead_id,
                                 'default_contact_id': lead.partner_id.id,
                                 'default_proposal_company_ids': [(6, 0, lead.company_id.ids)],

                                 'default_proposal_lines': proposal_lines,
                                 'default_date': date.today()}
            action['views'] = [(self.env.ref('ebs_fusion_services.view_ebs_crm_proposal_tree').id, 'tree'),
                               (self.env.ref('ebs_fusion_services.view_ebs_crm_proposal_form').id, 'form')]
            action['view_mode'] = 'tree'
            action['domain'] = [('id', 'in', proposal_ids.ids)]
            return action
        action['view_mode'] = 'form'
        action['target'] = 'self'
        action['context'] = {'default_type': 'agreement',
                             'default_lead_id': lead_id,
                             'default_contact_id': lead.partner_id.id,
                             'default_proposal_company_ids': [(6, 0, lead.company_id.ids)],
                             'default_proposal_lines': proposal_lines,
                             'default_date': date.today()}
        return action

    @api.depends('cost', 'crm_proposal_ids')
    def _compute_gross_profit(self):
        for rec in self:
            gross_profit = 0.00
            proposals = self.env['ebs.crm.proposal'].search(
                [('id', 'in', rec.crm_proposal_ids.ids), ('active', '=', True)], limit=1, order='id desc')
            if proposals:
                gross_profit = proposals.real_revenue - rec.cost
            rec.gross_profit = gross_profit


class OpportunityTypeServiceMapping(models.Model):
    _name = 'opportunity.type.service.mapping'
    _description = 'Opportunity Type Service Mapping '

    lead_id = fields.Many2one('crm.lead')
    company_id = fields.Many2one('res.company', related='lead_id.company_id')

    service_id = fields.Many2one('ebs.crm.service', String='Service', domain=[('is_group', '=', True)])
    service_option_id = fields.Many2one('ebs.service.option', string='Service Option',
                                        domain="[('service_id', '=', service_id), ('company_id', '=', company_id)]")
    qty = fields.Integer('Quantity', default=1)
    govt_fees = fields.Float(string='Govt. Fees')
    fusion_fees = fields.Float(string='Main Company Fees')
    stage_code_service = fields.Integer(related='lead_id.stage_code')

    state = fields.Selection([('draft', 'Draft'), ('approved', 'Approved'), ('rejected', 'Rejected')],
                             string="Approved", default='draft')

    def approve_opportunity_type_service_mapping_line(self):
        for rec in self:
            rec.write({'state': 'approved'})

    def reject_opportunity_type_service_mapping_line(self):
        for rec in self:
            rec.write({'state': 'rejected'})

    @api.onchange('service_id')
    def onchange_service(self):
        self.ensure_one()
        domain = [('state', '=', 'ready')]
        count = 0
        if self.lead_id.company_type == 'fme':
            count += 1
            domain.append(('fme', '=', True))
        if self.lead_id.company_type == 'fss':
            count += 1
            domain.append(('fss', '=', True))
        if self.lead_id.company_type == 'fos':
            count += 1
            domain.append(('fos', '=', True))
        if count == 2:
            domain.insert(0, '|')
        if count == 3:
            domain.insert(0, '|')
            domain.insert(1, '|')
        return {
            'domain':
                {'service_id': domain}
        }

    @api.onchange('service_option_id')
    def onchange_service_option_id(self):
        self.ensure_one()
        self.govt_fees = self.service_option_id.govt_fees
        self.fusion_fees = self.service_option_id.fusion_fees
