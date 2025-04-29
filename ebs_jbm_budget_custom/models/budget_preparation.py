from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class BudgetPreparation(models.Model):
    _name = 'budget.preparation'
    _inherit = ['dynamic.approval.mixin', 'mail.thread', 'mail.activity.mixin']
    _state_from = ['draft', 'confirm', 'validate1']
    _state_to = ['validate', 'cancel']
    _description = 'Budget Preparation'

    name = fields.Char(string="Name", required="1")
    description = fields.Char(string="Description")
    from_date = fields.Date(string="From Date", required="1")
    to_date = fields.Date(string="To Date", required="1")
    department = fields.Many2one('hr.department', string="Department", required="1")
    state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirm'), ('validate1', 'Approved'), ('validate', 'Validated'),
         ('cancel', 'Cancel')],
        string="Status", default="draft", required="1", tracking=True)
    user_id = fields.Many2one('res.users', string="Responsible", required="1")
    budget_preparation_lines = fields.One2many('budget.preparation.line', 'budget_preparation_id')
    is_department_manager = fields.Boolean(string="Is department manager", compute="compute_is_department_manager")
    budget_id = fields.Many2one('crossovered.budget')
    budget_state = fields.Selection(related='budget_id.state', store=True)



    def _run_final_approve_function(self):
        """ this method should be override to add custom function based on model"""
        if self._name == 'budget.preparation':
            self.action_validate()
            return True
        else:
            return True

    @api.onchange('department')
    def _onchange_department_id(self):
        if self.department:
            # Get the account_id from the department
            account_id = self.department.analytic_account_id.id
            # Update account_id in all budget_preperation_lines
            for line in self.budget_preparation_lines:
                line.analytic_account_id = account_id

    @api.onchange('budget_preparation_lines')
    def _onchange_budget_preparation_lines_id(self):
        if self.department:
            # Get the account_id from the department
            account_id = self.department.analytic_account_id.id
            # Update account_id in all budget_preperation_lines
            for line in self.budget_preparation_lines:
                line.analytic_account_id = account_id

    @api.depends('department', 'budget_preparation_lines')
    def _update_lines_account_id(self):
        if self.department:
            account_id = self.department.analytic_account_id.id
            for line in self.budget_preparation_lines:
                if not line.account_id:  # Only update if account_id is not set
                    line.analytic_account_id = account_id

    @api.constrains('from_date', 'to_date')
    def _validate_date_interval(self):
        for rec in self:
            from_date = rec.from_date
            to_date = rec.to_date
            if all((from_date, to_date)):
                if from_date.year != to_date.year:
                    raise ValidationError(_("The Interval period has to be in the same year"))

    @api.depends('department')
    def compute_is_department_manager(self):
        for record in self.sudo():
            is_department_manager = False
            if record.department and record.department.manager_id:
                if record.department.manager_id.user_id == self.env.user:
                    is_department_manager = True
            record.is_department_manager = is_department_manager

    @api.onchange('')
    def onchange_state(self):
        res = {}
        for line in self.budget_preparation_lines:
            if line.approved_amount <= 0:
                        res['warning'] = {'title': _('Warning'), 'message': _(
                            f'approved amount is zero for budget {line.budget_position_id.name}')}
                        break
        return res

    # def action_confirm(self):
    #     self.state = 'confirm'
    #
    # def action_approve(self):
    #     self.state = 'approve'

    def action_validate(self):
        # print('hello')
        # print('world')
        # self.onchange_state()
        rec = self.budget_id
        if rec:
            for line in self.budget_preparation_lines:
                rec.write({'crossovered_budget_line': [(0, 0, {'general_budget_id': line.budget_position_id.id,
                                                               'analytic_account_id': line.analytic_account_id.id,
                                                               'date_from': self.from_date, 'date_to': self.to_date, 'planned_amount': line.approved_amount,
                                                               'budget_preparation_line_id': line.id})]})
        self.state = 'validate'

    def action_cancel(self):
        self.state = 'cancel'

    def set_to_draft(self):
        self.state = 'draft'
        for line in self.budget_preparation_lines:
            crossovered_budget_line = self.budget_id.crossovered_budget_line.filtered(lambda x: x.budget_preparation_line_id.id == line.id)
            if crossovered_budget_line:
                crossovered_budget_line.unlink()

class BudgetPreparationLine(models.Model):
    _name = 'budget.preparation.line'
    _description = 'Budget Preparation Line'

    budget_preparation_id = fields.Many2one('budget.preparation')
    budget_position_id = fields.Many2one('account.budget.post', string="Budget position", required="1")
    planned_amount = fields.Monetary(string="Planned Amount", required="1")
    approved_amount = fields.Monetary(string="Approved Amount")
    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic Account')
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related="company_id.currency_id")
    company_ids = fields.Many2many('res.company', 'company_budget_preparation_rel', 'budget_preparation_id',
                                   'company_id',
                                   string='Companies', default=lambda self: self.env.company)


class CrossoveredBudgetLine(models.Model):
    _inherit = 'crossovered.budget.lines'

    budget_preparation_line_id = fields.Many2one('budget.preparation.line')
