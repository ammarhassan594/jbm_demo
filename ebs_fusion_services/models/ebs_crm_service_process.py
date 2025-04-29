from datetime import datetime, date, timedelta

from lxml import etree
from collections import defaultdict
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta


class ebsCrmOutDocuments(models.Model):
    _name = 'ebs.crm.proposal.out.documents'
    _description = 'EBS CRM Proposal Out Documents'
    _rec_name = 'name'

    service_process_id = fields.Many2one('ebs.crm.service.process', readonly=1)
    employee_id = fields.Many2one('hr.employee', related="service_process_id.employee_id", store=True)
    doc_type_id = fields.Many2one('ebs.document.type', string='Document Type', readonly=1)
    name = fields.Many2one('documents.document', string='Document')
    number = fields.Char(related='name.document_number', string='Document Number')

    @api.onchange('doc_type_id')
    def onchange_doc_type_id(self):
        doc_type = self.doc_type_id
        if doc_type:
            document = self.env['documents.document'].search(
                [('partner_id', '=', self.service_process_id.partner_id.id), ('document_type_id', '=', doc_type.id)])
            if len(document) == 1:
                self.name = document.id

    def preview_document(self):
        self.ensure_one()
        if self.name:
            action = {
                'type': "ir.actions.act_url",
                'target': "_blank",
                'url': '/documents/content/preview/%s' % self.name.id
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
                action['url'] = '/documents/content/%s' % self.name.id
            return action

    def upload_file(self):
        action = self.env.ref('ebs_fusion_documents.document_button_action').read()[0]
        context = {
            'default_service_process_id': self.service_process_id.id,
            'default_proposal_id': self.service_process_id.proposal_line_id.proposal_id.id,
            'default_document_type_id': self.doc_type_id.id,
            'default_employee_id': self.employee_id.id,
            'hide_field': 1,
        }

        action['context'] = context
        return action


class ebsCrmServiceProcess(models.Model):
    _name = 'ebs.crm.service.process'
    _description = 'EBS Service Order'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    def _default_currency_id(self):
        return self.env.user.company_id.currency_id.id

    def _set_default_option(self):
        domain = []
        if self.service_id:
            domain = [('service_id', '=', self.service_id), ('service_order_type', '=', self.service_order_type)]
        else:
            domain = [('id', 'in', [])]
        return domain

    name = fields.Char('Name', readonly=1, default='/')
    currency_id = fields.Many2one('res.currency', default=_default_currency_id)
    proposal_line_id = fields.Many2one('ebs.crm.proposal.line')
    pricelist_id = fields.Many2one('ebs.crm.pricelist', 'Pricelist')
    proposal_id = fields.Many2one('ebs.crm.proposal', string='Proposal', store=True)
    service_order_type = fields.Selection(
        [('company', 'Company'), ('employee', 'Employee'), ('visitor', 'Visitor'), ('dependent', 'Dependent')]
        , string='Target Audience', default='company')
    target_audience = fields.Selection([('company', 'Company'), ('person', 'Person')], default='company',
                                       string='Service Target Audience', compute='set_default_target_audience')
    partner_id = fields.Many2one('res.partner', string='Contact', required=False)
    client_id = fields.Many2one('res.partner', 'Client',
                                domain=['|', ('company_partner', '=', True), ('is_customer', '=', True),
                                        ('is_company', '=', True)])
    employee_id = fields.Many2one('hr.employee', 'Employee')
    employee_partner_id = fields.Many2one(related='employee_id.user_partner_id', string='Employee Partner')
    dependent_id = fields.Many2one('res.partner', string="Dependent")
    partner_type = fields.Selection(related='partner_id.company_type', string='Contact Type')
    partner_related_companies = fields.Many2many(related='partner_id.related_companies')
    pricelist_line_id = fields.Many2one('ebs.crm.pricelist.line')
    pricelist_category_id = fields.Many2one('ebs.crm.pricelist.category')
    service_id = fields.Many2one('ebs.crm.service', 'Service')
    service_code = fields.Char(related='service_id.service_id', string="Service ID")
    service_template_id = fields.Many2one('ebs.crm.service.template', 'Service Template')
    govt_fees = fields.Float(string='Govt. Fees', readonly=1)
    fusion_fees = fields.Float(string='Fusion. Fees', readonly=1)
    govt_product_id = fields.Many2one('product.product', string='Govt. Product')
    fusion_product_id = fields.Many2one('product.product', string='Fusion Product')
    service_type = fields.Selection([('individual', 'Individual'), ('corporate', 'Corporate')], string="Service Type")
    status = fields.Selection(
        [('draft', 'Draft'), ('ongoing', 'Active'), ('onhold', 'Pending'), ('completed', 'Closed'),
         ('cancelled', 'Cancelled')],
        string='Status', default='draft')
    start_date = fields.Date('Start Date', default=datetime.today())
    due_date = fields.Date('Due Date')

    invoice_line_id = fields.Many2one('account.move.line', 'Invoice Line', copy=False, readonly=True)
    end_date = fields.Date('End Date', readonly=1)
    is_invoiced = fields.Boolean('Is Invoiced?', compute='compute_invoiced', readonly=1)
    proposal_workflow_line_ids = fields.One2many('ebs.crm.proposal.workflow.line', 'service_process_id',
                                                 string='Workflow Lines', copy=True, ondelete='cascade')

    out_document_ids = fields.One2many('ebs.crm.proposal.out.documents', 'service_process_id', string='Out Documents',
                                       copy=True)
    in_document_ids = fields.One2many('ebs.crm.proposal.in.documents', 'service_process_id', string='In Documents',
                                      copy=True)
    additional_expenses = fields.One2many('ebs.crm.additional.expenses', 'service_process_id',
                                          string='Additional Expenses', copy=True)
    invoice_count = fields.Integer('Invoice Count', compute='_compute_invoice_count')
    payment_count = fields.Integer('Payment Count', compute='_compute_payment_count')
    service_order_date = fields.Date('Service Order Date', default=datetime.today())
    generated_from_portal = fields.Boolean('From Portal')
    completed = fields.Boolean('Completed')
    amount_total = fields.Float('Total Fees', compute='compute_total_fees')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    category_ids = fields.Many2many('ebs.crm.pricelist.category', 'CategoryIDs', compute='compute_category_ids')
    service_ids = fields.Many2many('ebs.crm.service', 'ServiceIDs', compute='compute_service_ids')
    is_individual = fields.Boolean('Individual')
    is_urgent = fields.Boolean('Urgent')
    urgent_text = fields.Char(default='Main Company Fees are doubled')
    comments = fields.Text(related='pricelist_line_id.comments')
    govt_invoiced = fields.Float('Govt. Invoiced')
    govt_payment = fields.Float('Govt. Payment')
    fusion_invoiced = fields.Float('Main Company Invoiced')
    fusion_payment = fields.Float('Main Company Payment')
    fusion_fees_net = fields.Float('Main Company Fees Net')
    discount = fields.Float('Discount')
    day_to_complete = fields.Float(string='Days to complete')
    actual_days_to_complete = fields.Integer(string='Actual days to complete',
                                             compute='compute_actual_days_to_complete')
    group_id = fields.Many2one('ebs.crm.service.groups', string="Service Group")
    parent_id = fields.Many2one('ebs.crm.service.process', 'Parent Service Order')
    option = fields.Selection([('new', 'New'), ('renew', 'Renew'), ('manage', 'Manage')], string="Option")
    option_id = fields.Many2one('ebs.service.option', string="Option")
    option_name = fields.Selection(related='option_id.name', string='Option Name')
    duration = fields.Selection([('1 year', '1 Year'), ('2 years', '2 Years'), ('3 years', '3 Years')],
                                string='Duration')

    sub_service_ids = fields.One2many('ebs.crm.service.process', 'parent_id', string="Sub Service Orders")
    sub_service_count = fields.Integer('Sub Service Count', compute='compute_sub_service_count')
    is_group_related = fields.Boolean(related="service_id.is_group")
    is_sub_service = fields.Boolean()
    labor_quota_id = fields.Many2one('ebs.labor.quota', string='Labor Quota')
    labor_quota_status = fields.Selection(
        [('under_process', 'Quota Under Process'), ('approved', 'Approved'), ('rejected', 'Rejected'),
         ('partially_approved', 'Partially Approved')], string='Labor Quota Status', default='under_process')
    is_labor_quota = fields.Boolean(related='service_id.labor_quota')
    labor_quota_line_ids = fields.One2many('ebs.crm.labor.quota', 'service_order_id', string='Labor Quota')
    manage_labor_quota_line_ids = fields.One2many('manage.labor.quota.line', 'service_order_id',
                                                  string='Labor Quota Lines')
    labor_quota_app_no = fields.Char("Application Number")
    labor_quota_app_date = fields.Date("Application Date")
    labor_quota_expiry_date = fields.Date("Expiry Date", related='labor_quota_id.expiry_date')
    request_no = fields.Char("Request No.")
    request_date = fields.Date("Request Date")
    request_type = fields.Selection([('new', 'New'),
                                     ('renew', 'Renew'),
                                     ('manage', 'Other'),
                                     ('release', 'Release'),
                                     ], string="Request Type")
    requeste_line_ids = fields.One2many('labor.quota.request.line', 'service_order_id', "Request Lines")
    lq_new_expiry_date = fields.Date("New Expiry Date")
    new_labor_quota_id = fields.Many2one('ebs.labor.quota', string='Labor Quota')
    contract_id = fields.Many2one('ebs.crm.proposal', "Contract No.")
    fos_employee_id = fields.Many2one('ebs.crm.proposal.employee.line')
    is_extra_order = fields.Boolean('Extra Order', default=False)
    workflow_count = fields.Integer('Workflows', compute='compute_workflow_count')
    assigned_user_id = fields.Many2one(comodel_name='res.users', string='Responsible User',
                                       default=lambda self: self.env.user,
                                       domain="[('share','=',False)]")
    batch_order_id = fields.Many2one('ebs.batch.service.order', 'Batch Order')
    description = fields.Text('Description')
    workflow_payment_ids = fields.One2many(comodel_name='ebs.workflow.payment', inverse_name='service_order_id',
                                           string='Payments', compute='compute_workflow_payment_ids')

    def compute_workflow_payment_ids(self):
        for rec in self:
            rec.workflow_payment_ids = rec.proposal_workflow_line_ids.workflow_payment_ids

    def get_service_order_chart_data(self, service_order_ids=[]):
        service_order_ids = self.sudo().browse(service_order_ids)
        label = []
        data = []
        for key, value in dict(self._fields['status'].selection).items():
            label.append(value)
            data.append(len(service_order_ids.filtered(lambda o: o.status == key).ids))
        return {
            'label': label,
            'data': data
        }

    def get_service_order_chart_data_of_target_audience(self, target_audience=[]):
        target_audience = self.sudo().browse(target_audience)
        label = []
        data = []
        for key, value in dict(self._fields['service_order_type'].selection).items():
            label.append(value)
            data.append(len(target_audience.filtered(lambda o: o.service_order_type == key).ids))
        return {
            'label': label,
            'data': data
        }

    def get_service_order_chart_data(self, service_order_ids=[]):
        service_order_ids = self.sudo().browse(service_order_ids)
        label = []
        data = []
        for key, value in dict(self._fields['status'].selection).items():
            label.append(value)
            data.append(len(service_order_ids.filtered(lambda o: o.status == key).ids))
        return {
            'label': label,
            'data': data
        }

    def unlink(self):
        for rec in self:
            if rec.status != 'draft':
                raise UserError(_('Only Draft Service Order Can Be Delete.'))
            if any(line.status != 'draft' for line in rec.proposal_workflow_line_ids):
                raise UserError(_('Only Draft Workflow Can Be Delete.'))
        return super(ebsCrmServiceProcess, self).unlink()

    def assign_user(self):
        action = self.env.ref('ebs_fusion_services.assign_workflows_wizard_action').read()[0]
        action['context'] = {'default_workflow_ids': [(6, 0, self.proposal_workflow_line_ids.ids)]}
        return action

    @api.onchange('service_id', 'company_id', 'client_id')
    def onchange_service_id(self):

        if self.service_id:
            option_ids = self.env['ebs.service.option'].search([
                ('service_id', '=', self.service_id.id), ('company_id', '=', self.company_id.id)
            ])
            if option_ids:
                self.option_id = option_ids.ids[0]
            else:
                self.option_id = False
        else:
            self.option_id = False

        additional_expenses_lst = []
        for rec in self:
            rec.additional_expenses = [(5, 0, 0)]
            if rec.service_id.fines_applicable and rec.service_id.service_fine_ids:
                for fine_line in rec.service_id.service_fine_ids:
                    docs = False
                    if rec.service_order_type == 'employee':
                        contact = rec.employee_id
                    else:
                        contact = rec.partner_id
                    if fine_line.document_type.meta_data_template == 'Visa' and fine_line.visa_type:
                        docs = contact.document_o2m.filtered(
                            lambda x: x.expiry_date and x.visa_type_id == fine_line.visa_type and x.status == 'expired')
                    else:
                        docs = contact.document_o2m.filtered(
                            lambda
                                x: x.expiry_date and x.document_type_name == fine_line.document_type.meta_data_template and x.status == 'expired')
                    for doc in docs:
                        duration_date = doc.expiry_date - date.today()
                        if duration_date.days < 0 and abs(duration_date.days) > fine_line.days_after_expiry:
                            additional_expenses_lst.append((0, 0, {
                                'product_id': fine_line.fusion_product_id.product_tmpl_id.id,
                                'amount': fine_line.fine * (abs(duration_date.days) - fine_line.days_after_expiry),
                                'type': 'fine',
                                'expense_service_id': rec.service_id.id}))

                if additional_expenses_lst:
                    rec.write({'additional_expenses': additional_expenses_lst})

    @api.onchange('service_order_type')
    def get_service_option_domain(self):
        type_domain = []
        service_domain = []
        if self.service_order_type == 'company':
            self.partner_id = self.client_id.id
            type_domain.append(('service_order_type', '=', 'company'))
            service_domain.append(('target_audience', '=', 'company'))
        elif self.service_order_type == 'employee':
            self.partner_id = self.employee_id.user_partner_id.id
            type_domain.append(('service_order_type', '=', 'employee'))
            service_domain.append(('target_audience', '=', 'person'))
        elif self.service_order_type == 'visitor':
            type_domain.append(('service_order_type', '=', 'visitor'))
            service_domain.append(('target_audience', '=', 'person'))
        elif self.service_order_type == 'dependent':
            self.partner_id = self.dependent_id.id
            type_domain.append(('service_order_type', '=', 'dependent'))
            service_domain.append(('target_audience', '=', 'person'))
        return {'domain': {'service_id': service_domain}}

    @api.depends('service_order_type')
    def set_default_target_audience(self):
        if self.service_order_type == 'company':
            self.target_audience = 'company'
        else:
            self.target_audience = 'person'

    @api.onchange('client_id')
    def onchange_client_id(self):
        for rec in self:
            if rec.service_order_type == 'company':
                rec.partner_id = rec.client_id.id

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        for rec in self:
            if rec.service_order_type == 'employee':
                rec.partner_id = rec.employee_id.user_partner_id.id

    @api.onchange('dependent_id')
    def onchange_dependent_id(self):
        for rec in self:
            if rec.service_order_type == 'dependent':
                rec.partner_id = rec.dependent_id.id

    @api.depends('proposal_workflow_line_ids')
    def compute_workflow_count(self):
        for record in self:
            record.workflow_count = len(record.proposal_workflow_line_ids.ids)

    def get_workflows(self):
        sub_service_order = self.env['ebs.crm.service.process'].search(
            ['|', ('parent_id', '=', self.id), ('id', '=', self.id)]).ids
        workflow_ids = self.env['ebs.crm.proposal.workflow.line'].search(
            [('service_process_id', '=', sub_service_order)])
        action = self.env.ref('ebs_fusion_services.ebs_fusion_crm_proposal_workflow_action').read([])[0]
        action['domain'] = [('id', 'in', workflow_ids.ids)]
        action['views'] = [(self.env.ref('ebs_fusion_services.view_ebs_crm_proposal_workflow_tree').id, 'tree'),
                           (self.env.ref('ebs_fusion_services.view_ebs_crm_proposal_workflow_form').id, 'form')]
        action['view_mode'] = 'tree'
        return action

    def add_requested_lines(self):
        self.ensure_one()
        approved_lines = []
        self.labor_quota_line_ids = [(5, 0, 0)]
        for line in self.requeste_line_ids:
            approved_lines.append((0, 0, {'nationality_id': line.nationality_id.id,
                                          'job_id': line.job_id.id,
                                          'gender': line.gender,
                                          'qty': line.qty}))
        self.write({'labor_quota_line_ids': approved_lines})

    @api.onchange('discount', 'fusion_fees')
    def onchange_fusion_fee_discount(self):
        for rec in self:
            rec.fusion_fees_net = rec.fusion_fees - (rec.discount / 100) * rec.fusion_fees

    @api.onchange('lq_new_expiry_date')
    def onchange_lq_new_expiry_date(self):
        for rec in self:
            if rec.lq_new_expiry_date and rec.lq_new_expiry_date <= date.today():
                raise ValidationError('Please Select Future Date For Expiry Date.')

    @api.onchange('labor_quota_app_date')
    def onchange_labor_quota_app_date(self):
        for rec in self:
            if rec.labor_quota_app_date and rec.labor_quota_app_date < date.today():
                raise ValidationError('Application Date Could Not Be In The Past.')

    @api.constrains('labor_quota_id')
    def check_labor_quota_status(self):
        for rec in self:
            if rec.labor_quota_id and rec.labor_quota_id.status == 'rejected':
                raise UserError(_('Please Change Selected Labor Quota status From Rejected Or Change Labor Quota.'))

    @api.onchange('labor_quota_id')
    def onchange_labor_quota_id(self):
        for rec in self:
            rec.labor_quota_status = rec.labor_quota_id.status
            if rec.option_name == 'manage':
                rec.manage_labor_quota_line_ids = [(5, 0, 0)]

                manage_labor_quota_line_ids = []
                for line in rec.labor_quota_id.labor_quota_line_id:
                    vals = {
                        'labor_quota_line_id': line.id,
                        'ref_no': line.ref_no,
                        'nationality_id': line.nationality_id.id,
                        'job_id': line.job_id.id,
                        'gender': line.gender,
                        'qty': line.qty,
                    }
                    manage_labor_quota_line_ids.append((0, 0, vals))
                rec.write({'manage_labor_quota_line_ids': manage_labor_quota_line_ids})
            return {'domain': {
                'labor_quota_subline_id': [('line_id', '=', rec.labor_quota_id.labor_quota_line_id.ids)]}}

    @api.onchange('option_id', 'is_labor_quota')
    def onchange_option_labor_quota(self):
        for rec in self:
            rec.labor_quota_id = False
            if rec.is_labor_quota and rec.option_id.name == 'new':
                rec.manage_labor_quota_line_ids = False
            if rec.is_labor_quota and rec.option_id.name == 'renew':
                rec.labor_quota_line_ids = False
                rec.manage_labor_quota_line_ids = False
                domain = {'domain': {
                    'labor_quota_id': [('partner_id', '=', rec.client_id.id), ('expiry_date', '<=', date.today())]}}
            else:
                rec.labor_quota_line_ids = False
                domain = {'domain': {
                    'labor_quota_id': [('partner_id', '=', rec.client_id.id), ('expiry_date', '>', date.today())]}}
            return domain

    @api.onchange('status')
    def onchange_status(self):
        for rec in self:
            flag = False
            blank = False
            subservice = False
            if rec.status == 'ongoing':
                for doc in rec.in_document_ids:
                    if not doc.name:
                        blank = True
                        break
                if blank:
                    raise UserError(
                        'You cannot mark this process active as all in documents have not been updated yet.')
            if rec.status == 'completed':
                rec.write({'end_date': datetime.today()})
                for doc in rec.out_document_ids:
                    if not doc.name:
                        blank = True
                        break
                for record in rec.proposal_workflow_line_ids:
                    if record.status != 'completed':
                        flag = True
                        break
                for sub in rec.sub_service_ids:
                    if sub.status != 'completed':
                        subservice = True
                        break
                if flag:
                    raise UserError(
                        'You cannot mark this process completed as all workflows have not been completed yet.')
                if blank:
                    raise UserError(
                        'You cannot mark this process completed as all out documents have not been updated yet.')
                if subservice:
                    raise UserError(
                        'You cannot mark this process completed as all subservices have not been completed yet.')
            else:
                rec.write({'completed': False})
            if rec.labor_quota_status != 'rejected':
                if rec.status == 'completed' and rec.is_labor_quota and rec.option_name == 'renew':
                    if rec.labor_quota_status == 'partially_approved':
                        raise UserError(_('Can Not Select Partially Approved Status For Renew Option.'))
                    if rec.labor_quota_status == 'approved':
                        expiry_date = rec.labor_quota_id.expiry_date + relativedelta(months=+6)
                        rec.labor_quota_id.write({'expiry_date': rec.lq_new_expiry_date})
                        rec.write({'labor_quota_status': 'approved'})
                        update_line = rec.labor_quota_id.labor_quota_line_id.filtered(lambda
                                                                                          o: o.nationality_id.id == rec.employee_id.nationality_id.id and o.job_id.id == rec.employee_id.job_id.id and o.gender == rec.employee_id.gender)
                        employee_line = update_line.subline_ids.filtered(
                            lambda o: o.employee_id.id == rec.employee_id.id)
                        if update_line and not employee_line:
                            available_line = update_line.subline_ids.filtered(lambda o: o.status == 'available')
                            if available_line:
                                available_line[0].write({'status': 'booked',
                                                         'employee_id': rec.employee_id.id})
                            if not available_line and update_line.qty_remaining > 0:
                                create_line = {'status': 'booked',
                                               'employee_id': rec.employee_id.id}
                                update_line.write({'subline_ids': [(0, 0, create_line)]})

                if rec.status == 'completed' and rec.manage_labor_quota_line_ids and rec.option_id.name == 'manage' and rec.labor_quota_status == 'approved':
                    if rec.request_type == 'release':
                        for subline in rec.manage_labor_quota_line_ids.filtered(lambda o: o.is_approved == True).mapped(
                                'labor_quota_subline_id'):
                            subline.write({'status': 'available', 'employee_id': False})
                del_line = []
                for line in rec.labor_quota_id.labor_quota_line_id:
                    if line not in rec.manage_labor_quota_line_ids.mapped('labor_quota_line_id'):
                        del_line.append(line.id)
                rec.labor_quota_id.write({'labor_quota_line_id': [(3, line_id) for line_id in del_line]})

                for line in rec.manage_labor_quota_line_ids:
                    if not line.labor_quota_line_id:
                        val = {
                            'labor_id': rec.labor_quota_id.id,
                            'ref_no': line.ref_no,
                            'nationality_id': line.nationality_id.id,
                            'job_id': line.job_id.id,
                            'gender': line.gender,
                            'qty': line.qty
                        }
                        if line.nationality_id.id == rec.employee_id.nationality_id.id and line.job_id.id == rec.employee_id.job_id.id and line.gender == rec.employee_id.gender:
                            subline = {'status': 'booked',
                                       'employee_id': rec.employee_id.id}
                            val.update({'subline_ids': [0, 0, subline]})
                        self.env['labor.quota.line'].create(val)
                    else:
                        val = {}
                        if line.ref_no != line.labor_quota_line_id.ref_no:
                            val.update({'ref_no': line.ref_no})
                        if line.nationality_id.id != line.labor_quota_line_id.nationality_id.id:
                            val.update({'nationality_id': line.nationality_id.id})
                        if line.job_id.id != line.labor_quota_line_id.job_id.id:
                            val.update({'job_id': line.job_id.id})
                        if line.gender != line.labor_quota_line_id.gender:
                            val.update({'gender': line.gender})
                        if line.qty != line.labor_quota_line_id.qty:
                            val.update({'qty': line.qty})
                        if line.nationality_id.id == rec.employee_id.nationality_id.id and line.job_id.id == rec.employee_id.job_id.id and line.gender == rec.employee_id.gender:
                            employee_line = line.labor_quota_line_id.subline_ids.filtered(
                                lambda o: o.employee_id.id == rec.employee_id.id)
                            if not employee_line:
                                available_line = line.labor_quota_line_id.subline_ids.filtered(
                                    lambda o: o.status == 'available')
                                if available_line:
                                    val.update({'subline_ids': [(1, available_line[0].id, {'status': 'booked',
                                                                                           'employee_id': rec.employee_id.id})]})
                                if not available_line and (line.qty - line.labor_quota_line_id.qty_used) > 0:
                                    create_line = {'status': 'booked',
                                                   'employee_id': rec.employee_id.id}
                                    val.update({'subline_ids': [(0, 0, create_line)]})

                        line.labor_quota_line_id.write(val)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(ebsCrmServiceProcess, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                                submenu=submenu)
        user = self.env['res.users'].browse(self.env.uid)
        if view_type == 'form':
            doc = etree.XML(res['arch'])
            node = doc.xpath("//field[@name='status']")[0]
            if user.has_group('ebs_fusion_services.group_services_manager'):
                node.set('clickable', '1')
            else:
                node.set('clickable', '0')
            res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

    def action_start(self):
        for rec in self:
            rec.status = 'ongoing'

            workflow_id = rec.proposal_workflow_line_ids and rec.proposal_workflow_line_ids[0]
            recipient_ids = []
            notification_ids = []
            if workflow_id:
                activity_type_id = self.env['mail.activity.type'].search([('name', '=', 'To Do')])
                subject = "The workflow '" + workflow_id.name + "' has started"
                if workflow_id.assigned_to and workflow_id.assigned_to.partner_id:
                    recipient_ids.append((4, workflow_id.assigned_to.partner_id.id))
                    notification_ids.append((0, 0, {
                        'res_partner_id': workflow_id.assigned_to.partner_id.id,
                        'notification_type': 'inbox'}))
                    vals = {
                        'activity_type_id': activity_type_id.id,
                        'res_model_id': self.env['ir.model']._get('res.partner').id,
                        'res_id': workflow_id.assigned_to.partner_id.id,
                        'note': subject,
                    }
                    self.env['mail.activity'].create(vals)

                if recipient_ids:
                    mail_server_id = self.env['ir.mail_server'].sudo().search([], order='sequence asc', limit=1)
                    mail = self.env['mail.mail'].sudo().create({
                        'subject': subject,
                        'body_html': '<p>The workflow <b>%s</b> of service <b>%s</b> has been started.</p>' % (
                            workflow_id.name, workflow_id.service_process_id.name),
                        'recipient_ids': recipient_ids,
                        'mail_server_id': mail_server_id and mail_server_id.id,
                    })
                    mail.send()
                if notification_ids:
                    self.message_post(
                        subject=subject,
                        body='<p>The workflow <b>%s</b> of service <b>%s</b> has been started.</p>' % (
                            workflow_id.name, workflow_id.service_process_id.name),
                        message_type='notification',
                        subtype_xmlid='mail.mt_comment', author_id=self.env.user.partner_id.id,
                        notification_ids=notification_ids)

    @api.depends('start_date', 'end_date')
    def compute_actual_days_to_complete(self):
        for rec in self:
            if rec.end_date and rec.start_date:
                rec.actual_days_to_complete = int((rec.end_date - rec.start_date).days)
            else:
                rec.actual_days_to_complete = 0

    @api.depends('sub_service_ids')
    def compute_sub_service_count(self):
        for rec in self:
            if rec.sub_service_ids:
                rec.sub_service_count = len(rec.sub_service_ids)
            else:
                rec.sub_service_count = 0

    def check_existing_line(self, subline, labor_quota):
        line = labor_quota.labor_quota_line_id.filtered(lambda
                                                            o: o.nationality_id.id == subline.nationality_id.id and o.job_id.id == subline.job_id.id and o.gender == subline.gender)
        return line

    def check_subline_changes(self, subline):
        if subline.nationality_id.id == subline.labor_quota_subline_id.nationality_id.id and subline.job_id.id == subline.labor_quota_subline_id.job_id.id and subline.gender == subline.labor_quota_subline_id.gender:
            return False
        else:
            return True

    def _get_sequence(self):
        ''' Return the sequence to be used during the post of the current move.
        :return: An ir.sequence record or False.
        '''
        self.ensure_one()

        service = self.service_id
        if service and service.sequence_ids:
            return service.sequence_ids.filtered(lambda l: l.company_id == self.company_id)

    def write(self, vals):
        if 'assigned_user_id' in vals and vals['assigned_user_id']:
            user_id = self.env['res.users'].browse([vals['assigned_user_id']])
            mail_server_id = self.env['ir.mail_server'].sudo().search([], order='sequence asc', limit=1)
            mail = self.env['mail.mail'].sudo().create({
                'body_html': '<p>The Service Order <b>%s</b> has been assigned to you.</p>' % self.name,
                'recipient_ids': [(4, user_id.partner_id.id)],
                'mail_server_id': mail_server_id and mail_server_id.id,
            })
            mail.send()
            notification_ids = [(0, 0, {
                'res_partner_id': user_id.partner_id.id,
                'notification_type': 'inbox'})]
            self.message_post(
                body='<p>The Service Order <b>%s</b> has been assigned to you.</p>' % self.name,
                message_type='notification',
                subtype_xmlid='mail.mt_comment', author_id=self.env.user.partner_id.id,
                notification_ids=notification_ids)
        template_obj = self.env['mail.mail']
        if 'status' in vals:
            receivers = []
            if self.partner_related_companies:
                for partner in self.partner_related_companies:
                    receivers.append((4, partner.id))
            else:
                receivers.append((4, self.partner_id.id or self.client_id.id))
            if vals['status'] == 'completed':
                if self.labor_quota_line_ids and self.option_name == 'new' and self.labor_quota_status != 'rejected':
                    if all(line.is_approved != True for line in self.labor_quota_line_ids):
                        raise UserError(
                            'No Labor Quota Line Is Selected For Approval. Please Change Labor Quota Status Or Update Labor Quota Lines.')
                    labor_quota_vals = {}
                    labor_quota_line_id = []
                    for labor_quota_line in self.labor_quota_line_ids.filtered(lambda o: o.is_approved == True):
                        val = {'ref_no': labor_quota_line.ref_no,
                               'nationality_id': labor_quota_line.nationality_id.id,
                               'job_id': labor_quota_line.job_id.id,
                               'gender': labor_quota_line.gender,
                               'qty': labor_quota_line.qty,
                               }

                        employee_line = {'status': 'booked',
                                         'employee_id': self.employee_id.id}
                        if labor_quota_line.nationality_id.id == self.employee_id.nationality_id.id and labor_quota_line.job_id.id == self.employee_id.job_id.id and labor_quota_line.gender == self.employee_id.gender:
                            val.update({'subline_ids': [(0, 0, employee_line)]})
                        if self.contract_id:
                            contract_line = {'status': 'booked',
                                             'contract_id': self.contract_id.id}
                            val.update({'subline_ids': [(0, 0, contract_line)]})
                        labor_quota_line_id.append((0, 0, val))
                    labor_quota_vals.update({'app_date': self.labor_quota_app_date,
                                             'partner_id': self.client_id.id,
                                             'app_no': self.labor_quota_app_no,
                                             'expiry_date': self.lq_new_expiry_date,
                                             'labor_quota_line_id': labor_quota_line_id,
                                             'service_order_id': self.id})
                    if len(self.labor_quota_line_ids.filtered(lambda o: o.is_approved == True)) != len(
                            self.labor_quota_line_ids):
                        labor_quota_vals.update({'status': 'partially_approved'})
                        vals.update({'labor_quota_status': 'partially_approved'})
                    if all(line.is_approved == True for line in self.labor_quota_line_ids):
                        labor_quota_vals.update({'status': 'approved'})
                        vals.update({'labor_quota_status': 'approved'})
                    labor_quota = self.env['ebs.labor.quota'].create(labor_quota_vals)
                    if self.fos_employee_id:
                        self.fos_employee_id.write({'labor_quota_id': labor_quota.id})
                    vals.update({'new_labor_quota_id': labor_quota.id})
                if self.option_name == 'new' and self.labor_quota_status == 'rejected':
                    labor_quota_vals = {}
                    labor_quota_line_id = []
                    for labor_quota_line in self.requeste_line_ids:
                        val = {'nationality_id': labor_quota_line.nationality_id.id,
                               'job_id': labor_quota_line.job_id.id,
                               'gender': labor_quota_line.gender,
                               'qty': labor_quota_line.qty,
                               }
                        labor_quota_line_id.append((0, 0, val))
                    labor_quota_vals.update({'app_date': self.request_date,
                                             'partner_id': self.client_id.id,
                                             'app_no': self.request_no,
                                             'labor_quota_line_id': labor_quota_line_id,
                                             'service_order_id': self.id})
                    labor_quota_vals.update({'status': 'rejected'})
                    labor_quota = self.env['ebs.labor.quota'].create(labor_quota_vals)
                    if self.fos_employee_id:
                        self.fos_employee_id.write({'labor_quota_id': labor_quota.id})
                    vals.update({'new_labor_quota_id': labor_quota.id})

                if self.manage_labor_quota_line_ids and self.option_name == 'manage' and self.labor_quota_status == 'approved':
                    if all(line.is_approved != True for line in self.manage_labor_quota_line_ids):
                        raise UserError(
                            'No Labor Quota Line Is Selected For Approval. Please Change Labor Quota Status Or Update Labor Quota Lines.')
                    if self.request_type == 'release':
                        for subline in self.manage_labor_quota_line_ids.filtered(
                                lambda o: o.is_approved == True).mapped('labor_quota_subline_id'):
                            subline.write({'status': 'available', 'employee_id': False})
                        if any(line.is_approved != True for line in self.manage_labor_quota_line_ids):
                            self.write({'labor_quota_status': 'partially_approved'})
                    if self.request_type == 'manage':
                        for subline in self.manage_labor_quota_line_ids.filtered(lambda o: o.is_approved == True):
                            if self.check_subline_changes(subline):
                                line = self.check_existing_line(subline, self.labor_quota_id)
                                subline.labor_quota_subline_id.write({'status': 'updated'})
                                if self.contract_id:
                                    subline.labor_quota_subline_id.write({'contract_id': self.contract_id.id})
                                subline_value = {}
                                subline_value.update({'status': 'available'})
                                if self.contract_id:
                                    subline_value.update({'contract_id': self.contract_id.id,
                                                          'status': 'booked'})
                                if line:
                                    line[0].write({'subline_ids': [(0, 0, subline_value)]})
                                else:
                                    line_vals = {
                                        'nationality_id': subline.nationality_id.id,
                                        'job_id': subline.job_id.id,
                                        'gender': subline.gender,
                                        'qty': 1,
                                        'subline_ids': [(0, 0, subline_value)]
                                    }
                                    self.labor_quota_id.write({'labor_quota_line_id': [(0, 0, line_vals)]})
                        if any(line.is_approved != True for line in self.manage_labor_quota_line_ids):
                            self.write({'labor_quota_status': 'partially_approved'})

                vals['end_date'] = datetime.today()
                recipient_ids = [(4, self.env.user.id)]
                if self.partner_id:
                    recipient_ids.append((4, self.partner_id.id), )
                template_data = {
                    'subject': 'Your Service Order (Ref %s) has been marked as Completed' % (self.name),
                    'body_html': """
                                        <p>Hello %s,<p>
                                        Your service order <b>%s</b>'s status has been marked as completed. </br>
                                        Please download your documents from the portal. <br/><br/>

                                        Thank you,
                                        <br/>
                                        --
                                        Administrator""" % (self.partner_id.name, self.name),
                    'email_from': self.env.company.email,
                    'recipient_ids': recipient_ids,
                    'record_name': self.name,
                }
                template_id = template_obj.create(template_data)
                template_obj.send(template_id)
            if vals['status'] == 'ongoing':
                template_data = {
                    'subject': 'Your Service Order (Ref %s) has been marked as Ongoing' % (self.name),
                    'body_html': """
                        <p>Hello %s,<p>
                        Your service order <b>%s</b>'s status has been marked as ongoing. </br>

                        Thank you,
                        <br/>
                        --
                        Administrator""" % (self.partner_id.name, self.name),
                    'email_from': self.env.company.email,
                    'recipient_ids': receivers,
                    'record_name': self.name,
                }
                template_id = template_obj.create(template_data)
                template_obj.send(template_id)
        return super(ebsCrmServiceProcess, self).write(vals)

    @api.model
    def create(self, vals):
        if 'proposal_line_id' in vals:
            proposal_line_id = self.env['ebs.crm.proposal.line'].browse([vals.get('proposal_line_id')])
            vals['proposal_id'] = proposal_line_id.proposal_id.id
            vals['partner_id'] = proposal_line_id.proposal_id.contact_id.id
            vals['govt_fees'] = proposal_line_id.govt_fees
            if 'fusion_fees' not in vals:
                vals['fusion_fees'] = proposal_line_id.fusion_fees
        res = super(ebsCrmServiceProcess, self).create(vals)
        sequence = res._get_sequence()
        if not sequence:
            raise UserError(_('Please define a sequence on your service or dependent services for this company.'))

        # Consume a new number.
        res.name = sequence.next_by_id()
        if res.is_group_related:
            # Group service order - Creating sub service orders
            counter = 1
            for service in res.service_id.dependent_services_ids:
                option = service.service.service_option_ids.filtered(lambda l: l.id == res.option_id.id)
                create_sub_vals = {
                    'name': str(res.name) + "-{0}".format(counter),
                    'service_id': service.service.id,
                    'parent_id': res.id,
                    'partner_id': res.partner_id.id,
                    'proposal_id': res.proposal_id.id,
                    'client_id': res.client_id.id,
                    'is_sub_service': True,
                    'option_id': option.id,
                    'govt_fees': option.govt_fees,
                    'fusion_fees': option.fusion_fees,
                    'service_order_type': res.service_order_type,

                }
                self.env['ebs.crm.service.process'].create(create_sub_vals)
                counter += 1

        if res.generated_from_portal:
            users = self.env['res.users'].sudo().search([])
            partner_ids = []
            mail_server_id = self.env['ir.mail_server'].sudo().search([], order='sequence asc', limit=1)
            for user in users:
                if user.has_group('ebs_fusion_services.group_services_manager'):
                    partner_ids.append(user.partner_id.id)
            notification_ids = []
            for partner in partner_ids:
                notification_ids.append((0, 0, {
                    'res_partner_id': partner,
                    'notification_type': 'inbox'}))
            res.message_post(
                body='A new service order has been created %s for contact %s' % (res.name, res.partner_id.name),
                message_type='notification',
                subtype_xmlid='mail.mt_comment', author_id=self.env.user.partner_id.id,
                notification_ids=notification_ids)
        return res

    def create_multipart_invoices(self):
        additional = 0
        additional_invoiced = 0
        for add_exp in self.additional_expenses:
            if not add_exp.is_invoiced:
                additional += add_exp.amount
                additional_invoiced += add_exp.amount_invoiced
        remaining_govt = self.govt_fees - self.govt_invoiced
        remaining_fusion = self.fusion_fees - self.fusion_invoiced
        remaining_additional = additional - additional_invoiced
        if remaining_govt == 0 and remaining_fusion == 0 and remaining_additional == 0:
            raise UserError("There is no remaining payment left to invoice. All fees have already been invoiced.")
        else:
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'ebs.advance.payment.inv',
                'target': 'new',
            }

    def create_multipart_proforma_invoices(self):

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'ebs.advance.payment.inv',
            'target': 'new',

        }

    def compute_invoiced(self):
        for rec in self:
            if rec.is_group_related:
                rec.is_invoiced = True
                return
            remaining_govt = rec.govt_fees - rec.govt_invoiced
            remaining_fusion = rec.fusion_fees - rec.fusion_invoiced
            flag = True
            for add in rec.additional_expenses:
                if not add.is_invoiced:
                    flag = False
                    break
            if flag and remaining_fusion == 0 and remaining_govt == 0:
                rec.is_invoiced = True
            else:
                rec.is_invoiced = False

    def generate_invoice(self, govt=None, fusion=None, additional=None, discount=None, analytic_acc=None,
                         invoice_date=None):
        if self.service_order_type in ['company', 'employee', 'dependent']:
            partner_invoice = self.client_id
        else:
            partner_invoice = self.partner_id

        if not partner_invoice:
            raise UserError(_('You have to select an invoice address in the service form.'))
        company = self.env.user.company_id

        journal = self.env['account.move'].sudo().with_context(force_company=company.id,
                                                               type='out_invoice')._get_default_journal()
        if not journal:
            raise UserError(_('Please define an accounting sales journal for the company %s (%s).') % (
                self.company_id.name, self.company_id.id))
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': partner_invoice.id,
            'invoice_origin': self.name,
            'service_process_id': self.id,
            'invoice_line_ids': [],
            'invoice_date': invoice_date
        }
        invoice_line_vals = self.get_invoice_line_vals(govt, fusion, additional, discount, analytic_acc, invoice_date)
        invoice_vals['invoice_line_ids'] = invoice_line_vals

        if not len(invoice_vals['invoice_line_ids']) == 0:
            self.env['account.move'].with_context(default_move_type='out_invoice').sudo().create(invoice_vals)
        else:
            raise UserError(_('No invoiceable lines remaining'))

    def get_invoice_line_vals(self, govt=None, fusion=None, additional=None, discount=None, analytic_acc=None,
                              invoice_date=None):
        invoice_lines = []
        govt_amount = 0
        fusion_amount = 0
        if govt >= 0:
            govt_amount = govt - self.govt_invoiced
        else:
            govt_amount = self.govt_fees - self.govt_invoiced
        if fusion >= 0:
            fusion_amount = fusion - self.fusion_invoiced
        else:
            fusion_amount = self.fusion_fees - self.fusion_invoiced
        service_name = self.service_id.name
        if govt_amount > 0:
            if not self.option_id.govt_product_id:
                raise UserError('Please Select Govt. Product')
            product_id = self.option_id.govt_product_id
            description = product_id and product_id.name + " - " + service_name
            if self.service_order_type == 'employee' and self.employee_id:
                description += ' - ' + self.employee_id.name
            elif self.service_order_type == 'dependent' and self.dependent_id:
                description += ' - ' + self.dependent_id.name
            account = self.option_id.govt_product_id.product_tmpl_id._get_product_accounts()['income']
            if not account:
                raise UserError(_('No account defined for product "%s".') % product_id.name)
            invoice_line_vals = {
                'name': description,
                'account_id': account.id,
                'analytic_account_id': self.option_id.account_id.id if self.option_id.account_id else analytic_acc.get(
                    'govt_acc'),
                'quantity': 1,
                'price_unit': govt_amount,
                'product_id': product_id[0].id,
                'govt': True,
                'service_process_id': self.id,
            }

            balance = -(govt_amount)
            invoice_line_vals.update({
                'debit': balance > 0.0 and balance or 0.0,
                'credit': balance < 0.0 and -balance or 0.0,
            })
            invoice_lines.append((0, 0, invoice_line_vals))

        if fusion_amount > 0:
            if not self.option_id.fusion_product_id:
                raise UserError('Please Select Main Company  Product')
            product_id = self.option_id.fusion_product_id
            description = product_id and product_id.name + " - " + service_name
            if self.service_order_type == 'employee' and self.employee_id:
                description += ' - ' + self.employee_id.name
            elif self.service_order_type == 'dependent' and self.dependent_id:
                description += ' - ' + self.dependent_id.name
            account = self.option_id.fusion_product_id.product_tmpl_id._get_product_accounts()['income']
            if not account:
                raise UserError(_('No account defined for product "%s".') % product_id.name)
            invoice_line_vals = {
                'name': description,
                'account_id': account.id,
                'analytic_account_id': self.option_id.account_id.id if self.option_id.account_id else analytic_acc.get(
                    'fusion_acc'),
                'quantity': 1,
                'price_unit': fusion_amount,
                'product_id': product_id[0].id,
                'service_process_id': self.id,
                'fusion': True,
            }

            balance = -(fusion_amount)
            invoice_line_vals.update({
                'debit': balance > 0.0 and balance or 0.0,
                'credit': balance < 0.0 and -balance or 0.0,
            })
            invoice_lines.append((0, 0, invoice_line_vals))

        # Additional Expenses
        if additional > 0:
            additional_amount = additional
            for add_exp in self.additional_expenses:
                if not add_exp.is_invoiced:
                    if additional_amount > 0 and add_exp.amount - add_exp.amount_invoiced > 0:
                        if add_exp.amount - add_exp.amount_invoiced >= additional_amount:
                            product_id = self.env['product.product'].search(
                                [('product_tmpl_id', '=', add_exp.product_id.id)])
                            description = product_id and product_id.name + " - " + service_name
                            if self.service_order_type == 'employee' and self.employee_id:
                                description += ' - ' + self.employee_id.name
                            elif self.service_order_type == 'dependent' and self.dependent_id:
                                description += ' - ' + self.dependent_id.name
                            account = add_exp.product_id._get_product_accounts()['income']
                            if not account:
                                raise UserError(_('No account defined for product "%s".') % product_id.name)

                            invoice_line_vals = {
                                'name': description,
                                'account_id': account.id,
                                'analytic_account_id': self.option_id.account_id.id if self.option_id.account_id else analytic_acc.get(
                                    'additional_acc'),
                                'quantity': 1,
                                'price_unit': additional_amount,
                                'product_id': product_id[0].id,
                                'additional_expense_id': add_exp.id,
                                'service_process_id': self.id,
                            }

                            balance = -(additional_amount)
                            invoice_line_vals.update({
                                'debit': balance > 0.0 and balance or 0.0,
                                'credit': balance < 0.0 and -balance or 0.0,
                            })
                            add_exp.amount_invoiced += additional_amount
                            additional_amount = 0
                            invoice_lines.append((0, 0, invoice_line_vals))
                        elif add_exp.amount - add_exp.amount_invoiced <= additional_amount:
                            name = add_exp.product_id.name
                            product_id = self.env['product.product'].search(
                                [('product_tmpl_id', '=', add_exp.product_id.id)])
                            description = product_id and product_id.name + " - " + service_name
                            if self.service_order_type == 'employee' and self.employee_id:
                                description += ' - ' + self.employee_id.name
                            elif self.service_order_type == 'dependent' and self.dependent_id:
                                description += ' - ' + self.dependent_id.name
                            account = add_exp.product_id._get_product_accounts()['income']
                            if not account:
                                raise UserError(_('No account defined for product "%s".') % product_id.name)

                            invoice_line_vals = {
                                'name': description,
                                'account_id': account.id,
                                'analytic_account_id': self.option_id.account_id.id if self.option_id.account_id else analytic_acc.get(
                                    'additional_acc'),
                                'quantity': 1,
                                'price_unit': add_exp.amount - add_exp.amount_invoiced,
                                'product_id': product_id[0].id,
                                'additional_expense_id': add_exp.id,
                                'service_process_id': self.id,
                            }

                            balance = -(add_exp.amount - add_exp.amount_invoiced)
                            invoice_line_vals.update({
                                'debit': balance > 0.0 and balance or 0.0,
                                'credit': balance < 0.0 and -balance or 0.0,
                            })
                            additional_amount = additional_amount - (add_exp.amount - add_exp.amount_invoiced)
                            add_exp.amount_invoiced += (add_exp.amount - add_exp.amount_invoiced)
                            invoice_lines.append((0, 0, invoice_line_vals))
        if self.workflow_payment_ids and sum(self.workflow_payment_ids.mapped('amount')) > 0:
            for line in self.workflow_payment_ids:
                payment_amount = line.amount
                if not line.is_invoiced:
                    if payment_amount > 0:
                        product_id = line.product_id
                        product_tmpl_id = product_id.product_tmpl_id
                        description = product_id and product_id.name + " - " + service_name
                        if self.service_order_type == 'employee' and self.employee_id:
                            description += ' - ' + self.employee_id.name
                        elif self.service_order_type == 'dependent' and self.dependent_id:
                            description += ' - ' + self.dependent_id.name
                        account = product_tmpl_id._get_product_accounts()['income']
                        if not account:
                            raise UserError(_('No account defined for product "%s".') % product_id.name)

                        invoice_line_vals = {
                            'name': description,
                            'account_id': account.id,
                            'quantity': 1,
                            'price_unit': payment_amount,
                            'product_id': product_id[0].id,
                            'workflow_payment_id': line.id,
                            'service_process_id': self.id,
                        }

                        balance = -(payment_amount)
                        invoice_line_vals.update({
                            'debit': balance > 0.0 and balance or 0.0,
                            'credit': balance < 0.0 and -balance or 0.0,
                        })
                        invoice_lines.append((0, 0, invoice_line_vals))
                        line.update({'is_invoiced': True})
        self.write({'govt_invoiced': self.govt_invoiced + govt_amount,
                    'fusion_invoiced': self.fusion_invoiced + fusion_amount, 'discount': discount})
        return invoice_lines

    def generate_payments(self, govt=None, fusion=None, invoice_date=None):
        if self.service_order_type in ['company', 'employee', 'dependent']:
            partner_invoice = self.client_id
        else:
            partner_invoice = self.partner_id

        if not partner_invoice:
            raise UserError(_('You have to select an invoice address in the service form.'))
        company = self.env.user.company_id

        journal = self.env['account.move'].with_context(force_company=company.id,
                                                        type='out_invoice').sudo()._get_default_journal()
        govt_amount = 0
        fusion_amount = 0
        if govt >= 0:
            govt_amount = govt
        else:
            govt_amount = self.govt_fees
        if fusion >= 0:
            fusion_amount = fusion
        else:
            fusion_amount = self.fusion_fees

        amount = fusion_amount + govt_amount
        payment_vals = {
            'payment_type': 'inbound',
            'payment_method_id': 1,
            'partner_type': 'customer',
            'is_proforma': True,
            'amount': amount,
            'partner_id': partner_invoice.id,
            'date': invoice_date,
            'journal_id': journal.id,
            'proforma_ids': [],
        }
        payment_line_vals = self.get_payment_line_vals(govt_amount, fusion_amount)
        payment_vals['proforma_ids'] = payment_line_vals
        if not len(payment_vals['proforma_ids']) == 0:
            self.env['account.payment'].sudo().create(payment_vals)
        else:
            raise UserError(_('No invoiceable lines remaining'))

        self.write({'govt_payment': self.govt_payment + govt_amount,
                    'fusion_payment': self.fusion_payment + fusion_amount})

    def get_payment_line_vals(self, govt_amount=None, fusion_amount=None):
        payment_line_vals = []
        if govt_amount > 0:
            name = self.name
            service_name = self.service_id.name

            if not self.option_id.govt_product_id:
                raise UserError('Please Select Govt. Product')
            product_id = self.option_id.govt_product_id
            account = self.option_id.govt_product_id.product_tmpl_id._get_product_accounts()['income']
            if not account:
                raise UserError(_('No account defined for product "%s".') % product_id.name)
            description = product_id and product_id.name + " - " + service_name
            if self.service_order_type == 'employee' and self.employee_id:
                description += ' - ' + self.employee_id.name
            elif self.service_order_type == 'dependent' and self.dependent_id:
                description += ' - ' + self.dependent_id.name
            payment_proforma_lines = {
                'quantity': 1,
                'rate': govt_amount,
                'description': description,
                'service_order_id': self.id,
            }
            payment_line_vals.append((0, 0, payment_proforma_lines))

        if fusion_amount > 0:
            name = self.name
            service_name = self.service_id.name
            if not self.option_id.fusion_product_id:
                raise UserError('Please Select Main Company Product')
            product_id = self.option_id.fusion_product_id
            description = product_id and product_id.name + " - " + service_name
            if self.service_order_type == 'employee' and self.employee_id:
                description += ' - ' + self.employee_id.name
            elif self.service_order_type == 'dependent' and self.dependent_id:
                description += ' - ' + self.dependent_id.name
            account = self.option_id.fusion_product_id.product_tmpl_id._get_product_accounts()['income']
            if not account:
                raise UserError(_('No account defined for product "%s".') % product_id.name)
            payment_proforma_lines = {
                'quantity': 1,
                'rate': fusion_amount,
                'description': description,
                'service_order_id': self.id,
            }
            payment_line_vals.append((0, 0, payment_proforma_lines))
        return payment_line_vals

    def _compute_invoice_count(self):
        Invoice = self.env['account.move']
        for rec in self:
            invoice_lines = self.env['account.move.line'].search([('service_process_id', '=', rec.id)])
            rec.invoice_count = len(set(invoice_lines.mapped('move_id'))) or 0

    def _compute_payment_count(self):
        Payment = self.env['account.payment']
        for rec in self:
            payment_lines = self.env['ebs.proforma.lines'].search([('service_order_id', '=', rec.id)])
            rec.payment_count = len(set(payment_lines.mapped('payment_id'))) or 0

    def action_created_invoice(self):
        self.ensure_one()
        invoice_lines = self.env['account.move.line'].search([('service_process_id', '=', self.id)])
        invoices = invoice_lines.mapped('move_id')
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

    def action_created_proforma_payment(self):
        self.ensure_one()
        payment_lines = self.env['ebs.proforma.lines'].search([('service_order_id', '=', self.id)])
        payments = payment_lines.mapped('payment_id')
        action = self.env.ref('account.action_account_payments').read()[0]
        action["context"] = {"create": False}
        if len(payments) > 1:
            action['domain'] = [('id', 'in', payments.ids)]
        elif len(payments) == 1:
            action['views'] = [(self.env.ref('account.view_account_payment_form').id, 'form')]
            action['res_id'] = payments.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def check_dependancy(self, workflow_id):
        if workflow_id.dependant_workflow_ids:
            temp_workflow_ids = []
            for dep in workflow_id.dependant_workflow_ids:
                flag = False
                existing_id = ''
                for pline in self.proposal_workflow_line_ids:
                    if dep.name == pline.name and dep.stage_id.id == pline.stage_id.id and dep.output == pline.output and \
                            dep.replacement_id.id == pline.replacement_id.id:
                        if set(dep.required_in_docs.ids) == set(pline.required_in_docs.ids) \
                                and set(dep.required_out_docs.ids) == set(pline.required_out_docs.ids) \
                                and dep.is_activity_required == pline.is_activity_required \
                                and dep.is_timesheet_required == pline.is_timesheet_required \
                                and dep.required_payment == pline.required_payment:
                            flag = True
                            existing_id = pline.id
                            break
                if flag:
                    temp_workflow_ids.append(existing_id)
                else:
                    temp_workflow_ids.append(
                        self.env['ebs.crm.proposal.workflow.line'].create({
                            'name': dep.name,
                            'process_char': dep.name,
                            'activity_id': dep.activity_id.id,
                            'sequence': dep.sequence,
                            'status': 'draft',
                            'stage_id': dep.stage_id.id,
                            'output': dep.output,
                            'output_char': dep.output,
                            'replacement_id': dep.replacement_id.id,
                            'service_process_id': self.id,
                            'required_in_docs': [
                                (6, 0, workflow_id.required_in_docs.ids)],
                            'required_out_docs': [
                                (6, 0, workflow_id.required_out_docs.ids)],
                            'is_activity_required': workflow_id.is_activity_required,
                            'is_timesheet_required': workflow_id.is_timesheet_required,
                            'required_payment': workflow_id.required_payment,
                            'workflow_days_to_complete': dep.workflow_days_to_complete,
                            'required_completed_service_ids': [(6, 0, dep.required_completed_service_ids.ids)],
                            'service_phase': dep.service_phase,
                        }).id
                    )
            temp_workflow_id = self.env['ebs.crm.proposal.workflow.line'].create({
                'name': workflow_id.name,
                'process_char': workflow_id.name,
                'activity_id': workflow_id.activity_id.id,
                'sequence': workflow_id.sequence,
                'status': 'draft',
                'stage_id': workflow_id.stage_id.id,
                'output': workflow_id.output,
                'output_char': workflow_id.output,
                'replacement_id': workflow_id.replacement_id.id,
                'service_process_id': self.id,
                'required_in_docs': [(6, 0, workflow_id.required_in_docs.ids)],
                'required_out_docs': [(6, 0, workflow_id.required_out_docs.ids)],
                'is_activity_required': workflow_id.is_activity_required,
                'is_timesheet_required': workflow_id.is_timesheet_required,
                'required_payment': workflow_id.required_payment,
                'workflow_days_to_complete': workflow_id.workflow_days_to_complete,
                'required_completed_service_ids': [(6, 0, workflow_id.required_completed_service_ids.ids)],
                'service_phase': workflow_id.service_phase,
            })
            for id in temp_workflow_ids:
                temp_workflow_id.write({'dependant_workflow_ids': [(4, id)]})
        else:
            flag = False
            for pline in self.proposal_workflow_line_ids:
                if workflow_id.name == pline.name and workflow_id.stage_id.id == pline.stage_id.id and workflow_id.output == pline.output and \
                        workflow_id.replacement_id.id == pline.replacement_id.id:
                    if set(workflow_id.required_in_docs.ids) == set(pline.required_in_docs.ids) \
                            and set(workflow_id.required_out_docs.ids) == set(pline.required_out_docs.ids) \
                            and workflow_id.is_activity_required == pline.is_activity_required \
                            and workflow_id.is_timesheet_required == pline.is_timesheet_required \
                            and workflow_id.required_payment == pline.required_payment:
                        flag = True
                        break
            if not flag:
                workflow_line_id = self.env['ebs.crm.proposal.workflow.line'].create({
                    'name': workflow_id.name,
                    'process_char': workflow_id.name,
                    'activity_id': workflow_id.activity_id.id,
                    'sequence': workflow_id.sequence,
                    'status': 'draft',
                    'stage_id': workflow_id.stage_id.id,
                    'output': workflow_id.output,
                    'output_char': workflow_id.output,
                    'replacement_id': workflow_id.replacement_id.id,
                    'service_process_id': self.id,
                    'required_in_docs': [(6, 0, workflow_id.required_in_docs.ids)],
                    'required_out_docs': [(6, 0, workflow_id.required_out_docs.ids)],
                    'is_activity_required': workflow_id.is_activity_required,
                    'is_timesheet_required': workflow_id.is_timesheet_required,
                    'required_payment': workflow_id.required_payment,
                    'workflow_days_to_complete': workflow_id.workflow_days_to_complete,
                    'required_completed_service_ids': [(6, 0, workflow_id.required_completed_service_ids.ids)],
                    'service_phase': workflow_id.service_phase,
                })

            return True

    def fetch_workflows(self):
        service = self.service_id
        for type in service.document_type_ids:
            if type.output:
                out_doc_line = self.env['ebs.crm.proposal.out.documents'].search(
                    [('doc_type_id', '=', type.document_type_id.id),
                     ('service_process_id', '=', self.id)])
                document_id = self.env['documents.document']
                if type.service:
                    document_id = self.env['documents.document'].search(
                        [('service_process_id', '=', self.id), ('document_type_id', '=', type.document_type_id.id)],
                        order='version desc', limit=1)
                if type.individual:
                    domain = self.get_doc_domain(type.document_type_id.id, self.service_order_type)
                    document_id = self.env['documents.document'].search(
                        domain,
                        order='version desc', limit=1)

                if not out_doc_line:
                    self.env['ebs.crm.proposal.out.documents'].create({
                        'doc_type_id': type.document_type_id.id,
                        'service_process_id': self.id,
                        'name': document_id.id,
                    })
                else:
                    if not out_doc_line.name:
                        out_doc_line.write({'name': document_id.id})

            if type.input:
                in_doc_line = self.env['ebs.crm.proposal.in.documents'].search(
                    [('doc_type_id', '=', type.document_type_id.id),
                     ('service_process_id', '=', self.id)])
                document_id = self.env['documents.document']
                if type.service:
                    document_id = self.env['documents.document'].search(
                        [('service_process_id', '=', self.id), ('document_type_id', '=', type.document_type_id.id)],
                        order='version desc', limit=1)
                if type.individual:
                    domain = self.get_doc_domain(type.document_type_id.id, self.service_order_type)
                    document_id = self.env['documents.document'].search(
                        domain,
                        order='version desc', limit=1)
                if not in_doc_line:
                    line_id = self.env['ebs.crm.proposal.in.documents'].create({
                        'doc_type_id': type.document_type_id.id,
                        'service_process_id': self.id,
                        'name': document_id.id,
                    })
                else:
                    if not in_doc_line.name:
                        in_doc_line.write({'name': document_id.id})

        if self.is_group_related:
            for sub_service in self.sub_service_ids:
                sub_service.fetch_workflows()
        for line in service.workflow_lines:
            flag = False
            if self.option_id and line.service_option_ids and self.option_id.id not in line.service_option_ids.ids:
                flag = True
            for pline in self.proposal_workflow_line_ids:
                if line.name == pline.name and line.stage_id.id == pline.stage_id.id and line.output == pline.output and \
                        line.replacement_id.id == pline.replacement_id.id:
                    if set(line.required_in_docs.ids) == set(pline.required_in_docs.ids) \
                            and set(line.required_out_docs.ids) == set(pline.required_out_docs.ids) \
                            and line.is_activity_required == pline.is_activity_required \
                            and line.is_timesheet_required == pline.is_timesheet_required \
                            and line.required_payment == pline.required_payment:
                        flag = True
            if not flag:
                workflow_line = self.env['ebs.crm.proposal.workflow.line'].search(
                    [('service_process_id', '=', self.id), ('sequence', '=', line.sequence)], limit=1).unlink()
                self.check_dependancy(line)
        for rec in self:
            in_document_ids_list = []
            out_document_ids_list = []
            if rec.proposal_workflow_line_ids:
                for line in rec.proposal_workflow_line_ids:
                    for doc in line.required_in_docs:
                        if doc.id not in rec.in_document_ids.doc_type_id.ids:
                            in_document_ids_list.extend(doc.ids)
                        else:
                            out_doc_line = self.env['ebs.crm.proposal.in.documents'].search(
                                [('doc_type_id', '=', doc.id),
                                 ('service_process_id', '=', self.id)])
                            if not out_doc_line.name:
                                domain = rec.get_doc_domain(doc.id, rec.service_order_type)
                                document_id = self.env['documents.document'].search(
                                    domain,
                                    order='version desc', limit=1)
                                out_doc_line.write({'name': document_id.id})
                    for doc in line.required_out_docs:
                        if doc.id not in rec.out_document_ids.doc_type_id.ids:
                            out_document_ids_list.extend(doc.ids)
                        else:
                            in_doc_line = self.env['ebs.crm.proposal.out.documents'].search(
                                [('doc_type_id', '=', doc.id),
                                 ('service_process_id', '=', self.id)])
                            if not in_doc_line.name:
                                domain = rec.get_doc_domain(doc.id, rec.service_order_type)
                                document_id = self.env['documents.document'].search(
                                    domain,
                                    order='version desc', limit=1)
                                in_doc_line.write({'name': document_id.id})

            if in_document_ids_list or out_document_ids_list:
                if in_document_ids_list:

                    for record in set(in_document_ids_list):
                        domain = rec.get_doc_domain(record, rec.service_order_type)
                        document_id = self.env['documents.document'].search(
                            domain,
                            order='version desc', limit=1)
                        rec.write({
                            'in_document_ids': [(0, 0, {'doc_type_id': record, 'name': document_id.id})]
                        })
                if out_document_ids_list:

                    for record in set(out_document_ids_list):
                        domain = rec.get_doc_domain(record, rec.service_order_type)
                        document_id = self.env['documents.document'].search(
                            domain,
                            order='version desc', limit=1)
                        rec.write({
                            'out_document_ids': [(0, 0, {'doc_type_id': record, 'name': document_id.id})]
                        })

    def get_doc_domain(self, doc_type_id, service_order_type):
        if service_order_type == 'employee':
            domain = [('employee_id', '=', self.employee_id.id), ('document_type_id', '=', doc_type_id)]
        elif service_order_type == 'company':
            related_partners = self.env['ebs.client.contact'].search(
                [('client_id', '=', self.client_id.id)]).mapped('partner_id').ids
            related_partners.append(self.client_id.id)
            related_employees = self.env['hr.employee'].search(
                [('partner_parent_id', '=', self.client_id.id)]).ids
            domain = [('document_type_id', '=', doc_type_id), '|', ('employee_id', 'in', related_employees),
                      ('partner_id', 'in', related_partners)]
        else:
            domain = [('partner_id', '=', self.client_id.id), ('document_type_id', '=', doc_type_id)]
        return domain

    @api.onchange('proposal_id')
    def onchange_proposal_id(self):
        for rec in self:
            if rec.proposal_id:
                rec.service_id = False
                proposal_line_services = self.env['ebs.crm.proposal.line'].search(
                    [('proposal_id', '=', rec.proposal_id.id)]). \
                    mapped('service_id')
                return {'domain': {
                    'service_id': [('id', 'in', proposal_line_services.ids)],
                }}
            else:
                return {'domain': {
                    'service_id': [('id', 'in', self.env['ebs.crm.service'].search([]).ids)],
                }}

    @api.onchange('proposal_workflow_line_ids', 'out_document_ids')
    def onchange_workflow_lines(self):
        for rec in self:
            status_flag = 0
            if rec.proposal_workflow_line_ids or rec.out_document_ids:
                flag = True
                blank = True
                for wline in rec.proposal_workflow_line_ids:
                    if wline.status != 'draft':
                        status_flag = 1
                    if not wline.status == 'completed':
                        flag = False
                for doc in rec.out_document_ids:
                    if not doc.name:
                        blank = False
                        break
                if flag and blank:
                    rec.status = 'completed'
                else:
                    if status_flag == 1:
                        rec.status = 'ongoing'
                    else:
                        rec.status = 'draft'

    def compute_category_ids(self):
        for rec in self:
            pline = rec.pricelist_id.pricelist_line_ids
            pcateg = []
            for line in pline:
                pcateg.append(line.pricelist_category_id.id)
            rec.category_ids = [(6, 0, pcateg)]

    @api.onchange('is_urgent')
    def onchange_urgent(self):
        for rec in self:
            if rec.is_urgent:
                rec.fusion_fees = rec.option_id.fusion_fees * 2
            else:
                rec.fusion_fees = rec.option_id.fusion_fees

    def compute_service_ids(self):
        for rec in self:
            if rec.pricelist_line_id:
                rec.service_ids = rec.pricelist_line_id.service_ids.ids

    @api.onchange('day_to_complete')
    def onchange_day_to_complete(self):
        for rec in self:
            rec.due_date = rec.start_date + timedelta(days=rec.day_to_complete)

    @api.onchange('service_template_id')
    def onchange_service_template(self):
        for rec in self:
            if rec.service_template_id:
                rec.day_to_complete = rec.service_template_id.days_to_complete

    def compute_total_fees(self):
        for rec in self:
            rec.amount_total = rec.govt_fees + rec.fusion_fees

    @api.onchange('option_id')
    def onchange_option(self):
        for rec in self:
            rec.govt_product_id = rec.option_id.govt_product_id.id
            rec.fusion_product_id = rec.option_id.fusion_product_id.id
            rec.govt_fees = rec.option_id.govt_fees
            if rec.is_urgent:
                rec.fusion_fees = rec.option_id.fusion_fees * 2
            else:
                rec.fusion_fees = rec.option_id.fusion_fees

    def action_show_sub_service_process(self):
        self.ensure_one()
        form_view = self.env.ref('ebs_fusion_services.view_ebs_crm_service_process_form')
        tree_view = self.env.ref('ebs_fusion_services.view_ebs_crm_service_process_tree')
        search_view = self.env.ref('ebs_fusion_services.view_ebs_crm_service_process_search')
        return {
            'name': _('Service Orders'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'res_model': 'ebs.crm.service.process',
            'views': [(form_view.id, 'form')],
            'view_id': form_view.id,
            'target': 'current',
            'res_id': self.id,
            'search_view_id': search_view.id,
            'domain': [('id', '=', self.id)]

        }

    def send_service_order_mail(self, subject, body, recipient_ids):
        mail_server_id = self.env['ir.mail_server'].sudo().search([('name', '=', 'Info.system')], limit=1)
        if mail_server_id:
            mail = self.env['mail.mail'].sudo().create({
                'subject': subject,
                'body_html': body,
                'recipient_ids': recipient_ids,
                'mail_server_id': mail_server_id and mail_server_id.id,
            })
            mail.send()

    def send_service_order_notification(self, subject, body, notification_ids):
        self.message_post(
            subject=subject,
            body=body,
            message_type='notification',
            subtype_xmlid='mail.mt_comment', author_id=self.env.user.partner_id.id,
            notification_ids=notification_ids)


class ebsCrmAdditionalExpenses(models.Model):
    _name = 'ebs.crm.additional.expenses'
    _description = 'EBS Additional Expenses'
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.template', string='Product')
    amount = fields.Float(string='Amount')
    is_invoiced = fields.Boolean('Is Invoiced', readonly=1, compute='compute_invoiced')
    service_process_id = fields.Many2one('ebs.crm.service.process', readonly=1)
    invoice_line_id = fields.Many2one('account.move.line', 'Invoice Line', copy=False, readonly=True)
    expense_service_id = fields.Many2one('ebs.crm.service', 'Service')
    amount_invoiced = fields.Float()
    receipt = fields.Binary('Receipt', attachment=True)
    type = fields.Selection([('govt', 'Govt'), ('other', 'Other'), ('fine', 'Fine')], string='Type')

    def compute_invoiced(self):
        for rec in self:
            if rec.amount_invoiced == rec.amount:
                rec.is_invoiced = True
            else:
                rec.is_invoiced = False

    @api.onchange('product_id')
    def onchange_product_id(self):
        for rec in self:
            if rec.product_id.list_price:
                rec.amount = rec.product_id.list_price


class ebsCrmProposalWorkflowLines(models.Model):
    _name = 'ebs.crm.proposal.workflow.line'
    _description = 'EBS Proposal Workflow Lines'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _get_dependent_services(self):
        domain = []
        print(self)
        if self.service_process_id:
            dependant_service_ids = self.service_process_id.service_id.dependent_services_ids.mapped('service').ids
            domain = [('id', 'in', dependant_service_ids)]
        else:
            if self._context.get('service_id'):
                service_id = self.env['ebs.crm.service'].browse([self._context.get('service_id')])
                dependant_service_ids = service_id.dependent_services_ids.mapped('service').ids
                domain = [('id', 'in', dependant_service_ids)]
        return domain

    name = fields.Text('Process', required=1)

    status = fields.Selection(
        [('draft', 'Draft'), ('ongoing', 'Ongoing'), ('onhold', 'Onhold'), ('completed', 'Completed'),
         ('returned', 'Returned'), ('cancelled', 'Cancelled')], default='draft',
        string='Status', group_expand='_expand_states')
    sequence = fields.Integer('Sequence')
    assigned_to = fields.Many2one(comodel_name='res.users', string='User')

    employee_assigned_to = fields.Many2one('hr.employee', 'User')  # domain=_get_employees
    invoice_line_id = fields.Many2one('account.move.line', 'Invoice Line', copy=False, readonly=True)
    stage_id = fields.Many2one('ebs.crm.service.stage', 'Service Stage')
    activity_id = fields.Many2one('ebs.crm.service.activity', 'Activity', domain="[('stage_id','=',stage_id)]")
    output = fields.Text('Output', required=1)

    responsible_user_id = fields.Many2one('ebs.services.user.group', 'Service User Group')
    replacement_id = fields.Many2one('hr.department', 'Replacement Department')

    due_date = fields.Datetime('Due Date')
    readonly = fields.Boolean('Readonly')
    service_process_id = fields.Many2one('ebs.crm.service.process', 'Service Order', readonly=1)
    related_client_id = fields.Many2one('res.partner', 'Client', related='service_process_id.client_id', store=True)
    related_partner_id = fields.Many2one('res.partner', 'Beneficiary', related='service_process_id.partner_id',
                                         store=True)
    related_employee_id = fields.Many2one('hr.employee', 'Employee', related='service_process_id.employee_id',
                                          store=True)
    related_dependent_id = fields.Many2one('res.partner', 'Dependent', related='service_process_id.dependent_id',
                                           store=True)
    related_service_order_type = fields.Selection(
        selection=[('company', 'Company'), ('employee', 'Employee'), ('visitor', 'Visitor'),
                   ('dependent', 'Dependent')], related='service_process_id.service_order_type', store=True)
    related_service_id = fields.Many2one('ebs.crm.service', 'Service', related='service_process_id.service_id')
    is_show = fields.Boolean('Show')

    workflow_timesheet_ids = fields.One2many('ebs.workflow.timesheet', 'workflow_id', string='Timesheets', copy=True)
    dependant_workflow_ids = fields.Many2many('ebs.crm.proposal.workflow.line',
                                              'service_process_workflow_dependant_rel', 'workflow_id', 'dependant_id',
                                              string='Required Completed Workflows',
                                              domain="[('service_process_id','=',service_process_id)]")
    required_completed_service_ids = fields.Many2many('ebs.crm.service', 'dependant_service_workflow_order_rel',
                                                      'workflow_line', 'service_id',
                                                      string='Required Completed Service',
                                                      domain="[('id', 'in', dependant_service_ids)]")
    dependant_service_ids = fields.Many2many('ebs.crm.service', compute='compute_dependant_service_ids')

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date', readonly=1)
    proposal_id = fields.Many2one('ebs.crm.proposal', 'Proposal')
    partner_id = fields.Many2one('res.partner', 'Beneficiary')
    pricelist_id = fields.Many2one('ebs.crm.pricelist', 'Pricelist')
    pricelist_line_id = fields.Many2one('ebs.crm.pricelist.line', 'Pricelist Line', )
    service_id = fields.Many2one('ebs.crm.service', 'Service')
    service_template_id = fields.Many2one('ebs.crm.service.template', 'Service Template')
    next_assigned_user = fields.Many2one('res.users', 'Next Assigned User')
    workflow_complete = fields.Boolean('Workflow Complete', default=False)
    last_workflow = fields.Boolean('Last Workflow', compute='compute_last_workflow', default=False)
    return_reason = fields.Text('Reason for Return')
    is_activity_required = fields.Boolean('Is Activity Required')
    is_timesheet_required = fields.Boolean('Is Timesheet Required')
    required_payment = fields.Boolean('Is Payment Required')
    required_in_docs = fields.Many2many('ebs.document.type', 'workflow_in_doctype_rel', 'workflow_id',
                                        'document_type_id', string='Required In Documents', readonly=1)
    required_out_docs = fields.Many2many('ebs.document.type', 'workflow_out_doctype_rel', 'workflow_id',
                                         'document_type_id', string='Required Out Documents', readonly=1)
    workflow_days_to_complete = fields.Float(string='Days to complete')
    actual_workflow_days_to_complete = fields.Integer(string='Actual days to complete',
                                                      compute='compute_actual_workflow_days_to_complete')
    edit_access = fields.Boolean()
    activity_type_ids = fields.Many2many('mail.activity.type', 'workflow_activity', 'workflow_id', 'activity_id',
                                         string="Activity Type")
    service_phase = fields.Selection([('manual', 'Manual'), ('online', 'Online')], string='Type')
    process_char = fields.Char('Process')
    output_char = fields.Char('Output')
    is_group = fields.Boolean(related='related_service_id.is_group')
    workflow_payment_ids = fields.One2many(comodel_name='ebs.workflow.payment', inverse_name='workflow_id',
                                           string='Payments')

    def unlink(self):
        for rec in self:
            if rec.status != 'draft':
                raise UserError(_('Only Draft Workflow Can Be Delete.'))
        return super(ebsCrmProposalWorkflowLines, self).unlink()

    def compute_dependant_service_ids(self):
        for rec in self:
            sub_service_ids = rec.service_process_id.sub_service_ids
            if sub_service_ids:
                rec.dependant_service_ids = [(6, 0, sub_service_ids.mapped('service_id').ids)]
            else:
                rec.dependant_service_ids = False

    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).status.selection]

    @api.onchange('name')
    def onchange_name(self):
        for rec in self:
            rec.process_char = rec.name

    @api.onchange('output')
    def onchange_output(self):
        for rec in self:
            rec.output_char = rec.output

    @api.onchange('activity_id')
    def onchnage_activity(self):
        for rec in self:
            if rec.activity_id:
                rec.write({'required_in_docs': [(6, 0, rec.activity_id.in_documents.ids)],
                           'required_out_docs': [(6, 0, rec.activity_id.out_documents.ids)]
                           })
            else:
                rec.write({'required_in_docs': [(5, 0, 0)],
                           'required_out_docs': [(5, 0, 0)]
                           })

    @api.depends('start_date', 'end_date')
    def compute_actual_workflow_days_to_complete(self):
        for rec in self:
            if rec.end_date and rec.start_date:
                rec.actual_workflow_days_to_complete = int((rec.end_date - rec.start_date).days)
            else:
                rec.actual_workflow_days_to_complete = 0

    def compute_access(self):
        for rec in self:
            user = self.env.user
            if user.has_group('ebs_fusion_services.group_services_manager'):
                rec.edit_access = True
            else:
                rec.edit_access = False

    def start_workflow(self):
        if self.service_process_id.status == 'draft':
            raise UserError("Workflows cannot be started until the service is started.")
        if not self.assigned_to:
            raise UserError("Please assign a user to workflow.")
        if self.required_completed_service_ids:
            sub_service_ids = self.service_process_id.sub_service_ids.filtered(
                lambda l: l.service_id.id in self.required_completed_service_ids.ids)
            statuses = sub_service_ids.mapped('status')
            if not all(state == 'completed' for state in statuses):
                raise UserError("Please complete the required sub service first before starting this workflow!")

        self.start_date = date.today()
        for dep_workflow in self.dependant_workflow_ids:
            if not dep_workflow.status == 'completed':
                raise UserError("Workflow " + (dep_workflow.name or '') + " must be completed.")
        for in_doc in self.required_in_docs:
            for service_in_doc in self.service_process_id.in_document_ids:
                if service_in_doc.doc_type_id.id == in_doc.id:
                    if not service_in_doc.name:
                        raise UserError("Cannot start workflow, requires document:  " + (in_doc.name or ''))
        self.status = 'ongoing'
        self.readonly = True
        user = self.assigned_to
        body = "The workflow '" + self.name + "' has started"
        mail_server_id = self.env['ir.mail_server'].sudo().search([], order='sequence asc', limit=1)
        if user:
            mail = self.env['mail.mail'].sudo().create({
                'body_html': '<p>The workflow <b>%s</b> of service <b>%s</b> has been started.</p>' % (
                    self.name, self.service_process_id.name),
                'recipient_ids': [(4, user.partner_id.id)],
                'mail_server_id': mail_server_id and mail_server_id.id,
            })
            mail.send()
            activity_type_id = self.env['mail.activity.type'].search([('name', '=', 'To Do')])
            vals = {
                'activity_type_id': activity_type_id.id,
                'res_model_id': self.env['ir.model']._get('res.partner').id,
                'res_id': user.partner_id.id,
                'note': body,
                'user_id': user.id,
            }
            self.env['mail.activity'].create(vals)

    def action_show_workflows_line(self):
        self.ensure_one()
        form_view = self.env.ref('ebs_fusion_services.view_ebs_crm_proposal_workflow_form')
        tree_view = self.env.ref('ebs_fusion_services.view_ebs_crm_proposal_workflow_tree')
        search_view = self.env.ref('ebs_fusion_services.view_ebs_crm_proposal_workflow_search')
        return {
            'name': _('Workflows'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'res_model': 'ebs.crm.proposal.workflow.line',
            'views': [(form_view.id, 'form')],
            'view_id': form_view.id,
            'target': 'current',
            'res_id': self.id,
            'search_view_id': search_view.id,
            'domain': [('id', '=', self.id)]

        }

    def put_onhold(self):
        self.status = 'onhold'

    def returned_workflow(self):
        self.status = 'returned'

    def cancelled_workflow(self):
        self.status = 'cancelled'
        self.end_date = date.today()

    def complete_workflow(self):
        flag = False
        self.status = 'completed'
        self.end_date = date.today()
        print('============================================')
        print('============================================')
        if self.activity_type_ids:
            fixed_activities = self.activity_type_ids.mapped('name')
            activities = self.env['mail.message'].search(
                [('res_id', '=', self._origin.id), ('model', '=', 'ebs.crm.proposal.workflow.line'),
                 ('mail_activity_type_id', 'in', self.activity_type_ids.ids)]).mapped(
                'mail_activity_type_id').mapped('name')
            if self.activity_type_ids and not activities:
                raise ValidationError(
                    'You cannot mark this workflow completed until complete all fixed all activities.')
            check = all(activity in activities for activity in fixed_activities)
            if check is False:
                raise ValidationError(
                    'You cannot mark this workflow completed until complete all fixed all activities.')

        if not self.last_workflow:
            self.write({'workflow_complete': True})
        for record in self.dependant_workflow_ids:
            if record.status != 'completed':
                flag = True
                break
        if flag:
            raise UserError(
                'You cannot mark this workflow completed as dependant workflows have not been completed yet.')

    @api.model
    def open_closed(self):
        user = self.env.user
        domain = []
        if user.has_group('ebs_fusion_services.group_fusion_workflow_manager'):
            domain = ['|', ('service_process_id.company_id', '=', user.company_id.id), ('assigned_to', '=', user.id)]
        if user.has_group('ebs_fusion_services.group_fusion_activity_admin'):
            domain = []
        return {
            'name': _('All Workflows'),
            'type': 'ir.actions.act_window',
            'view_mode': 'kanban,tree,pivot,graph,form,activity',
            'res_model': 'ebs.crm.proposal.workflow.line',
            'target': 'current',
            'context': {},
            'domain': domain
        }

    def set_draft_workflow(self):
        self.status = 'draft'
        self.end_date = ''
        self.readonly = False

    def upload_document(self):
        out_docs = []
        in_docs = []
        for doc_type_out in self.required_out_docs:
            out_document_ids = self.env['ebs.crm.proposal.out.documents'].search(
                [('doc_type_id', '=', doc_type_out.id), ('service_process_id', '=', self.service_process_id.id)])
            for doc in out_document_ids:
                if not doc.name:
                    out_docs.append(doc.id)
        for doc_type_in in self.required_in_docs:
            in_document_ids = self.env['ebs.crm.proposal.in.documents'].search(
                [('doc_type_id', '=', doc_type_in.id), ('service_process_id', '=', self.service_process_id.id)])
            for doc in in_document_ids:
                if not doc.name:
                    in_docs.append(doc.id)
        if not out_docs and not in_docs:
            raise UserError(
                'All required documents have already been uploaded.')
        ctx = {'out_docs': out_docs,
               'in_docs': in_docs,
               }
        if self._context.get('default_service_process_id'):
            service_process_id = self.env['ebs.crm.service.process'].browse(
                self._context.get('default_service_process_id'))
            if service_process_id.service_order_type:
                ctx.update({'service_order_type': service_process_id.service_order_type})
            if service_process_id.employee_id:
                ctx.update({'employee': service_process_id.employee_id.id})
            if service_process_id.client_id:
                ctx.update({'partner': service_process_id.client_id.id})
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'document.validation.wizard',
            'target': 'new',
            'context': ctx
        }

    def compute_last_workflow(self):
        for rec in self:
            seq_list = []
            if rec.service_process_id:
                seq_list = rec.service_process_id.sudo().proposal_workflow_line_ids.mapped('sequence')
            rec.last_workflow = False
            if seq_list:
                if rec.sequence == max(seq_list):
                    rec.last_workflow = True

    @api.model
    def create(self, vals):
        service_process_id = self.env['ebs.crm.service.process'].search([('id', '=', vals.get('service_process_id'))])
        if service_process_id:
            if service_process_id.status != 'draft':
                raise UserError("Cannot add new workflows as the service order is already active.")
        vals['proposal_id'] = service_process_id.proposal_id.id
        vals['partner_id'] = service_process_id.partner_id.id
        vals['pricelist_id'] = service_process_id.pricelist_id.id
        vals['pricelist_line_id'] = service_process_id.pricelist_line_id.id
        vals['service_id'] = service_process_id.service_id.id
        vals['service_template_id'] = service_process_id.service_template_id.id
        res = super(ebsCrmProposalWorkflowLines, self).create(vals)
        if 'assigned_to' in vals and vals['assigned_to']:
            user_id = self.env['res.users'].browse([vals['assigned_to']])
            assign_subject = 'Workflow Assigned'
            assign_body = 'The workflow <b>%s</b> of service <b>%s</b> has been assigned to you.' % (
                vals.get('name'), res.service_process_id.service_id.name)
            res.send_workflow_mail(assign_subject, assign_body, [(4, user_id.partner_id.id)])
            notification_ids = []
            notification_ids.append((0, 0, {
                'res_partner_id': user_id.partner_id.id,
                'notification_type': 'inbox'}))
            res.send_workflow_notification(assign_subject, assign_body, notification_ids)
        return res

    @api.onchange('status')
    def onchange_status(self):
        for rec in self:
            rec.workflow_complete = False
            flag = False
            if rec.status == 'ongoing':
                user = rec.assigned_to
                rec.start_date = datetime.today()
                body = "The workflow '" + rec.name + "' has been set as ongoing"
                if user:
                    activity_type_id = self.env['mail.activity.type'].search([('name', '=', 'To Do')])
                    vals = {
                        'activity_type_id': activity_type_id.id,
                        'res_model_id': self.env['ir.model']._get('res.partner').id,
                        'res_id': user.partner_id.id,
                        'note': body,
                        'user_id': user.id,
                    }
                    self.env['mail.activity'].create(vals)
            if rec.status == 'completed':
                if rec.activity_type_ids:
                    fixed_activities = rec.activity_type_ids.mapped('name')
                    activities = self.env['mail.message'].search(
                        [('res_id', '=', rec._origin.id), ('model', '=', 'ebs.crm.proposal.workflow.line'),
                         ('mail_activity_type_id', 'in', rec.activity_type_ids.ids)]).mapped(
                        'mail_activity_type_id').mapped('name')
                    if rec.activity_type_ids and not activities:
                        raise ValidationError(
                            'You cannot mark this workflow completed until complete all fixed all activities.')
                    check = all(activity in activities for activity in fixed_activities)
                    if check is False:
                        raise ValidationError(
                            'You cannot mark this workflow completed until complete all fixed all activities.')

                rec.write({'end_date': datetime.today()})
                if not rec.last_workflow:
                    rec.write({'workflow_complete': True})
                for record in rec.dependant_workflow_ids:
                    if record.status != 'completed':
                        flag = True
                        break
                if flag:
                    raise UserError(
                        'You cannot mark this workflow completed as dependant workflows have not been completed yet.')

    def write(self, vals):
        if 'assigned_to' in vals and vals['assigned_to']:
            user_id = self.env['res.users'].browse([vals['assigned_to']])
            assign_subject = 'Workflow Assigned'
            assign_body = 'The workflow <b>%s</b> of service <b>%s</b> has been assigned to you.' % (
                self.name, self.service_process_id.service_id.name)
            self.send_workflow_mail(assign_subject, assign_body, [(4, user_id.partner_id.id)])
            notification_ids = []
            notification_ids.append((0, 0, {
                'res_partner_id': user_id.partner_id.id,
                'notification_type': 'inbox'}))
            self.send_workflow_notification(assign_subject, assign_body, notification_ids)

        if 'status' in vals and vals['status'] == 'completed':
            if self.required_in_docs:
                flag = True
                for doc_type in self.required_in_docs:
                    document_id = self.service_process_id.in_document_ids.search(
                        [('doc_type_id', '=', doc_type.id)]).name
                    if not document_id:
                        flag = False
                if not flag:
                    raise UserError(
                        'You cannot mark this workflow completed as required documents have not been uploaded')
            if self.required_out_docs:
                flag = True
                for doc_type in self.required_out_docs:
                    document_id = self.service_process_id.out_document_ids.search(
                        [('doc_type_id', '=', doc_type.id)]).name
                    if not document_id:
                        flag = False
                if not flag:
                    raise UserError(
                        'You cannot mark this workflow completed as required documents have not been uploaded')

            if self.required_payment:
                for line in self.workflow_payment_ids:
                    company_id = line.credit_card_id.company_id
                    journal_id = line.credit_card_id.journal_id
                    if not journal_id:
                        raise UserError(
                            _('Please define a journal for the Credit Card %s.') % (line.credit_card_id.name))
                    move_vals = {
                        'type': 'entry',
                        'date': line.date
                    }
                    expense_account = \
                        line.product_id.product_tmpl_id.with_context(
                            force_company=company_id.id)._get_product_accounts()[
                            'expense']
                    if not expense_account:
                        raise UserError(_('No Expense account defined for product "%s" with company "%s".') % (
                            line.product_id.name, company_id.name))
                    line_ids = [
                        (0, 0, {
                            'account_id': line.credit_card_id.account_id.id,
                            'debit': 0.0,
                            'credit': line.amount,
                        }),
                        (0, 0, {
                            'account_id': expense_account.id,
                            'debit': line.amount,
                            'credit': 0.0,
                        })
                    ]
                    move_vals['line_ids'] = line_ids
                    move_id = self.env['account.move'].sudo().create(move_vals)
                    line.write({'move_id': move_id.id})

            subject = "The workflow '" + self.name + "' has been completed."
            body = 'The workflow <b>%s</b> of service <b>%s</b> has been completed.' % (
                self.name, self.service_process_id.name),

            if self.service_process_id.assigned_user_id:
                recipient_ids = [(4, self.service_process_id.assigned_user_id.partner_id.id)]
                notification_ids = [(0, 0, {
                    'res_partner_id': self.service_process_id.assigned_user_id.partner_id.id,
                    'notification_type': 'inbox'
                })]
                self.service_process_id.send_service_order_mail(subject, body, recipient_ids)
                self.service_process_id.send_service_order_notification(subject, body, notification_ids)

                if not self.service_process_id.proposal_workflow_line_ids.filtered(
                        lambda o: o.status != 'completed' and o.id != self.id):
                    complete_subject = "All workflows related to service order %s has been completed." % self.service_process_id.name
                    complete_body = 'All workflows related to service order <b>%s</b> has been completed.' % self.service_process_id.name
                    self.service_process_id.send_service_order_mail(complete_subject, complete_body, recipient_ids)
                    self.service_process_id.send_service_order_notification(complete_subject, complete_body,
                                                                            notification_ids)

            vals['end_date'] = datetime.today()
            next_seq = self.sequence + 1
            next_workflow_id = self.sudo().search(
                [('service_process_id', '=', self.service_process_id.id), ('sequence', '=', next_seq)], limit=1)
            if next_workflow_id:
                next_workflow_id.status = 'draft'
                if self.assigned_to:
                    print("-------------------------------")
                    message = self.env['mail.message'].sudo().create({
                        'subject': 'Workflow Assigned',
                        'body': '<p>The workflow <b>%s</b> of service <b>%s</b> has been completed. Please assign a user for the next workflow.</p>' % (
                            self.name, self.service_process_id.service_id.name),
                        'author_id': self.assigned_to.partner_id.id,
                        'email_from': self.assigned_to.partner_id.email,
                        'model': 'ebs.crm.proposal.workflow.line',
                        'res_id': self.id,
                    })

                recipient_ids = []
                notification_ids = []
                if next_workflow_id.assigned_to and next_workflow_id.assigned_to.partner_id:
                    recipient_ids.append((4, next_workflow_id.assigned_to.partner_id.id))
                    notification_ids.append((0, 0, {
                        'res_partner_id': next_workflow_id.assigned_to.partner_id.id,
                        'notification_type': 'inbox'}))
                if recipient_ids:
                    self.send_workflow_mail(subject, body, recipient_ids)
                if notification_ids:
                    self.send_workflow_notification(subject, body, notification_ids)

        return super(ebsCrmProposalWorkflowLines, self).write(vals)

    def send_workflow_mail(self, subject, body, recipient_ids):
        mail_server_id = self.env['ir.mail_server'].sudo().search([], order='sequence asc', limit=1)
        mail = self.env['mail.mail'].sudo().create({
            'subject': subject,
            'body_html': body,
            'recipient_ids': recipient_ids,
            'mail_server_id': mail_server_id and mail_server_id.id,
            'email_from': mail_server_id.smtp_user,
        })
        mail.send()

    def send_workflow_notification(self, subject, body, notification_ids):
        self.message_post(
            subject=subject,
            body=body,
            message_type='notification',
            subtype_xmlid='mail.mt_comment', author_id=self.env.user.partner_id.id,
            notification_ids=notification_ids)


class ebsWorkflowTimesheets(models.Model):
    _name = 'ebs.workflow.timesheet'
    _description = 'EBS Workflow Timesheet'

    date = fields.Date('Date')
    name = fields.Char('Description')
    duration = fields.Float('Duration')
    workflow_id = fields.Many2one('ebs.crm.proposal.workflow.line')


class ebsCrmInDocuments(models.Model):
    _name = 'ebs.crm.proposal.in.documents'
    _description = 'EBS CRM Proposal In Documents'
    _rec_name = 'name'

    doc_type_id = fields.Many2one('ebs.document.type', string='Document Type', readonly=1)
    service_process_id = fields.Many2one('ebs.crm.service.process', readonly=1)

    name = fields.Many2one('documents.document', string='Document')
    expiry_date = fields.Date('Expiry Date', related='name.expiry_date')
    number = fields.Char(related='name.document_number', string='Document Number')

    employee_id = fields.Many2one('hr.employee', string="Employee", related="service_process_id.employee_id")
    partner_id = fields.Many2one('res.partner', string="Partner")

    @api.onchange('doc_type_id')
    def onchange_doc_type_id(self):
        doc_type = self.doc_type_id
        if doc_type:
            document = self.env['documents.document'].search(
                [('partner_id', '=', self.service_process_id.partner_id.id), ('document_type_id', '=', doc_type.id)])
            if len(document) == 1:
                self.name = document.id

    def preview_document(self):
        self.ensure_one()
        if self.name:
            action = {
                'type': "ir.actions.act_url",
                'target': "_blank",
                'url': '/documents/content/preview/%s' % self.name.id
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
                action['url'] = '/documents/content/%s' % self.name.id
            return action

    def upload_file_contact(self):
        action = self.env.ref('ebs_fusion_documents.document_button_action').read()[0]
        context = {
            'default_partner_id': self.partner_id.id,
        }
        action['context'] = context
        return action

    def upload_file_employee(self):
        action = self.env.ref('ebs_fusion_documents.document_button_action').read()[0]
        context = {
            'default_employee_id': self.employee_id.id,
            'default_partner_id': self.employee_id.user_partner_id.id,
        }

        action['context'] = context
        return action

    def upload_file(self):
        action = self.env.ref('ebs_fusion_documents.document_button_action').read()[0]
        context = {
            'default_service_process_id': self.service_process_id.id,
            'default_proposal_id': self.service_process_id.proposal_line_id.proposal_id.id,
            'default_document_type_id': self.doc_type_id.id,
            'default_employee_id': self.employee_id.id,
            'hide_field': 1,
        }

        action['context'] = context
        return action


class ebsWorkflowDocumentTracking(models.Model):
    _name = 'ebs.workflow.doc.tracking'
    _description = 'EBS Workflow Document Tracking'

    def default_employee(self):
        employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return employee_id.id or False

    document_id = fields.Many2one('documents.document', string='Document')
    tracking_date = fields.Datetime('Date', default=datetime.today())
    employee_id = fields.Many2one('hr.employee', string='Employee', default=default_employee)
    description = fields.Char('Description')
    workflow_id = fields.Many2one('ebs.crm.proposal.workflow.line')

    @api.onchange('tracking_date')
    def onchange_date(self):
        doc_ids = []
        for rec in self:
            in_docs = rec.workflow_id.service_process_id.in_document_ids
            out_docs = rec.workflow_id.service_process_id.out_document_ids
            for doc in in_docs:
                doc_ids.append(doc.name.id)
            for doc in out_docs:
                doc_ids.append(doc.name.id)

        return {'domain': {
            'document_id': [('id', 'in', doc_ids)],
        }}


class ebsCrmLaborQuota(models.Model):
    _name = 'ebs.crm.labor.quota'
    _description = 'EBS CRM Labor Quota'

    job_id = fields.Many2one('hr.job', "Job Title")
    nationality_id = fields.Many2one('res.country', "Nationality")
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Gender')
    ref_no = fields.Char("Reference Number")
    qty = fields.Integer("Quantity")
    is_approved = fields.Boolean(string='Approved')
    service_order_id = fields.Many2one('ebs.crm.service.process', "Service Order")


class ManageLaborQuotaLine(models.Model):
    _name = 'manage.labor.quota.line'
    _description = 'Manage Labor Quota Line'

    service_order_id = fields.Many2one('ebs.crm.service.process')
    labor_quota_line_id = fields.Many2one('labor.quota.line')
    labor_quota_subline_id = fields.Many2one('labor.quota.subline', string="Labor Quota Subline")
    ref_no = fields.Char("Reference Number")
    nationality_id = fields.Many2one('res.country', "Nationality")
    job_id = fields.Many2one('hr.job', "Job Title")
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Gender')
    status = fields.Selection([('available', 'Available'), ('booked', 'Booked'),
                               ('released', 'Released'), ('updated', 'Updated')], string='Status')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    is_approved = fields.Boolean("Approved")

    qty = fields.Integer("Quantity")

    @api.onchange('labor_quota_line_id')
    def onchange_labor_quota_line_id(self):
        if self.service_order_id.option_name == 'manage' and self.service_order_id.labor_quota_id:
            return {'domain': {'labor_quota_line_id': [('labor_id', '=', self.service_order_id.labor_quota_id.id)]}}


class LaborQuotaRequestLine(models.Model):
    _name = 'labor.quota.request.line'
    _description = 'Labor Quota Request Line'

    service_order_id = fields.Many2one('ebs.crm.service.process')
    job_id = fields.Many2one('hr.job', "Job Title")
    nationality_id = fields.Many2one('res.country', "Nationality")
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Gender')
    qty = fields.Integer("Quantity")
