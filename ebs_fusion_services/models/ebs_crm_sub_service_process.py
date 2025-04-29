from datetime import datetime, date

from lxml import etree
from collections import defaultdict
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta


class ebsCrmSubServiceProcess(models.Model):
    _name = 'ebs.crm.sub.service.process'
    _description = 'EBS Sub Service Order'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    def _default_currency_id(self):
        return self.env.user.company_id.currency_id.id

    name = fields.Char('Name', readonly=1)
    currency_id = fields.Many2one('res.currency', default=_default_currency_id)
    proposal_line_id = fields.Many2one('ebs.crm.proposal.line')
    pricelist_id = fields.Many2one('ebs.crm.pricelist', 'Pricelist')
    proposal_id = fields.Many2one(related='proposal_line_id.proposal_id', string='Proposal', store=True)
    service_order_type = fields.Selection(
        [('client', 'Client'), ('contact', 'Contact'), ('employee', 'Employee'), ('dependant', 'Dependant')]
        , string='Partner Type')
    partner_id = fields.Many2one('res.partner', string='Contact')
    main_partner_id = fields.Many2one('res.partner', 'Client')
    client_id = fields.Many2one('res.partner', 'Client',
                                domain=['|', ('company_partner', '=', True), ('is_customer', '=', True),
                                        ('is_company', '=', True)])
    employee_id = fields.Many2one('hr.employee', 'Employee')
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
                                                 string='Workflow Lines', copy=True)

    out_document_ids = fields.One2many('ebs.crm.proposal.out.documents', 'service_process_id', string='Out Documents',
                                       copy=True)
    in_document_ids = fields.One2many('ebs.crm.proposal.in.documents', 'service_process_id', string='In Documents',
                                      copy=True)
    additional_expenses = fields.One2many('ebs.crm.additional.expenses', 'service_process_id',
                                          string='Additional Expenses', copy=True)
    invoice_count = fields.Integer('Invoice Count', compute='_compute_invoice_count')
    service_order_date = fields.Date('Service Order Date', default=datetime.today())
    generated_from_portal = fields.Boolean('From Portal')
    completed = fields.Boolean('Completed')
    amount_total = fields.Float('Total Fees', compute='compute_total_fees')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    category_ids = fields.Many2many('ebs.crm.pricelist.category', 'CategoryIDs_sub_process',
                                    compute='compute_category_ids')
    service_ids = fields.Many2many('ebs.crm.service', 'ServiceIDs_sub_process', compute='compute_service_ids')
    is_individual = fields.Boolean('Individual')
    is_urgent = fields.Boolean('Urgent')
    comments = fields.Text(related='pricelist_line_id.comments')
    govt_invoiced = fields.Float('Govt. Invoiced')

    fusion_invoiced = fields.Float('Fusion Invoiced')

    discount = fields.Float('Discount')
    day_to_complete = fields.Float(string='Days to complete')
    actual_days_to_complete = fields.Integer(string='Actual days to complete',
                                             compute='compute_actual_days_to_complete')
    group_id = fields.Many2one('ebs.crm.service.groups', string="Service Group")
    option = fields.Selection([
        ('new', 'New'),
        ('renew', 'Renew'),
        ('manage', 'Other'),
    ], string="Option")
    duration = fields.Selection([('1 year', '1 Year'), ('2 years', '2 Years'), ('3 years', '3 Years')],
                                string='Duration')

    group_service_id = fields.Many2one('ebs.crm.service.process', string="Group Service")
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

            if rec.option.name == 'manage':
                rec.manage_labor_quota_line_ids = [(5, 0, 0)]

    @api.onchange('status')
    def onchange_status(self):
        for rec in self:
            if rec.labor_quota_status != 'rejected':
                if rec.status == 'completed' and rec.is_labor_quota and rec.option == 'renew':
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

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(ebsCrmSubServiceProcess, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                                   toolbar=toolbar,
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

    @api.depends('start_date', 'end_date')
    def compute_actual_days_to_complete(self):
        for rec in self:
            if rec.end_date and rec.start_date:
                rec.actual_days_to_complete = int((rec.end_date - rec.start_date).days)
            else:
                rec.actual_days_to_complete = 0

    def check_existing_line(self, subline, labor_quota):
        line = labor_quota.labor_quota_line_id.filtered(lambda
                                                            o: o.nationality_id.id == subline.nationality_id.id and o.job_id.id == subline.job_id.id and o.gender == subline.gender)
        return line

    def check_subline_changes(self, subline):
        if subline.nationality_id.id == subline.labor_quota_subline_id.nationality_id.id and subline.job_id.id == subline.labor_quota_subline_id.job_id.id and subline.gender == subline.labor_quota_subline_id.gender:
            return False
        else:
            return True

    def write(self, vals):
        template_obj = self.env['mail.mail']
        if 'pricelist_line_id' in vals:
            pricelist_line_id = self.env['ebs.crm.pricelist.line'].browse([vals['pricelist_line_id']])
            if self.is_urgent:
                self.govt_fees = pricelist_line_id.govt_urgent_fees
                self.fusion_fees = pricelist_line_id.fusion_urgent_fees
            else:
                self.govt_fees = pricelist_line_id.govt_fees
                self.fusion_fees = pricelist_line_id.fusion_fees
        if 'status' in vals:
            receivers = []
            if self.partner_related_companies:
                for partner in self.partner_related_companies:
                    receivers.append((4, partner.id))
            else:
                receivers.append((4, self.partner_id.id))

            if vals['status'] == 'completed':
                if self.labor_quota_line_ids and self.option == 'new' and self.labor_quota_status != 'rejected':
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
                if self.option == 'new' and self.labor_quota_status == 'rejected':
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

                if self.manage_labor_quota_line_ids and self.option == 'manage' and self.labor_quota_status == 'approved':
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
                    'recipient_ids': receivers,
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
        return super(ebsCrmSubServiceProcess, self).write(vals)

    @api.model
    def create(self, vals):
        if 'proposal_line_id' in vals:
            proposal_line_id = self.env['ebs.crm.proposal.line'].browse([vals.get('proposal_line_id')])
            vals['pricelist_id'] = proposal_line_id.proposal_id.pricelist_id.id
            vals['partner_id'] = proposal_line_id.proposal_id.contact_id.id
            vals['govt_fees'] = proposal_line_id.govt_fees
            vals['fusion_fees'] = proposal_line_id.fusion_fees
        else:
            pricelist_line_id = self.env['ebs.crm.pricelist.line'].browse([vals.get('pricelist_line_id')])
            if pricelist_line_id:
                if 'is_urgent' in vals and vals.get('is_urgent'):
                    vals['govt_fees'] = pricelist_line_id.govt_urgent_fees
                    vals['fusion_fees'] = pricelist_line_id.fusion_urgent_fees
                else:
                    vals['govt_fees'] = pricelist_line_id.govt_fees
                    vals['fusion_fees'] = pricelist_line_id.fusion_fees
        res = super(ebsCrmSubServiceProcess, self).create(vals)
        if res.generated_from_portal:
            users = self.env['res.users'].sudo().search([])
            partner_ids = []
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

            mail_server_id = self.env['ir.mail_server'].sudo().search([], order='sequence asc', limit=1)
            mail = self.env['mail.mail'].sudo().create({
                'body_html': '<p>A new service order has been created %s for contact %s</p>' % (
                    res.name, res.partner_id.name),

                'recipient_ids': [(6, 0, partner_ids)],
                'mail_server_id': mail_server_id and mail_server_id.id,
            })
            mail.send()
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

    def compute_invoiced(self):
        for rec in self:
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

    def generate_invoice(self, govt=None, fusion=None, additional=None, discount=None):
        partner_invoice = self.partner_id
        if not partner_invoice:
            raise UserError(_('You have to select an invoice address in the service form.'))
        company = self.env.user.company_id

        journal = self.env['account.move'].with_context(force_company=company.id,
                                                        type='out_invoice').sudo()._get_default_journal()
        if not journal:
            raise UserError(_('Please define an accounting sales journal for the company %s (%s).') % (
                self.company_id.name, self.company_id.id))
        invoice_vals = {
            'type': 'out_invoice',
            'partner_id': partner_invoice.id,
            'line_ids': [],
            'invoice_origin': self.name,
            'service_process_id': self.id,
            'invoice_line_ids': [],
        }
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

        if govt_amount > 0:
            name = self.name
            if not self.govt_product_id:
                raise UserError('Please Select Govt. Product')
            product_id = self.govt_product_id
            account = self.govt_product_id._get_product_accounts()['income']
            if not account:
                raise UserError(_('No account defined for product "%s".') % product_id.name)
            invoice_line_vals = {
                'name': name,
                'account_id': account.id,
                'quantity': 1,
                'price_unit': govt_amount,
                'product_id': product_id[0].id,
                'govt': True,
            }

            balance = -(govt_amount)
            invoice_line_vals.update({
                'debit': balance > 0.0 and balance or 0.0,
                'credit': balance < 0.0 and -balance or 0.0,
            })
            invoice_vals['invoice_line_ids'].append((0, 0, invoice_line_vals))

        if fusion_amount > 0:
            name = self.name
            if not self.fusion_product_id:
                raise UserError('Please Select Main Company Product')
            product_id = self.fusion_product_id
            account = self.fusion_product_id._get_product_accounts()['income']
            if not account:
                raise UserError(_('No account defined for product "%s".') % product_id.name)
            invoice_line_vals = {
                'name': name,
                'account_id': account.id,
                'quantity': 1,
                'price_unit': fusion_amount,
                'product_id': product_id[0].id,
                'fusion': True,
            }
            if discount:
                invoice_line_vals.update({'discount': discount, })

            balance = -(fusion_amount)
            invoice_line_vals.update({
                'debit': balance > 0.0 and balance or 0.0,
                'credit': balance < 0.0 and -balance or 0.0,
            })
            invoice_vals['invoice_line_ids'].append((0, 0, invoice_line_vals))

        # Additional Expenses
        if additional > 0:
            additional_amount = additional
            for add_exp in self.additional_expenses:
                if not add_exp.is_invoiced:
                    if additional_amount > 0 and add_exp.amount - add_exp.amount_invoiced > 0:
                        if add_exp.amount - add_exp.amount_invoiced >= additional_amount:
                            name = add_exp.product_id.name
                            product_id = self.env['product.product'].search(
                                [('product_tmpl_id', '=', add_exp.product_id.id)])
                            account = add_exp.product_id._get_product_accounts()['income']
                            if not account:
                                raise UserError(_('No account defined for product "%s".') % product_id.name)

                            invoice_line_vals = {
                                'name': name,
                                'account_id': account.id,
                                'quantity': 1,
                                'price_unit': additional_amount,
                                'product_id': product_id[0].id,
                                'additional_expense_id': add_exp.id,
                            }

                            balance = -(additional_amount)
                            invoice_line_vals.update({
                                'debit': balance > 0.0 and balance or 0.0,
                                'credit': balance < 0.0 and -balance or 0.0,
                            })
                            add_exp.amount_invoiced += additional_amount
                            additional_amount = 0
                            invoice_vals['invoice_line_ids'].append((0, 0, invoice_line_vals))
                        elif add_exp.amount - add_exp.amount_invoiced <= additional_amount:
                            name = add_exp.product_id.name
                            product_id = self.env['product.product'].search(
                                [('product_tmpl_id', '=', add_exp.product_id.id)])
                            account = add_exp.product_id._get_product_accounts()['income']
                            if not account:
                                raise UserError(_('No account defined for product "%s".') % product_id.name)

                            invoice_line_vals = {
                                'name': name,
                                'account_id': account.id,
                                'quantity': 1,
                                'price_unit': add_exp.amount - add_exp.amount_invoiced,
                                'product_id': product_id[0].id,
                                'additional_expense_id': add_exp.id,
                            }

                            balance = -(add_exp.amount - add_exp.amount_invoiced)
                            invoice_line_vals.update({
                                'debit': balance > 0.0 and balance or 0.0,
                                'credit': balance < 0.0 and -balance or 0.0,
                            })
                            additional_amount = additional_amount - (add_exp.amount - add_exp.amount_invoiced)
                            add_exp.amount_invoiced += (add_exp.amount - add_exp.amount_invoiced)
                            invoice_vals['invoice_line_ids'].append((0, 0, invoice_line_vals))

        if not len(invoice_vals['invoice_line_ids']) == 0:
            self.env['account.move'].with_context(default_move_type='out_invoice').sudo().create(invoice_vals)
        else:
            raise UserError(_('No invoiceable lines remaining'))
        self.write({'govt_invoiced': self.govt_invoiced + govt_amount,
                    'fusion_invoiced': self.fusion_invoiced + fusion_amount})

    def _compute_invoice_count(self):
        Invoice = self.env['account.move']

        for rec in self:
            rec.invoice_count = Invoice.search_count(
                [('service_process_id', '=', rec.id)]) or 0

    def action_created_invoice(self):
        self.ensure_one()
        invoices = self.env['account.move'].sudo().search([('service_process_id', '=', self.id)])
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

    def check_dependancy(self, workflow_id):
        if workflow_id.dependant_workflow_ids:
            temp_workflow_ids = []
            for dep in workflow_id.dependant_workflow_ids:
                flag = False
                existing_id = ''
                for pline in self.proposal_workflow_line_ids:
                    if dep.name.name == pline.name and dep.stage_id.id == pline.stage_id.id and dep.output == pline.output and \
                            dep.replacement_id.id == pline.replacement_id.id:
                        if set(dep.required_in_docs.ids) == set(pline.required_in_docs.ids) \
                                and set(dep.required_out_docs.ids) == set(pline.required_out_docs.ids) \
                                and dep.is_activity_required == pline.is_activity_required:
                            flag = True
                            existing_id = pline.id
                            break
                if flag:
                    temp_workflow_ids.append(existing_id)
                else:
                    temp_workflow_ids.append(
                        self.env['ebs.crm.proposal.workflow.line'].create({
                            'name': dep.name.name,
                            'activity_id': dep.activity_id.id,
                            'sequence': dep.sequence,
                            'status': 'draft',
                            'stage_id': dep.stage_id.id,
                            'output': dep.output,
                            'replacement_id': dep.replacement_id.id,
                            'service_process_id': self.id,
                            'required_in_docs': [
                                (6, 0, workflow_id.required_in_docs.ids)],
                            'required_out_docs': [
                                (6, 0, workflow_id.required_out_docs.ids)],
                            'is_activity_required': workflow_id.is_activity_required,
                            'workflow_days_to_complete': dep.workflow_days_to_complete,
                        }).id
                    )
            temp_workflow_id = self.env['ebs.crm.proposal.workflow.line'].create({
                'name': workflow_id.name.name,
                'activity_id': workflow_id.activity_id.id,
                'sequence': workflow_id.sequence,
                'status': 'draft',
                'stage_id': workflow_id.stage_id.id,
                'output': workflow_id.output,
                'replacement_id': workflow_id.replacement_id.id,
                'service_process_id': self.id,
                'required_in_docs': [(6, 0, workflow_id.required_in_docs.ids)],
                'required_out_docs': [(6, 0, workflow_id.required_out_docs.ids)],
                'is_activity_required': workflow_id.is_activity_required,
                'workflow_days_to_complete': workflow_id.workflow_days_to_complete,
            })
            for id in temp_workflow_ids:
                temp_workflow_id.write({'dependant_workflow_ids': [(4, id)]})
        else:
            flag = False
            for pline in self.proposal_workflow_line_ids:
                if workflow_id.name.name == pline.name and workflow_id.stage_id.id == pline.stage_id.id and workflow_id.output == pline.output and \
                        workflow_id.replacement_id.id == pline.replacement_id.id:
                    if set(workflow_id.required_in_docs.ids) == set(pline.required_in_docs.ids) \
                            and set(workflow_id.required_out_docs.ids) == set(pline.required_out_docs.ids) \
                            and workflow_id.is_activity_required == pline.is_activity_required:
                        flag = True
                        break
            if not flag:
                workflow_line_id = self.env['ebs.crm.proposal.workflow.line'].create({
                    'name': workflow_id.name.name,
                    'activity_id': workflow_id.activity_id.id,
                    'sequence': workflow_id.sequence,
                    'status': 'draft',
                    'stage_id': workflow_id.stage_id.id,
                    'output': workflow_id.output,
                    'replacement_id': workflow_id.replacement_id.id,
                    'service_process_id': self.id,
                    'required_in_docs': [(6, 0, workflow_id.required_in_docs.ids)],
                    'required_out_docs': [(6, 0, workflow_id.required_out_docs.ids)],
                    'is_activity_required': workflow_id.is_activity_required,
                    'workflow_days_to_complete': workflow_id.workflow_days_to_complete,
                })

            return True

    def fetch_workflows(self):
        service = self.service_id
        service_template = self.service_template_id
        for type in service_template.document_type_ids:
            if type.output:
                out_doc_line = self.env['ebs.crm.proposal.out.documents'].search(
                    [('doc_type_id', '=', type.document_type_id.id),
                     ('service_process_id', '=', self.id)])

                if not out_doc_line:
                    self.env['ebs.crm.proposal.out.documents'].create({
                        'doc_type_id': type.document_type_id.id,
                        'service_process_id': self.id,

                    })
            if type.input:
                in_doc_line = self.env['ebs.crm.proposal.in.documents'].search(
                    [('doc_type_id', '=', type.document_type_id.id),
                     ('service_process_id', '=', self.id)])

                if not in_doc_line:
                    line_id = self.env['ebs.crm.proposal.in.documents'].create({
                        'doc_type_id': type.document_type_id.id,
                        'service_process_id': self.id,

                    })

        for line in service_template.workflow_lines:
            flag = False
            for pline in self.proposal_workflow_line_ids:
                if line.name.name == pline.name and line.stage_id.id == pline.stage_id.id and line.output == pline.output and \
                        line.replacement_id.id == pline.replacement_id.id:
                    if set(line.required_in_docs.ids) == set(pline.required_in_docs.ids) \
                            and set(line.required_out_docs.ids) == set(pline.required_out_docs.ids) \
                            and line.is_activity_required == pline.is_activity_required:
                        flag = True
            if not flag:
                workflow_line = self.env['ebs.crm.proposal.workflow.line'].search(
                    [('service_process_id', '=', self.id), ('sequence', '=', line.sequence)], limit=1).unlink()

                self.check_dependancy(line)

        docs = self.proposal_workflow_line_ids.required_in_docs.mapped('name')
        recipient_ids = [(4, self.client_id.id), (4, self.env.user.id)]
        mail_server_id = self.env['ir.mail_server'].sudo().search([], order='sequence asc', limit=1)
        mail = self.env['mail.mail'].sudo().create({
            'body_html': '<p>Sub service order %s has %s required in documents.</p>' % (self.name, ', '.join(docs)),
            'subject': 'Required In Documents',
            'recipient_ids': recipient_ids,
            'mail_server_id': mail_server_id and mail_server_id.id,
        })
        mail.send()

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

    @api.onchange('status')
    def onchange_status(self):
        print("========onchange status called==========")
        for rec in self:
            flag = False
            blank = False
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
                if flag:
                    raise UserError(
                        'You cannot mark this process completed as all workflows have not been completed yet.')
                if blank:
                    raise UserError(
                        'You cannot mark this process completed as all out documents have not been updated yet.')
            else:
                rec.write({'completed': False})

    @api.onchange('service_order_type')
    def onchange_service_order_type(self):
        for rec in self:
            if rec.service_order_type == 'client':
                rec.partner_id = rec.client_id
                return {'domain': {
                    'partner_id': [('is_company', '=', True)],
                }}
            if rec.service_order_type == 'contact':
                return {'domain': {
                    'partner_id': [('parent_id', '=', rec.client_id.id),
                                   ('is_company', '!=', True)],
                }}
            if rec.service_order_type == 'dependant':
                rec.partner_id = ''
                return {'domain': {
                    'partner_id': [('parent_id', '=', rec.client_id.id), ('is_dependent', '=', True)],
                }}
            if rec.service_order_type == 'employee':
                return {'domain': {
                    'employee_id': [('parent_id', '=', rec.client_id.id)],
                }}

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        for rec in self:
            if rec.employee_id:
                rec.partner_id = rec.employee_id.user_partner_id.id
                print(rec.partner_id, "partner--------------------")

    def compute_category_ids(self):
        for rec in self:
            pline = rec.pricelist_id.pricelist_line_ids
            pcateg = []
            for line in pline:
                pcateg.append(line.pricelist_category_id.id)
            rec.category_ids = [(6, 0, pcateg)]

    @api.onchange('pricelist_category_id')
    def onchange_pricelist_category(self):
        for rec in self:
            pline = rec.pricelist_id.pricelist_line_ids
            pcateg = []
            for line in pline:
                pcateg.append(line.pricelist_category_id.id)
            pricelist_lines = self.env['ebs.crm.pricelist.line'].search(
                [('pricelist_category_id', '=', rec.pricelist_category_id.id),
                 ('pricelist_id', '=', rec.pricelist_id.id)])
            rec.pricelist_line_id = False
            return {'domain': {
                'pricelist_line_id': [('id', 'in', pricelist_lines.ids)],
                'pricelist_category_id': [('id', 'in', pcateg)]
            }}

    @api.onchange('pricelist_line_id')
    def onchange_pricelist_line(self):
        for rec in self:

            services = rec.pricelist_line_id.service_ids
            if rec.pricelist_line_id.govt_product_id:
                rec.govt_fees = rec.pricelist_line_id.govt_fees
            if rec.pricelist_line_id.fusion_product_id:
                rec.fusion_fees = rec.pricelist_line_id.fusion_fees

            return {'domain': {
                'service_id': [('id', 'in', services.ids)],
            }}

    @api.onchange('is_urgent')
    def onchange_urgent(self):
        for rec in self:
            if rec.is_urgent:
                if rec.pricelist_line_id.govt_product_id:
                    rec.govt_fees = rec.pricelist_line_id.govt_urgent_fees
                if rec.pricelist_line_id.fusion_product_id:
                    rec.fusion_fees = rec.pricelist_line_id.fusion_urgent_fees
            else:
                if rec.pricelist_line_id.govt_product_id:
                    rec.govt_fees = rec.pricelist_line_id.govt_fees
                if rec.pricelist_line_id.fusion_product_id:
                    rec.fusion_fees = rec.pricelist_line_id.fusion_fees

    def compute_service_ids(self):
        for rec in self:
            if rec.pricelist_line_id:
                rec.service_ids = rec.pricelist_line_id.service_ids.ids

    @api.onchange('service_id')
    def onchange_service(self):
        for rec in self:
            if rec.service_id:
                service_templates = self.env['ebs.crm.service.template'].search(
                    [('service_id', '=', rec.service_id.id)])
                rec.day_to_complete = rec.service_id.days_to_complete

                return {'domain': {
                    'service_template_id': [('id', 'in', service_templates.ids)],
                }}

    @api.onchange('service_template_id')
    def onchange_service_template(self):
        for rec in self:
            if rec.service_template_id:
                rec.day_to_complete = rec.service_template_id.days_to_complete

    def compute_total_fees(self):
        for rec in self:
            rec.amount_total = rec.govt_fees + rec.fusion_fees


class LaborQuotaRequestLine(models.Model):
    _name = 'labor.quota.request.line'
    _description = 'Labor Quota Request Line'

    service_order_id = fields.Many2one('ebs.crm.service.process')
    job_id = fields.Many2one('hr.job', "Job Title")
    nationality_id = fields.Many2one('res.country', "Nationality")
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Gender')
    qty = fields.Integer("Quantity")
