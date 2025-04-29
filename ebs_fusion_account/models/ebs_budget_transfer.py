
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class EbsBudgetTransfer(models.Model):
    _name = 'ebs.budget.transfer'
    _inherit = ['dynamic.approval.mixin', 'mail.thread', 'mail.activity.mixin']
    _state_from = ['draft']
    _state_to = ['confirmed']
    _description = 'EBS Budget Transfer'


    name = fields.Char('Transfer Reason')
    from_crossovered_budget_id = fields.Many2one('crossovered.budget', 'From Budget', required=True)
    to_crossovered_budget_id = fields.Many2one('crossovered.budget', 'To Budget', required=True)

    from_crossovered_budget_lines_id = fields.Many2one('crossovered.budget.lines', 'From Budget Lines', required=True)
    to_crossovered_budget_lines_id = fields.Many2one('crossovered.budget.lines', 'To Budget Lines', required=True)

    company_id = fields.Many2one(related='from_crossovered_budget_id.company_id', comodel_name='res.company',
        string='Company', store=True, readonly=True)

    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)

    from_amount = fields.Monetary('Planned Amount', related='from_crossovered_budget_lines_id.planned_amount', store=True)
    practical_amount = fields.Monetary('From Practical Amount', related='from_crossovered_budget_lines_id.practical_amount', store=True)
    amount_of_reservation = fields.Monetary('From Reserved Amount', related='from_crossovered_budget_lines_id.amount_of_reservation', store=True)
    remaining_budget = fields.Monetary('Remaining Amount', compute='_compute_remaining_amount')

    existing_amount = fields.Monetary('Existing Amount', related='to_crossovered_budget_lines_id.planned_amount', store=True)
    to_practical_amount = fields.Monetary('To Practical Amount', related='to_crossovered_budget_lines_id.practical_amount', store=True)
    to_amount_of_reservation = fields.Monetary('To Reserved Amount', related='to_crossovered_budget_lines_id.amount_of_reservation', store=True)
    to_amount = fields.Monetary('Amount to be Transferred', required=True)

    transfer_date = fields.Date('Transfer Date', default=fields.Datetime.now())

    state = fields.Selection([('draft', 'Draft'),('confirmed','Confirmed'), ('transferred', 'Transferred')], default='draft', tracking=True)



    @api.depends('from_amount', 'practical_amount', 'amount_of_reservation')
    def _compute_remaining_amount(self):
        for rec in self:
            rec.remaining_budget = rec.from_amount - (abs(rec.practical_amount) + rec.amount_of_reservation)


    @api.constrains('to_crossovered_budget_lines_id')
    def _check_crossovered_budget_lines_id(self):
        if self.from_crossovered_budget_id == self.to_crossovered_budget_id and self.from_crossovered_budget_lines_id == self.to_crossovered_budget_lines_id:
            raise UserError(_("You can't transfer budget to same budget line."))

    @api.constrains('to_amount')
    def _check_to_amount(self):
        if not self.to_amount:
            raise UserError(_("Please Enter To amount."))

    def action_budget_transfer(self):
        for rec in self:
            if rec.remaining_budget > 0 and rec.remaining_budget > rec.to_amount:
                rec.from_crossovered_budget_lines_id.planned_amount -= rec.to_amount
                rec.to_crossovered_budget_lines_id.planned_amount += rec.to_amount
                rec.state = 'transferred'
            else:
                raise UserError(_("You don't have enough amount to transfer."))
        return True

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirmed'
        return True