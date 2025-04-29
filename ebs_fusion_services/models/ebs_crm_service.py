from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime


class ebsCrmService(models.Model):
    _name = 'ebs.crm.service'
    _rec_name = 'name'
    _description = 'EBS CRM Service'

    name = fields.Char("Name", required=1)
    workflow_lines = fields.One2many('ebs.crm.workflow', 'service_id', string='Workflows', copy=True)
    document_type_ids = fields.One2many('ebs.service.document.type', 'service_id', string='Document Types', copy=True)
    category_id = fields.Many2one('ebs.crm.service.category', 'Service Category')
    authority_id = fields.Many2one('ebs.crm.service.authority', string='Authority/Ministry')
    service_id = fields.Char('Service ID')
    state = fields.Selection([('draft', 'Draft'), ('ready', 'Ready')], string='Status', default='draft')
    priority = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], string='Priority')
    document_classification = fields.Selection(
        [('general', 'General'), ('confidential', 'Confidential'), ('highly_confidential', 'Highly Confidential')],
        string='Document Classification')
    service_template_id = fields.Many2one('ebs.crm.service.template')
    service_group_id = fields.Many2one('ebs.crm.service.groups', string="Group")
    days_to_complete = fields.Float(string='Days to complete')
    is_group = fields.Boolean('Is Group')

    labor_quota = fields.Boolean('Labor Quota')
    company = fields.Boolean('Company', default=True)
    employee = fields.Boolean('Is Employee')
    visitor = fields.Boolean('Visitor')
    dependent = fields.Boolean('Dependent')
    service_type = fields.Selection([('individual', 'Individual'), ('corporate', 'Corporate')], string="Service Type")
    sequence_ids = fields.One2many('ir.sequence', 'service_id', string='Sequences', copy=False)
    abbreviation = fields.Char('Abbreviation')

    new_option = fields.Boolean('New')
    renew = fields.Boolean('Renew')
    manage = fields.Boolean('Manage')
    fme = fields.Boolean('FME')
    fss = fields.Boolean('FSS')
    fos = fields.Boolean('FOS')
    service_option_ids = fields.One2many('ebs.service.option', 'service_id', string='Service Options', copy=True)
    target_audience = fields.Selection([('company', 'Company'), ('person', 'Person')], default='company',
                                       string='Target Audience')
    dependent_services_ids = fields.One2many('ebs.crm.service.line', 'services_id', 'Service', copy=True)
    fines_applicable = fields.Boolean('Fines Applicable')
    service_fine_ids = fields.One2many('ebs.crm.service.fines', 'service_id', string='Service Fines', copy=True)

    def unlink(self):
        for rec in self:
            rec.sequence_ids.unlink()
        return super(ebsCrmService, self).unlink()

    def set_ready(self):

        if not self.service_id:
            raise UserError(_('Service ID can not be empty.'))

        self.sudo()._create_sequence({'service_id': self.service_id})
        if not self.workflow_lines and not self.is_group:
            raise UserError(_('At least one workflow line must be entered.'))
        if self.document_type_ids:
            for rec in self.document_type_ids:
                if not rec.input and not rec.output:
                    raise UserError(_('At least one check box should be check in document types.'))
        return self.write({'state': 'ready'})

    def set_draft(self):
        return self.write({'state': 'draft'})

    @api.model
    def _get_sequence_prefix(self, code, refund=False):
        prefix = code.upper()
        if refund:
            prefix = 'R' + prefix
        return prefix + '/%(range_year)s/'

    @api.model
    def _create_sequence(self, vals):
        """ Create new no_gap entry sequence for every new Journal"""
        seq_name = vals['service_id']

        for company in self.env['res.company'].search([]):
            prefix = self._get_sequence_prefix(seq_name)
            company_sequence_id = self.sequence_ids.mapped('company_id').ids
            if not company.id in company_sequence_id and company.partner_id.abbreviation:
                prefix = company.partner_id.abbreviation + " - " + prefix
                seq = {'name': _('%s Sequence') % seq_name, 'implementation': 'no_gap', 'prefix': prefix, 'padding': 5,
                       'number_increment': 1, 'use_date_range': True, 'company_id': company.id}
                seq = self.env['ir.sequence'].sudo().create(seq)
                today = datetime.today()
                seq.sudo()._create_date_range_seq(today.replace(year=today.year + 1))
                seq.sudo()._create_date_range_seq(today.replace(year=today.year + 2))
                seq.sudo()._create_date_range_seq(today.replace(year=today.year + 3))

                self.sequence_ids = [(4, seq.id)]

    @api.onchange('target_audience')
    def onchange_target_audience(self):
        for rec in self:
            if rec.target_audience == 'company':
                rec.company = True
                rec.employee = False
                rec.visitor = False
                rec.dependent = False
            if rec.target_audience == 'person':
                rec.company = False
                rec.employee = True
                rec.visitor = True
                rec.dependent = True

    @api.onchange('dependent_services_ids')
    def dependent_services_ids_onchnage(self):
        if self.is_group:
            print(self.dependent_services_ids)
            lines = self.env['ebs.crm.service.line'].search([('services_id', '=', self._origin.id)])
            print(lines)
            dependent_service_data = self.dependent_services_ids.read_group([('services_id', '=', self._origin.id)],
                                                                            ['service'], ['sequence'])
            mapped_data = {m['sequence']: m['sequence_count'] for m in dependent_service_data}

            total = 0
            for line in mapped_data:
                service_ids = self.dependent_services_ids.filtered(lambda o: o.sequence == line).mapped('service')
                max = 0
                for service in service_ids:
                    if service.days_to_complete > max:
                        max = service.days_to_complete
                total += max
            self.days_to_complete = total

    @api.onchange('is_group')
    def onchange_is_group(self):
        for rec in self:
            if rec.is_group:
                rec.labor_quota = False


class EbsServiceLine(models.Model):
    _name = 'ebs.crm.service.line'
    _description = 'EBS CRM Service Line'

    sequence = fields.Integer(string="Sequence", copy=False, store=True)
    services_id = fields.Many2one('ebs.crm.service', string="Service")
    service = fields.Many2one('ebs.crm.service', string="Service", domain="[('is_group','=',False)]")

    def action_show_service(self):
        self.ensure_one()
        form_view = self.env.ref('ebs_fusion_services.view_ebs_crm_service_form')
        tree_view = self.env.ref('ebs_fusion_services.view_ebs_crm_proposal_workflow_tree')

        return {
            'name': _('Workflows'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'ebs.crm.service',
            'views': [(form_view.id, 'form')],
            'view_id': form_view.id,
            'target': 'current',
            'res_id': self.service.id,
            'domain': [('id', '=', self.service)]

        }


class ebsCrmWorkflow(models.Model):
    _name = 'ebs.crm.workflow'
    _description = 'EBS CRM Workflow'
    _rec_name = 'name'

    def _get_service_workflow(self):
        domain = []
        if self.service_id:
            domain = [('service_id', '=', self.service_id.id)]
        else:
            if self._context.get('service_id'):
                workflow = self.env['ebs.crm.service'].browse([self._context.get('service_id')])
                domain = [('id', 'in', workflow.service_option_ids.ids)]
        return domain

    def _get_dependent_services(self):
        domain = []
        if self.service_id:
            dependant_service_ids = self.service_id.dependent_services_ids.mapped('service').ids
            domain = [('id', 'in', dependant_service_ids)]
        else:
            if self._context.get('service_id'):
                service_id = self.env['ebs.crm.service'].browse([self._context.get('service_id')])
                dependant_service_ids = service_id.dependent_services_ids.mapped('service').ids
                domain = [('id', 'in', dependant_service_ids)]
        return domain

    sequence = fields.Integer(index=True,
                              help="Gives the sequence order when displaying a list of bank statement lines.",
                              default=1)
    name = fields.Text("Process", required=1)

    stage_id = fields.Many2one('ebs.crm.service.stage', 'Service Stage')
    activity_id = fields.Many2one('ebs.crm.service.activity', 'Activity', domain="[('stage_id','=', stage_id)]")
    output = fields.Text('Output', required=1)

    responsible_user_id = fields.Many2one('ebs.services.user.group', 'Service User Group', )
    replacement_id = fields.Many2one('hr.department', 'Replacement Department')

    service_id = fields.Many2one('ebs.crm.service')
    service_phase = fields.Selection([('manual', 'Manual'), ('online', 'Online')], string='Type')
    proposal_line_ids = fields.Many2many('ebs.crm.proposal.line', 'prop_line_workflow_rel', 'workflow_id',
                                         'proposal_line_id')
    proposal_ids = fields.Many2many('ebs.crm.proposal', 'prop_workflow_rel', 'workflow_id',
                                    'proposal_id')
    dependant_workflow_ids = fields.Many2many('ebs.crm.workflow', 'service_workflow_dependant_rel', 'workflow_id',
                                              'dependant_id',
                                              string='Required Completed Workflows',
                                              domain="[('service_id','=',service_id)]")
    required_completed_service_ids = fields.Many2many('ebs.crm.service', 'dependant_service_workflow_rel',
                                                      'workflow_id', 'service_id', string='Required Completed Service',
                                                      domain=_get_dependent_services)

    in_document_types = fields.Many2many('ebs.document.type', 'service_workflow_all_intype',
                                         compute='compute_document_types')
    out_document_types = fields.Many2many('ebs.document.type', 'service_workflow_all_outtype',
                                          compute='compute_document_types')
    required_in_docs = fields.Many2many('ebs.document.type', 'service_workflow_in_doctype_rel', 'workflow_id',
                                        'document_type_id', string='Required In Documents',
                                        domain="[('id','in',in_document_types)]")
    required_out_docs = fields.Many2many('ebs.document.type', 'service_workflow_out_doctype_rel', 'workflow_id',
                                         'document_type_id', string='Required Out Documents',
                                         domain="[('id','in',out_document_types)]")
    workflow_days_to_complete = fields.Float(string='Days to complete')
    is_activity_required = fields.Boolean('Is Activity Required')
    is_timesheet_required = fields.Boolean('Is Timesheet Required')
    required_payment = fields.Boolean('Is Payment Required')
    process_char = fields.Char('Process')
    output_char = fields.Char('Output')
    is_group = fields.Boolean(related='service_id.is_group')
    service_option_ids = fields.Many2many('ebs.service.option', string='Service Options', domain=_get_service_workflow)

    @api.onchange('service_id', 'required_in_docs', 'required_out_docs')
    def onchange_service_id(self):
        if self.service_id:
            in_document_type_ids = self.service_id.document_type_ids.filtered(lambda l: l.input).mapped(
                'document_type_id')
            out_document_type_ids = self.service_id.document_type_ids.filtered(lambda l: l.output).mapped(
                'document_type_id')
            return {'domain': {
                'required_in_docs': [('id', 'in', in_document_type_ids.ids)],
                'required_out_docs': [('id', 'in', out_document_type_ids.ids)]
            }
            }

    @api.onchange('name')
    def onchange_name(self):
        for rec in self:
            rec.process_char = rec.name

    @api.onchange('output')
    def onchange_output(self):
        for rec in self:
            rec.output_char = rec.output

    @api.onchange('stage_id')
    def stage_id_onchange(self):
        for rec in self:
            rec.activity_id = False
            if rec.stage_id:
                return {'domain': {
                    'activity_id': [('id', 'in', rec.stage_id.activity_ids.ids)],
                }}
            else:
                return {'domain': {
                    'activity_id': [(1, '=', 1)],
                }}

    def compute_document_types(self):
        for rec in self:
            in_document_type_ids = rec.service_id.document_type_ids.filtered(lambda l: l.input).mapped(
                'document_type_id')
            out_document_type_ids = rec.service_id.document_type_ids.filtered(lambda l: l.output).mapped(
                'document_type_id')
            rec.in_document_types = [(6, 0, in_document_type_ids.ids)]
            rec.out_document_types = [(6, 0, out_document_type_ids.ids)]

    @api.model
    def default_get(self, fields):
        res = super(ebsCrmWorkflow, self).default_get(fields)
        if self._context:
            context_keys = self._context.keys()
            next_sequence = 1
            if 'workflow_lines' in context_keys:
                if len(self._context.get('workflow_lines')) > 0:
                    next_sequence = len(self._context.get('workflow_lines')) + 1
        res.update({'sequence': next_sequence})
        return res

    @api.onchange('activity_id')
    def onchnage_stage(self):
        for rec in self:
            if rec.activity_id:
                rec.write({'required_in_docs': [(6, 0, rec.activity_id.in_documents.ids)],
                           'required_out_docs': [(6, 0, rec.activity_id.out_documents.ids)]
                           })
            else:
                rec.write({'required_in_docs': [(5, 0, 0)],
                           'required_out_docs': [(5, 0, 0)]
                           })


class ebsServiceDocumentTypes(models.Model):
    _name = 'ebs.service.document.type'
    _description = 'Ebs Service Document Type'

    document_type_id = fields.Many2one('ebs.document.type', 'Document Type')
    input = fields.Boolean('Input')
    output = fields.Boolean('Output')
    service = fields.Boolean(related='document_type_id.is_services', string="Related To Service")
    individual = fields.Boolean(related='document_type_id.is_individual', string="Related To Partner")
    service_id = fields.Many2one('ebs.crm.service', string='Service ID')


class ebsServiceDOption(models.Model):
    _name = 'ebs.service.option'
    _description = 'Ebs Service Option'
    _rec_name = 'display_name'

    name = fields.Selection([('new', 'New'), ('renew', 'Renew'), ('manage', 'Other')], string='Type')
    govt_fees = fields.Float(string='Govt. Fees')
    fusion_fees = fields.Float(string='Main Company Fees')
    govt_product_id = fields.Many2one('product.product', string='Govt Product')
    fusion_product_id = fields.Many2one('product.product', string='Fusion Product')
    service_id = fields.Many2one('ebs.crm.service')
    account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic Account')
    authority_id = fields.Many2one('ebs.crm.service.authority', related='service_id.authority_id',
                                   string='Authority/Ministry', store=True)
    is_group = fields.Boolean(related='service_id.is_group', string='Is Group')
    fme = fields.Boolean(related='service_id.fme', string='FME')
    fss = fields.Boolean(related='service_id.fss', string='FSS')
    fos = fields.Boolean(related='service_id.fos', string='FOS')
    service_order_type = fields.Selection(
        [('company', 'Company'), ('employee', 'Employee'), ('visitor', 'Visitor'), ('dependent', 'Dependent')]
        , string='Target Audience')
    company = fields.Boolean('Company')
    employee = fields.Boolean('Employee')
    visitor = fields.Boolean('Visitor')
    dependent = fields.Boolean('Dependent')
    duration = fields.Integer('Duration')
    duration_type = fields.Selection([('year', 'Year'), ('month', 'Month')], string='Duration Type', default='year')
    display_name = fields.Char('Name', compute='compute_display_name', store=True, readonly=False)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=1)

    @api.model
    def create(self, vals):
        service_id = self.env['ebs.crm.service'].search([('id', '=', vals.get('service_id'))])
        if service_id.company:
            if vals.get('service_order_type') in ['employee', 'visitor', 'dependent']:
                raise UserError('The target audience cannot be different from the target audience of the service')
        if not service_id.company:
            if vals.get('service_order_type') == 'company':
                raise UserError('The target audience cannot be different from the target audience of the service')
        return super(ebsServiceDOption, self).create(vals)

    def write(self, vals):
        service_id = self.service_id
        if service_id.company:
            if vals.get('service_order_type') in ['employee', 'visitor', 'dependent']:
                raise UserError('The target audience cannot be different from the target audience of the service')
        if not service_id.company:
            if vals.get('service_order_type') == 'company':
                raise UserError('The target audience cannot be different from the target audience of the service')
        return super(ebsServiceDOption, self).write(vals)

    @api.depends('name', 'duration', 'duration_type', 'service_order_type')
    def compute_display_name(self):
        for rec in self:
            if rec.name:
                rec.display_name = rec.name.capitalize()
                if rec.duration != 0 and rec.duration_type:
                    rec.display_name += " - " + str(rec.duration) + " " + rec.duration_type.capitalize()
                if rec.service_order_type == 'company':
                    rec.display_name += " - Company"
                if rec.service_order_type == 'employee':
                    rec.display_name += " - Employee"
                if rec.service_order_type == 'visitor':
                    rec.display_name += " - Visitor"
                if rec.service_order_type == 'dependent':
                    rec.display_name += " - Dependent"
            else:
                rec.display_name = ''


class ebsServiceFines(models.Model):
    _name = 'ebs.crm.service.fines'
    _description = 'Ebs CRM Service Fines'
    _rec_name = 'visa_type'

    document_type = fields.Many2one('ebs.document.type', string="Document Type")
    is_visa = fields.Boolean('Is Visa')
    visa_type = fields.Many2one('ebs.visa.type', string="Visa Type")
    fine = fields.Float(string='Fine')
    days_after_expiry = fields.Integer('Days After Expiry', required=1)
    fusion_product_id = fields.Many2one('product.product', string='Product')
    service_id = fields.Many2one('ebs.crm.service')

    @api.onchange('document_type')
    def onchange_document_type(self):
        if self.document_type.meta_data_template == 'Visa':
            self.is_visa = True
        else:
            self.is_visa = False
