from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Purchase_Order_Line(models.Model):
    _inherit = 'purchase.order.line'

    def _compute_tax_id(self):
        for line in self:
            if line.order_id.partner_id.vat and line.order_id.company_id.tin_tax_id:
                line.taxes_id = [(6, 0, [line.company_id.tin_tax_id.id])]
            else:
                fpos = line.order_id.fiscal_position_id or \
                       line.order_id.partner_id.with_company(line.company_id.id).\
                           property_account_position_id
                # If company_id is set, always filter taxes by the company
                taxes = line.product_id.supplier_taxes_id.filtered(
                    lambda r: not line.company_id or r.company_id == line.company_id)
                line.taxes_id = fpos.map_tax(taxes, line.product_id, line.order_id.partner_id) if fpos else taxes

    is_finanace_approval_needed = fields.Boolean()
    is_coo_approval_needed = fields.Boolean()

    def approve_finance(self):
        for rec in self:
            rec.is_finanace_approval_needed = False

    def approve_coo(self):
        for rec in self:
            rec.is_coo_approval_needed = False

    @api.constrains('product_id')
    def _check_product_budget(self):
        for rec in self:
            if not (rec.product_id.property_account_expense_id or (
                    rec.product_id.categ_id and rec.product_id.categ_id.property_account_expense_categ_id)):
                raise UserError(
                    _("Please configure Chart of Accounts in the expense account of the %s or to product category." % rec.product_id.name))

            budgetory_positions = rec.env['account.budget.post'].sudo().search([('account_ids', 'in', [
                rec.product_id.property_account_expense_id.id or rec.product_id.categ_id.property_account_expense_categ_id.id])])
            if not budgetory_positions and rec.company_id.is_active_budget == True:
                raise UserError(
                    _("Chart of account is not link to any budgetory position for the %s." % rec.product_id.name))
            domain = [
                ('general_budget_id', 'in', budgetory_positions.ids),
                ('date_from', '<=', rec.order_id.date_order),
                ('date_to', '>=', rec.order_id.date_order),
                ('crossovered_budget_id.state', '=', 'validate'),
                ('company_ids', 'in', rec.order_id.company_id.id)
            ]
            if rec.account_analytic_id:
                domain.append(('analytic_account_id', '=', rec.account_analytic_id.id))
            budget_lines = rec.env['crossovered.budget.lines'].sudo().search(domain, limit=1)
            if not budget_lines and rec.company_id.is_active_budget == True:
                raise UserError(_("There is no budget defined for the %s." % rec.product_id.name))

    @api.onchange('price_subtotal')
    def _onchange_price_subtotal_approval_required(self):
        if self.product_id.property_account_expense_id or (
                self.product_id.categ_id and self.product_id.categ_id.property_account_expense_categ_id):
            budgetory_positions = self.env['account.budget.post'].sudo().search([('account_ids', 'in', [
                self.product_id.property_account_expense_id.id or self.product_id.categ_id.property_account_expense_categ_id.id])])
            if budgetory_positions:
                budget_lines = self.env['crossovered.budget.lines'].sudo().search([
                    ('general_budget_id', 'in', budgetory_positions.ids),
                    ('date_from', '<=', self.order_id.date_order),
                    ('date_to', '>=', self.order_id.date_order),
                    ('crossovered_budget_id.state', '=', 'validate'),
                    ('company_ids', '=', self.order_id.company_id.id)
                ], limit=1)
                if budget_lines:
                    total_reserve_amount = budget_lines.amount_of_reservation + self.price_subtotal
                    if budget_lines.planned_amount >= total_reserve_amount:
                        self.is_finanace_approval_needed = False
                        self.is_coo_approval_needed = False
                    elif budget_lines.planned_amount < total_reserve_amount:
                        final_planned_amount = budget_lines.planned_amount + (
                                budget_lines.planned_amount * budget_lines.exceed_margin_finance) / 100
                        if final_planned_amount >= total_reserve_amount:
                            self.is_finanace_approval_needed = True
                            self.is_coo_approval_needed = False
                        else:
                            self.is_finanace_approval_needed = True
                            self.is_coo_approval_needed = True
                    else:
                        self.is_finanace_approval_needed = False
                        self.is_coo_approval_needed = False
                else:
                    self.is_finanace_approval_needed = False
                    self.is_coo_approval_needed = False
            else:
                self.is_finanace_approval_needed = False
                self.is_coo_approval_needed = False
        else:
            self.is_finanace_approval_needed = False
            self.is_coo_approval_needed = False
