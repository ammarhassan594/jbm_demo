from odoo import models, fields, api, _
import ast


class PurchaseorderLine(models.Model):
    _inherit = 'purchase.order.line'

    supplying_duration = fields.Char(string="Supplying Duration", required=False, )
    insurance_duration = fields.Char(string="Insurance Duration / Technical Support", required=False, )
    tax_subtotal_affect = fields.Boolean(string="Is tax effect on subtotal", compute="_compute_tax_subtotal_affect",
                                         store=True)
    price_subtotal = fields.Monetary(inverse="_inverse_price_subtotal")

    @api.model
    def _prepare_purchase_order_line(self, product_id, product_qty, product_uom, company_id, supplier, po):
        res = super(PurchaseorderLine, self)._prepare_purchase_order_line(product_id, product_qty, product_uom,
                                                                          company_id, supplier, po)
        if 'unit_price' in self._context:
            res['price_unit'] = self._context.get('unit_price')

        return res

    @api.onchange('price_subtotal')
    def _inverse_price_subtotal(self):
        for line in self:
            if line.product_qty:
                line.price_unit = line.price_subtotal / line.product_qty

    @api.depends('taxes_id')
    def _compute_tax_subtotal_affect(self):
        for line in self:
            line.tax_subtotal_affect = any(line.taxes_id.mapped('include_base_amount')) or \
                                       any(line.taxes_id.mapped('price_include'))


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    variant_order_id = fields.Many2one('purchase.order', string="Variant order id")
    is_variant_order = fields.Boolean(string="Is variant order")
    purchase_order_evaluation_ids = fields.One2many('purchase.order.evaluation', 'purchase_order_id',
                                                    string="Supplier Evaluation")
    approved_by = fields.Many2one('res.users', string="Approved By")
    deadline_date = fields.Date(string="Date Deadline", required=False, )
    subject = fields.Char(string="Subject", required=False, )
    rfq_terms_id = fields.Many2one(comodel_name="rfq.terms", string="RFQ Terms and Conditions",
                                   compute="_compute_rfq_terms_id")

    partner_id = fields.Many2one('res.partner', required=False)

    evaluation_state = fields.Selection(string="Evaluation State", selection=[('success', 'Success'), ('fail', 'Fail')],
                                        compute="_compute_evaluation_state",
                                        store=True)

    employee_ids = fields.Many2many('hr.employee', string="Committee")
    user_ids = fields.Many2many('res.users', string="Users", compute="_get_users")
    recommendation = fields.Text(string="Recommendation")
    purchase_description = fields.Text(string="Description")
    approval_sequence = fields.Char(string="PO")
    quotation_date = fields.Date()

    @api.onchange('employee_ids')
    @api.depends('employee_ids')
    def _get_users(self):
        for record in self:
            users = []
            if record.employee_ids:
                for employee in record.employee_ids:
                    if employee.user_id:
                        if employee.user_id.id not in users:
                            users.append(employee.user_id.id)
            record.user_ids = [(6, 0, users)] if users else False

    @api.depends('purchase_order_evaluation_ids', 'purchase_order_evaluation_ids.total_score',
                 'purchase_order_evaluation_ids.min_score')
    def _compute_evaluation_state(self):
        for rec in self:
            if rec.purchase_order_evaluation_ids:
                evaluation_state = 'success'
                for evaluation in rec.purchase_order_evaluation_ids:
                    if evaluation.total_score < evaluation.min_score:
                        evaluation_state = 'fail'
                        break
                rec.evaluation_state = evaluation_state

    def get_procurment_approval(self):
        return self.env['approval.request'].search(
            [('product_line_ids.purchase_order_line_id', 'in', self.order_line.ids)])

    def create_variation_order(self):
        variant_order_id = self.copy()
        self.variant_order_id = variant_order_id.id
        self_comp = variant_order_id.with_company(variant_order_id.company_id)
        # sequence_name = self_comp.env['ir.sequence'].next_by_code('variant.purchase.order',
        #                                                           sequence_date=variant_order_id.date_order) or ''
        # name = self.name + '-' + sequence_name
        variant_order_id.sudo().write({'state': 'draft', 'is_variant_order': True, 'origin': self.name})

    def action_evaluation(self):
        action = self.env.ref('purchase.purchase_form_action').read()[0]
        domain = action.get('domain')
        if domain:
            domain = ast.literal_eval(domain)
            domain.append(('partner_id', '=', self.partner_id.id))
        else:
            domain = [('partner_id', '=', self.partner_id.id)]
        action.update({'domain': domain})
        return action

    def button_confirm(self):
        object = super(PurchaseOrder, self).button_confirm()
        self.write({
            'approved_by': self.env.user.id
        })
        return object

    def _compute_rfq_terms_id(self):
        rfq_terms = self.env['rfq.terms'].search([('is_used', '=', True)])
        for rec in self:
            rec.rfq_terms_id = rfq_terms[0].id if rfq_terms else False

    def action_rfq_send(self):
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            if self.env.context.get('send_rfq', False):
                template_id = ir_model_data._xmlid_lookup('taqat_purchase_extended.email_template_edi_purchase')[2]
            else:
                template_id = ir_model_data._xmlid_lookup('taqat_purchase_extended.email_template_edi_purchase_done')[2]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data._xmlid_lookup('mail.email_compose_message_wizard_form')[2]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'purchase.order',
            'active_model': 'purchase.order',
            'active_id': self.ids[0],
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'custom_layout': "mail.mail_notification_paynow",
            'force_email': True,
            'mark_rfq_as_sent': True,
        })

        # In the case of a RFQ or a PO, we want the "View..." button in line with the state of the
        # object. Therefore, we pass the model description in the context, in the language in which
        # the template is rendered.
        lang = self.env.context.get('lang')
        if {'default_template_id', 'default_model', 'default_res_id'} <= ctx.keys():
            template = self.env['mail.template'].browse(ctx['default_template_id'])
            if template and template.lang:
                lang = template._render_lang([ctx['default_res_id']])[ctx['default_res_id']]

        self = self.with_context(lang=lang)
        if self.state in ['draft', 'sent']:
            ctx['model_description'] = _('Request for Quotation')
        else:
            ctx['model_description'] = _('Purchase Order')

        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    def write(self, vals):

        if 'purchase_order_evaluation_ids' in vals:
            message = f'{self.env.user.name} '
            lines = vals['purchase_order_evaluation_ids']
            for value in lines:
                if value[2]:
                    field = getattr(self, 'purchase_order_evaluation_ids')
                    selected_line = field.filtered(lambda x: x.id == value[1])
                    if selected_line:
                        current_value_model = selected_line.__class__.__name__
                        for k, v in value[2].items():
                            current_label = selected_line.fields_get().get(k).get('string')
                        old_value = getattr(selected_line, k)
                        new_value = v
                        print('old_value', old_value, 'new_value', new_value)
                        message += f'{current_label} --> {old_value} to --> {new_value}\n'
                    elif value[0] == 0:
                        message += "New Line added with values:"
                        for k, v in value[2].items():
                            label = field.fields_get().get(k).get('string')
                        message += f'{label} --> {v}.\n'
                    self.message_post(body=message)

        return super(PurchaseOrder, self).write(vals)

    def get_approval_request(self):
        self.ensure_one()
        product_approval_lines = self.env['approval.product.line'].sudo().search([
            ('purchase_order_line_id', 'in', self.order_line.ids)
        ])
        print("product_approval_lines ", product_approval_lines)
        approval_request = product_approval_lines.mapped('approval_request_id')
        approval_request = approval_request and approval_request[0]
        return approval_request

    def print_quotation(self):
        self.write({'state': "sent"})
        return self.env.ref('taqat_purchase_extended.purchase_order_approval_template').report_action(self)