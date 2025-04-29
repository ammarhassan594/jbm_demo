from odoo import models, fields, api, _

class InheritAccountBudgetPost(models.Model):
    _inherit = 'account.budget.post'

    budget_position_number = fields.Char(string="Budget Position Number")