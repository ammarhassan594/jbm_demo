# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, Command, _
from odoo.exceptions import ValidationError
import datetime

_logger = logging.getLogger(__name__)


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    is_financial_approver = fields.Boolean(string="Is financial Approver",
                                           compute="compute_is_financial_approver")
    approval_product_type = fields.Selection([
        ('', ''),
        ('consumable_storable', 'Consumable/Storable'),
        ('service', 'Service'),
        ('consumable_storable_service', 'Consumable/Storable/Service')
    ], compute="_get_approval_type", defaul="")

    purchases_total_amount = fields.Float(compute="_compute_purchase_order_amount")
    stock_ids = fields.One2many(comodel_name="stock.picking", inverse_name="material_request_id", string="Stock")
    stock_picking_count = fields.Integer(compute='_get_stock_picking_count')
    purchase_order_ids = fields.One2many(comodel_name="purchase.order", inverse_name="approval_request_id",
                                         string="Purchase Orders")
    product_line_ids = fields.One2many(copy=True)

    @api.depends('purchase_order_ids')
    def _compute_purchase_order_count(self):
        for request in self:
            request.purchase_order_count = len(request.purchase_order_ids)

    @api.depends('product_line_ids.purchase_order_line_id')
    def _compute_purchase_order_amount(self):
        for request in self:
            purchase_lines = request.product_line_ids.filtered(
                lambda line: not line.is_available).purchase_order_line_id
            request.purchases_total_amount = sum(purchase_lines.mapped('price_total'))

    @api.depends('product_line_ids')
    @api.onchange('product_line_ids')
    def _get_approval_type(self):
        for record in self:
            if record.product_line_ids:
                type = set(record.product_line_ids.mapped('product_id.detailed_type'))
                if type:
                    if len(type) >= 3:
                        record.approval_product_type = 'consumable_storable_service'
                    else:
                        if len(type) == 2:
                            if ('consu' in type and 'service' in type) or ('product' in type and 'service' in type):
                                record.approval_product_type = 'consumable_storable_service'
                            elif 'consu' in type and 'product' in type:
                                record.approval_product_type = 'consumable_storable'
                        elif len(type) == 1:
                            if 'consu' in type or 'product' in type:
                                record.approval_product_type = 'consumable_storable'
                            elif 'service' in type:
                                record.approval_product_type = 'service'
                else:
                    record.approval_product_type = ""
            else:
                record.approval_product_type = ""

    @api.depends('product_line_ids.purchase_order_line_id')
    def _get_purchase_order(self):
        for request in self:
            purchases = request.product_line_ids.purchase_order_line_id.order_id
            if purchases:
                return purchases[0]
            return False

    @api.depends('approver_ids')
    def compute_is_financial_approver(self):
        for record in self:
            is_financial_approver = False
            if record.approver_ids:
                users = record.approver_ids.mapped('user_id')
                for user in users:
                    if user.has_group('account.group_account_manager'):
                        is_financial_approver = True
            record.is_financial_approver = is_financial_approver

    def notify_correct_approver(self):
        for request in self:
            if request.request_status == 'under_approval' and \
                    not request.approver_ids.filtered(lambda line: line.status == 'pending'):
                approvers = self.mapped('approver_ids').filtered(lambda approver: approver[0].status == 'new').sorted(
                    'sequence')
                if len(approvers) > 0:
                    approvers[0].sudo()._create_activity()
                    approvers[0].sudo().write({'status': 'pending'})

    def next_approver_deligation(self, user_line):
        self.sudo()._get_user_approval_activities(user=user_line.user_id).action_feedback()
        approvers = self.mapped('approver_ids').filtered(lambda approver: approver[0].status == 'new').sorted(
            'sequence')
        if len(approvers) > 0:
            approvers[0].sudo()._create_activity()
            approvers[0].sudo().write({'status': 'pending'})

    def check_product_availability(self):
        self.ensure_one()
        if self.approval_type == 'purchase' or \
                self.category_id.approval_type == 'purchase':
            users_account_manager = self.approver_ids. \
                filtered(lambda l:
                         l.user_id.has_group('jbm_group_access_right_extended.custom_accounting_manager')
                         and l.status not in ['approved']
                         )
            command = []
            for user_line in users_account_manager:
                if user_line.status == 'pending':
                    user_line.request_id.next_approver_deligation(user_line)
                    command.append(Command.unlink(user_line.id))
                else:
                    command.append(Command.unlink(user_line.id))
            if command:
                self.sudo().approver_ids = command

    def create_stock_picking(self):
        self.ensure_one()
        if self.approval_type == 'purchase' or \
                self.category_id.approval_type == 'purchase':
            stock_obj = self.env['stock.picking']
            move_obj = self.env['stock.move']
            pick_vals = []
            # stock_id = stock_obj.sudo().create(picking_vals)
            for line in self.product_line_ids:
                picking_vals = {
                    'location_id': line.location_id.id,
                    'location_dest_id': line.dest_location_id.id,
                    'picking_type_id': line.picking_type_id.id,
                    'material_request_id': self.id,
                }
                stock_id = stock_obj.sudo().create(picking_vals)
                pick_vals.append({
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.quantity,
                    'product_uom': line.product_uom_id.id,
                    'location_id': stock_id.location_id.id,
                    'location_dest_id': stock_id.location_dest_id.id,
                    'name': line.product_id.name,
                    'picking_type_id': stock_id.picking_type_id.id,
                    'picking_id': stock_id.id,
                })
            move_obj.sudo().create(pick_vals)

    def create_update_rfq(self, purchase_orders, supplier, line):
        if purchase_orders:
            # Existing RFQ found: check if we must modify an existing
            # purchase order line or create a new one.
            purchase_line = self.env['purchase.order.line'].search([
                ('order_id', 'in', purchase_orders.ids),
                ('product_id', '=', line.product_id.id),
                ('product_uom', '=', line.product_id.uom_po_id.id),
            ], limit=1)
            purchase_order = self.env['purchase.order']
            if purchase_line:
                # Compatible po line found, only update the quantity.
                line.purchase_order_line_id = purchase_line.id
                purchase_line.product_qty += line.po_uom_qty
                purchase_order = purchase_line.order_id
            else:
                # No purchase order line found, create one.
                purchase_order = purchase_orders[0]
                po_line_vals = self.env['purchase.order.line']._prepare_purchase_order_line(
                    line.product_id,
                    line.quantity,
                    line.product_uom_id,
                    line.company_id,
                    supplier,
                    purchase_order,
                )
                new_po_line = self.env['purchase.order.line'].create(po_line_vals)
                line.purchase_order_line_id = new_po_line.id
                purchase_order.order_line = [(4, new_po_line.id)]

            # Add the request name on the purchase order `origin` field.
            new_origin = set([self.name])
            if purchase_order.origin:
                missing_origin = new_origin - set(purchase_order.origin.split(', '))
                if missing_origin:
                    purchase_order.write({'origin': purchase_order.origin + ', ' + ', '.join(missing_origin)})
            else:
                purchase_order.write({'origin': ', '.join(new_origin)})
        else:
            # No RFQ found: create a new one.
            po_vals = line.with_context(
                first_approval_request=self._context.get('first_approval_request'))._get_purchase_order_values(
                supplier.name)
            new_purchase_order = self.env['purchase.order'].create(po_vals)
            po_line_vals = self.env['purchase.order.line']._prepare_purchase_order_line(
                line.product_id,
                line.quantity,
                line.product_uom_id,
                line.company_id,
                supplier,
                new_purchase_order,
            )
            new_po_line = self.env['purchase.order.line'].create(po_line_vals)
            line.purchase_order_line_id = new_po_line.id
            new_purchase_order.order_line = [(4, new_po_line.id)]

    def action_create_purchase_orders(self):
        """ Create and/or modifier Purchase Orders. """
        self.ensure_one()
        if not self.purchase_order_ids:
            for line in self.product_line_ids.filtered(lambda product_line: not product_line.is_available):
                suppliers = line.product_id.seller_ids
                for supplier in suppliers:
                    po_domain = line._get_purchase_orders_domain(supplier.name)
                    purchase_orders = self.env['purchase.order'].search(po_domain)
                    self.create_update_rfq(purchase_orders, supplier, line)
                if not suppliers:
                    supplier = self.env['product.supplierinfo']
                    picking_type = line._get_picking_type()
                    domain = [
                        ('company_id', '=', line.company_id.id),
                        ('state', '=', 'draft'),
                        ('partner_id', '=', False),
                        ('first_approval_request', '=', True),
                        ('approval_request_id', 'in', self.ids)
                    ]
                    if picking_type:
                        domain.append(('picking_type_id', '=', picking_type.id))
                    purchase_orders = self.env['purchase.order'].search(domain)
                    self.with_context(first_approval_request=True).create_update_rfq(purchase_orders, supplier, line)
        else:
            previous_po_ids = self.purchase_order_ids.ids
            for line in self.product_line_ids.filtered(lambda product_line: not product_line.is_available):
                supplier = self.env['product.supplierinfo']
                picking_type = line._get_picking_type()
                domain = [
                    ('company_id', '=', line.company_id.id),
                    ('state', '=', 'draft'),
                    ('partner_id', '=', False),
                    ('id', 'not in', previous_po_ids),
                    ('approval_request_id', 'in', self.ids)
                ]

                #
                if picking_type:
                    domain.append(('picking_type_id', '=', picking_type.id))
                purchase_orders = self.env['purchase.order'].search(domain)
                self.with_context(first_approval_request=False).create_update_rfq(purchase_orders, supplier, line)

    def action_cancel(self):
        if self.request_status == 'approved':
            raise ValidationError(_('You can not cancel an approved request'))
        self.sudo().activity_ids.unlink()
        super(ApprovalRequest, self).action_cancel()

    def action_refuse(self):
        self.sudo().activity_ids.unlink()
        return super(ApprovalRequest, self).action_refuse()

    def get_request_responsible(self):
        responsible = []
        if self.create_uid and self.create_uid.employee_id and self.create_uid.employee_id.parent_id and self.create_uid.employee_id.parent_id.user_id:
            approvers = set(self.approver_ids.mapped('user_id'))
            if approvers and self.create_uid.employee_id.parent_id.user_id in approvers:
                request_responsible = self.approver_ids.filtered(
                    lambda rec: rec.user_id.id == self.create_uid.employee_id.parent_id.user_id.id)
                if request_responsible:
                    if request_responsible:
                        responsible.append(request_responsible.user_id.name)
                    if request_responsible.approval_date:
                        responsible.append(request_responsible.approval_date.date())
        return responsible if responsible else False

    def get_budget(self):
        budget = self.env['crossovered.budget'].search([
            ('date_from', '<=', self.date.date()),
            ('date_to', '>=', self.date.date())
        ], limit=1)
        return budget if budget else False

    def get_budget_amounts(self):
        budget = self.get_budget()
        lines = []
        if budget:
            if budget.crossovered_budget_line:
                if self.product_category_id and self.product_category_id.property_account_expense_categ_id:
                    for budget_line in budget.crossovered_budget_line:
                        if self.product_category_id.property_account_expense_categ_id in budget_line.general_budget_id.account_ids:
                            if budget_line not in lines:
                                lines.append(budget_line)
        return lines if lines else False

    def get_accounting_manager(self):
        accounting_approver = []
        if self.approver_ids:
            accounting_managers = self.approver_ids.filtered(
                lambda rec: rec.action_user_id.has_group('jbm_group_access_right_extended.custom_accounting_manager'))
            if accounting_managers:
                accounting_approver.append(accounting_managers[-1].action_user_id.name)
                if accounting_managers[-1].approval_date:
                    accounting_approver.append(accounting_managers[-1].approval_date.date())
        return accounting_approver

    def get_last_approver(self):
        last_approver = []
        if self.approver_ids:
            shared_service_manager = self.approver_ids.mapped('action_user_id'). \
                filtered(lambda u: u.has_group('jbm_group_access_right_extended.custom_group_shared_service_manager'))
            if shared_service_manager:
                last_approver.append(shared_service_manager and shared_service_manager[0].name)
                if self.approver_ids[-1].approval_date:
                    last_approver.append(self.approver_ids[-1].approval_date.date())

        return last_approver

    def action_print_material_request(self):
        return self.env.ref('ebs_jbm_approval_extend.need_request_report_action').report_action(self)

    def _get_stock_picking_count(self):
        for rec in self:
            if rec.stock_ids:
                rec.stock_picking_count = len(rec.stock_ids)
            else:
                rec.stock_picking_count = 0

    def action_open_stock_picking(self):
        self.ensure_one()
        domain = [('id', 'in', self.stock_ids.ids)]
        action = {
            'name': _('Stock Picking'),
            'view_type': 'tree',
            'view_mode': 'list,form',
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'context': self.env.context,
            'domain': domain,
        }
        return action

    def action_open_purchase_orders(self):
        action = super().action_open_purchase_orders()
        if action.get('domain'):
            action['domain'] = [('id', 'in', self.purchase_order_ids.ids)]
        return action
