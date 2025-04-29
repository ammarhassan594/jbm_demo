from odoo import models, fields, api, _


class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    @api.model
    def default_get(self, fields):
        res = super(ProductTemplateInherit, self).default_get(fields)
        product_income = self.env['account.account']
        product_expense = self.env['account.account']
        if res.get('detailed_type') == 'product':
            product_income = self.env.company.product_storable_account_income_id
            product_expense = self.env.company.product_storable_account_expense_id
        if res.get('detailed_type') == 'service':
            product_income = self.env.company.product_service_account_income_id
            product_expense = self.env.company.product_service_account_expense_id
        if res.get('detailed_type') == 'consu':
            product_income = self.env.company.product_cons_account_income_id
            product_expense = self.env.company.product_cons_account_expense_id

        res['property_account_income_id'] = product_income.id
        res['property_account_expense_id'] = product_expense.id
        return res

    @api.onchange('detailed_type')
    def get_product_income_expense_account(self):
        product_income = self.env['account.account']
        product_expense = self.env['account.account']
        if self.detailed_type == 'product':
            product_income = self.env.company.product_storable_account_income_id
            product_expense = self.env.company.product_storable_account_expense_id
        if self.detailed_type == 'service':
            product_income = self.env.company.product_service_account_income_id
            product_expense = self.env.company.product_service_account_expense_id
        if self.detailed_type == 'consu':
            product_income = self.env.company.product_cons_account_income_id
            product_expense = self.env.company.product_cons_account_expense_id

        self.property_account_income_id = product_income.id
        self.property_account_expense_id = product_expense.id
