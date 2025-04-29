from odoo import models, fields, api
import datetime


class CrossoverBudget(models.Model):
    _name = 'crossovered.budget'
    _inherit = ['crossovered.budget', 'dynamic.approval.mixin']
    _state_from = ['draft', 'committee_confirmed', 'confirm']
    _state_to = ['validate','cancel']

    company_ids = fields.Many2many('res.company', 'company_crossover_budget_rel', 'budget_id', 'company_id',
                                   'Companies', required=True,
                                   default=lambda self: self.env.company)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
        ('committee_confirmed', 'Committee Confirmed'),
        ('confirm', 'Confirmed'),
        ('validate', 'Validated'),
        ('done', 'Done')], 'Status', default='draft', index=True, required=True, readonly=True, copy=False)

    def action_budget_committee_confirm(self):
        self.write({'state': 'committee_confirmed'})

    def write(self, vals):
        res = super(CrossoverBudget, self).write(vals)
        if vals.get('state') == 'confirm':
            for rec in self:
                for line in rec.crossovered_budget_line:
                    line.monthly_budget_line_ids.unlink()
                    line.generate_monthly_line()
        return res


class CrossoverBudgetLines(models.Model):
    _inherit = 'crossovered.budget.lines'

    exceed_margin_finance = fields.Float(string='Exceed Margin Finance')
    amount_of_reservation = fields.Monetary(string='Reservation Amount', compute="_compute_reservation")
    company_ids = fields.Many2many('res.company', related='crossovered_budget_id.company_ids',
                                   string='Companies')
    account_ids = fields.Many2many('account.account', 'Accounts',
                                   related="general_budget_id.account_ids")

    budgetary_position_type = fields.Selection(related="general_budget_id.budgetary_position_type",
                                               string="Budgetary Position Type", readonly=True)
    monthly_budget_line_ids = fields.One2many('ebs.monthly.budget.line', 'budget_line_id', string="Monthly budget line")
    type_of_budget = fields.Selection(
        [('hr', 'HR'), ('marketing', 'Marketing'), ('sales', 'Sales'), ('social', 'Social Media'),
         ('legal', 'Legal'), ('account', 'Account'), ('it', 'Information Technology'), ('procurement', 'Procurement')],
        string='Type')

    def _compute_reservation(self):
        for line in self:
            if line.account_ids:
                po_line_domain = [
                    ('product_id.property_account_expense_id', 'in', line.account_ids.ids),
                    ('order_id.state', 'in', ['purchase', 'done'])
                ]
                if line.analytic_account_id:
                    po_line_domain.append(('account_analytic_id', '=', line.analytic_account_id.id))

                po_line_list = self.env['purchase.order.line'].search(po_line_domain)

                total_reservation = 0
                for po_line in po_line_list:
                    not_invoiced = po_line.product_qty - po_line.qty_invoiced
                    if not_invoiced > 0:
                        total_reservation += not_invoiced * po_line.price_unit
                    invoice_line_list = self.env['account.move.line'].search([('purchase_line_id', '=', po_line.id)])
                    for inv_line in invoice_line_list:
                        if inv_line.parent_state == 'draft':
                            total_reservation += abs(inv_line.price_subtotal)
                line.amount_of_reservation = total_reservation
            else:
                line.amount_of_reservation = 0.00

    def generate_monthly_line(self):
        rec = self
        curr_date = rec.date_from
        curr_month = rec.date_from.strftime("%m")
        segments = []
        loop = (curr_date != rec.date_to)
        days_increment = 1

        while loop:
            curr_date = rec.date_from + datetime.timedelta(days=days_increment)
            prev_month = curr_month
            curr_month = curr_date.strftime("%m")
            if prev_month != curr_month:
                if not segments:
                    start_segment = rec.date_from
                else:
                    start_segment = segments[-1][1] + datetime.timedelta(days=1)
                end_segment = curr_date - datetime.timedelta(days=1)
                segment = [start_segment, end_segment]
                segments.append(segment)
            loop = (curr_date != rec.date_to)
            days_increment += 1

        if not segments or segments[-1][1] != rec.date_to:
            if not segments:
                start_last_segment = rec.date_from
            else:
                start_last_segment = segments[-1][1] + datetime.timedelta(days=1)
            last_segment = [start_last_segment, rec.date_to]
            segments.append(last_segment)

        for i in range(len(segments)):
            segments[i][0] = segments[i][0].strftime("%Y-%m-%d")
            segments[i][1] = segments[i][1].strftime("%Y-%m-%d")

        planned_amount = self.planned_amount / len(segments)

        for seg in segments:
            vals = {
                'date_from': seg[0],
                'date_to': seg[1],
                'amount': planned_amount,
                'budget_line_id': rec.id,
            }
            self.env['ebs.monthly.budget.line'].create(vals)
        return True


class AccountBudgetPost(models.Model):
    _inherit = "account.budget.post"

    company_ids = fields.Many2many('res.company', 'company_budget_rel', 'budget_id', 'company_id', string='Companies')
    account_ids = fields.Many2many('account.account', 'account_budget_rel', 'budget_id', 'account_id', 'Accounts',
                                   domain="[('deprecated', '=', False),('company_id','in',company_ids)]")

    budgetary_position_type = fields.Selection([('expenses', 'Expenses'), ('revenues', 'Revenues')],
                                               string="Budgetary Position Type")


class EbsMonthlyBudgetLine(models.Model):
    _name = 'ebs.monthly.budget.line'
    _description = 'EBS Monthly Budget Line'

    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    amount = fields.Float(string='Planned Amount')
    actual_amount = fields.Float(string='Practical Amount', compute='compute_actual_amount')
    general_budget_id = fields.Many2one('account.budget.post', related='budget_line_id.general_budget_id',
                                        string='Budgetary Position')
    budget_line_id = fields.Many2one('crossovered.budget.lines')

    def compute_actual_amount(self):
        for line in self:
            acc_ids = line.general_budget_id.account_ids.ids
            date_to = line.date_to
            date_from = line.date_from
            if line.budget_line_id.analytic_account_id.id:
                analytic_line_obj = self.env['account.analytic.line']
                domain = [('account_id', '=', line.budget_line_id.analytic_account_id.id),
                          ('date', '>=', date_from),
                          ('date', '<=', date_to),
                          ]
                if acc_ids:
                    domain += [('general_account_id', 'in', acc_ids)]

                where_query = analytic_line_obj._where_calc(domain)
                analytic_line_obj._apply_ir_rules(where_query, 'read')
                from_clause, where_clause, where_clause_params = where_query.get_sql()
                select = "SELECT SUM(amount) from " + from_clause + " where " + where_clause

            else:
                aml_obj = self.env['account.move.line']
                domain = [('account_id', 'in',
                           line.general_budget_id.account_ids.ids),
                          ('date', '>=', date_from),
                          ('date', '<=', date_to),
                          ('move_id.state', '=', 'posted')
                          ]
                where_query = aml_obj._where_calc(domain)
                aml_obj._apply_ir_rules(where_query, 'read')
                from_clause, where_clause, where_clause_params = where_query.get_sql()
                select = "SELECT sum(credit)-sum(debit) from " + from_clause + " where " + where_clause

            self.env.cr.execute(select, where_clause_params)
            line.actual_amount = self.env.cr.fetchone()[0] or 0.0
