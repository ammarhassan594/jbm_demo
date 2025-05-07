from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    state = fields.Selection(selection_add=[('draft', 'Pending'),
                                            ('sent', 'Sent'),
                                            ('to approve', 'To Approve'),
                                            ('purchase', 'Approved'),
                                            ('rejected', 'Rejected'),
                                            ('done', 'Locked'),
                                            ('cancel', 'Cancelled')])
    department_id = fields.Many2one('hr.department', string="Department")
    is_active_budget_preparation = fields.Boolean(related="company_id.is_active_budget_preparation",
                                                  string="is active budget preparation")
    phone_number = fields.Char(string="Phone Representative")

    def action_rejected(self):
        self.state = 'rejected'

    def button_approve(self, force=False):
        coo_approval_needed = False
        finance_approval_needed = False
        for line in self.order_line:
            if line.is_finanace_approval_needed and not finance_approval_needed:
                finance_approval_needed = True
            if line.is_coo_approval_needed and not coo_approval_needed:
                coo_approval_needed = True
        if (not coo_approval_needed and not finance_approval_needed) or force:

            return super(PurchaseOrder, self).button_approve(force=force)
        else:
            raise ValidationError(_("Please Approve the line first."))
        return {}

    def button_confirm(self):
        for order in self:
            product_ids = order.order_line.mapped('product_id')
            if product_ids and order.company_id.is_active_budget:
                budget_lines = self.env['crossovered.budget.lines']
                for product_id in product_ids:
                    line = order.order_line.filtered(lambda s: s.product_id == product_id)
                    budgetory_positions = self.env['account.budget.post'].sudo().search([('account_ids', 'in', [
                        product_id.property_account_expense_id.id or product_id.categ_id.property_account_expense_categ_id.id])])
                    if not budgetory_positions and order.company_id.is_active_budget:
                        raise UserError(
                            _("Chart of account is not link to any budgetory position for the product."))
                    domain = [
                        ('general_budget_id', 'in', budgetory_positions.ids),
                        ('date_from', '<=', order.date_order),
                        ('date_to', '>=', order.date_order),
                        ('crossovered_budget_id.state', '=', 'validate'),
                        ('company_ids', 'in', order.company_id.id)
                    ]
                    if line.account_analytic_id:
                        domain.append(('analytic_account_id', '=', line.account_analytic_id.id))
                    current_budget_line = self.env['crossovered.budget.lines'].sudo().search(domain)
                    if current_budget_line not in budget_lines:
                        budget_lines += current_budget_line
                if not budget_lines and order.company_id.is_active_budget:
                    raise UserError(
                        _("Budget line is not available for the order."))
                budget_amount = sum(budget_lines.mapped('planned_amount'))
                existing_purchase_orders = self.env['purchase.order']
                for budget_line in budget_lines:
                    date_from = datetime.combine(budget_line.date_from, datetime.min.time())
                    date_to = datetime.combine(budget_line.date_to, datetime.max.time())
                    existing_purchase_orders += self.search([('date_order', '<=', date_to),
                                                             ('date_order', '>=', date_from),
                                                             ('state', 'in', ['purchase', 'done', 'to approve'])])
                if existing_purchase_orders:
                    budget_amount = budget_amount - sum(existing_purchase_orders.mapped('amount_total'))
                if order.amount_total > budget_amount:
                    raise UserError(
                        _("Order amount is more than budget amount."))
            if product_ids and order.company_id.is_active_budget_preparation:
                budget_preparation_ids = self.env['budget.preparation'].sudo().search(
                    [('from_date', '<=', order.date_order.date()),
                     ('to_date', '>=', order.date_order.date()),
                     ('department', '=', self.department_id.id),
                     ('state', '=', 'validate')])
                if budget_preparation_ids:
                    current_budget_line = self.env['budget.preparation.line']
                    for product_id in product_ids:
                        line = order.order_line.filtered(lambda s: s.product_id == product_id)
                        budgetory_positions = self.env['account.budget.post'].sudo().search([('account_ids', 'in', [
                            product_id.property_account_expense_id.id or product_id.categ_id.property_account_expense_categ_id.id])])
                        if not budgetory_positions and order.company_id.is_active_budget:
                            raise UserError(
                                _("Chart of account is not link to any budget position for the product."))
                        domain = [
                            ('budget_position_id', 'in', budgetory_positions.ids),
                            ('budget_preparation_id', 'in', budget_preparation_ids.ids),
                            ('company_ids', 'in', order.company_id.id)
                        ]
                        if line.account_analytic_id:
                            domain.append(('analytic_account_id', '=', line.account_analytic_id.id))
                        current_budget_line = self.env['budget.preparation.line'].sudo().search(domain)
                    if not current_budget_line and order.company_id.is_active_budget_preparation:
                        raise UserError(
                            _("Budget preparation line is not available for the order."))
                    budget_amount = sum(current_budget_line.mapped('approved_amount'))
                    existing_purchase_orders = self.env['purchase.order']
                    for budget_line in budget_lines:
                        date_from = datetime.combine(budget_line.date_from, datetime.min.time())
                        date_to = datetime.combine(budget_line.date_to, datetime.max.time())
                        existing_purchase_orders += self.search([('date_order', '<=', date_to),
                                                                 ('date_order', '>=', date_from),
                                                                 ('state', 'in', ['purchase', 'done', 'to approve'])])
                    if existing_purchase_orders:
                        budget_amount = budget_amount - sum(existing_purchase_orders.mapped('amount_total'))
                    if order.amount_total > budget_amount:
                        raise UserError(
                            _("Order amount is more than budget preparation amount."))
            if order.state not in ['draft', 'sent']:
                continue
            order._add_supplier_to_product()

            coo_approval_needed = False
            finance_approval_needed = False
            for line in self.order_line:
                if line.is_finanace_approval_needed and not finance_approval_needed:
                    finance_approval_needed = True
                if line.is_coo_approval_needed and not coo_approval_needed:
                    coo_approval_needed = True
            if not finance_approval_needed and not coo_approval_needed:
                order.button_approve(force=True)
            #elif finance_approval_needed:
                #raise ValidationError(_("Finanace Manager approval needed."))
            if not finance_approval_needed and coo_approval_needed:
                order.write({'state': 'to approve'})
            #elif finance_approval_needed and coo_approval_needed:
                #raise ValidationError(_("Finanace Manager approval needed."))
        return True
