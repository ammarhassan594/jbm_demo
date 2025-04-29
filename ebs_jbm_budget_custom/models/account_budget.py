from odoo import models, fields, api,_
from odoo.exceptions import ValidationError


class Budget(models.Model):
    _inherit = 'crossovered.budget'


    @api.constrains('date_from', 'date_to')
    def _validate_date_interval(self):
        for rec in self:
            date_from = rec.date_from
            date_to = rec.date_to
            if all((date_from, date_to)):
                if date_from.year != date_to.year:
                    raise ValidationError(_("The Interval period has to be in the same year"))


    @api.onchange('crossovered_budget_line', 'crossovered_budget_line.general_budget_id')
    def _onchange_budget_position(self):
        lines = self.crossovered_budget_line
        if lines:
            budget_preparation = self.env['budget.preparation'].search([]).filtered(
                lambda x: x.from_date and self.date_from and
                          x.from_date.year == self.date_from.year)
            for line in lines:
                amount_lst = budget_preparation.mapped('budget_preparation_lines').filtered(lambda x: x.budget_position_id == line.general_budget_id).mapped('approved_amount')
                if amount_lst:
                    line.planned_amount = sum(amount_lst)

# class BudgetLines(models.Model):
#     _inherit = 'crossovered.budget.lines'
#
#
#     @api.model
#     def create(self, vals):
#         obj = super(BudgetLines, self).create(vals)
#         budget_preparation = obj.env['budget.preparation'].search([]).filtered(
#             lambda x: x.from_date.year == obj.crossovered_budget_id.date_from.year)
#         if budget_preparation:
#             amount_lst = budget_preparation.mapped('budget_preparation_lines').filtered(lambda x: x.budget_position_id == obj.general_budget_id).mapped('approved_amount')
#             if amount_lst:
#                 obj.planned_amount = sum(amount_lst)
#         return obj




