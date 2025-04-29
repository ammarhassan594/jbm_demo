from odoo import models, fields, api, _


class ResConfigSettingInherit(models.TransientModel):
    _inherit = 'res.config.settings'

    is_active_budget = fields.Boolean("Active Budget", related="company_id.is_active_budget", readonly=False)
    product_service_account_income_id = fields.Many2one("account.account", related="company_id.product_service_account_income_id", readonly=False)
    product_service_account_expense_id = fields.Many2one("account.account", related="company_id.product_service_account_expense_id", readonly=False)
    product_storable_account_income_id = fields.Many2one("account.account", related="company_id.product_storable_account_income_id", readonly=False)
    product_storable_account_expense_id = fields.Many2one("account.account", related="company_id.product_storable_account_expense_id", readonly=False)
    product_cons_account_income_id = fields.Many2one("account.account", related="company_id.product_cons_account_income_id", readonly=False)
    product_cons_account_expense_id = fields.Many2one("account.account", related="company_id.product_cons_account_expense_id", readonly=False)
    is_active_budget_preparation = fields.Boolean("Active Budget Preparation", related="company_id.is_active_budget_preparation", readonly=False)


class ResCompanyInherit(models.Model):
    _inherit = 'res.company'

    is_active_budget = fields.Boolean("Active Budget")
    product_service_account_income_id = fields.Many2one("account.account",)
    product_service_account_expense_id = fields.Many2one("account.account")
    product_storable_account_income_id = fields.Many2one("account.account")
    product_storable_account_expense_id = fields.Many2one("account.account")
    product_cons_account_income_id = fields.Many2one("account.account")
    product_cons_account_expense_id = fields.Many2one("account.account")
    is_active_budget_preparation = fields.Boolean("Active Budget Preparation")
