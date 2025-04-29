from odoo import models, fields, api, tools, _
from dateutil.relativedelta import relativedelta


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    loan_ids = fields.Many2many(comodel_name='hr.loan', string="Loans")


    def get_loan_payment(self, payslip, employee):
        amount = 0.0
        loans = self.env['hr.loan'].search([('employee_id', '=', employee.id),
                                                 ('loan_payment_date', '>=', payslip.date_from),
                                                 ('loan_payment_date', '<=', payslip.date_to),
                                                 ('state', '=', 'paid')])
        if loans:
            amount= sum(loans.mapped('loan_amount'))
        return amount
    def calculate_personal_loan_deductions(self, payslip, employee):
        amount = 0.0
        loan_type = self.env['hr.loan.type'].search([('personal_loan', '=', True)])
        loans = self.env['hr.loan.line'].search([('employee_id', '=', employee.id),
                                                 ('date', '>=', payslip.date_from),
                                                 ('date', '<=', payslip.date_to),
                                                 ('paid', '=', False),
                                                 ('loan_id.loan_type', '=', loan_type.id),
                                                 ('loan_id.state', '=', 'paid')])
        if loans:
            payslip_id = self.search([('id', '=', payslip.id)])
            for loan in loans:
                amount += loan.amount
                if payslip_id.loan_ids:
                    payslip_id.loan_ids = [(4, loan.loan_id.id)]
                else:
                    payslip_id.loan_ids = [(4, loan.loan_id.id)]
        return amount

    def calculate_car_loan_deductions(self, payslip, employee):
        amount = 0.0
        loan_type = self.env['hr.loan.type'].search([('car_loan', '=', True)])
        loans = self.env['hr.loan.line'].search([('employee_id', '=', employee.id),
                                                 ('date', '>=', payslip.date_from),
                                                 ('date', '<=', payslip.date_to),
                                                 ('paid', '=', False),
                                                 ('loan_id.loan_type', '=', loan_type.id),
                                                 ('loan_id.state', '=', 'paid')])

        if loans:
            payslip_id = self.search([('id', '=', payslip.id)])
            for loan in loans:
                amount += loan.amount
                if payslip_id.loan_ids:
                    payslip_id.loan_ids = [(4, loan.loan_id.id)]
                else:
                    payslip_id.loan_ids = [(4, loan.loan_id.id)]
        return amount

    def calculate_marriage_loan_deductions(self, payslip, employee):
        amount = 0.0
        loans_ids = []
        loan_type = self.env['hr.loan.type'].search([('marriage_loan', '=', True)])
        loans = self.env['hr.loan.line'].search([('employee_id', '=', employee.id),
                                                 ('date', '>=', payslip.date_from),
                                                 ('date', '<=', payslip.date_to),
                                                 ('paid', '=', False),
                                                 ('loan_id.loan_type', '=', loan_type.id),
                                                 ('loan_id.state', '=', 'paid')])

        if loans:
            payslip_id = self.search([('id', '=', payslip.id)])
            for loan in loans:
                amount += loan.amount
                if payslip_id.loan_ids:
                    payslip_id.loan_ids = [(4, loan.loan_id.id)]
                else:
                    payslip_id.loan_ids = [(4, loan.loan_id.id)]
        return amount

    def calculate_good_will_loan_deductions(self, payslip, employee):
        amount = 0.0
        loan_type = self.env['hr.loan.type'].search([('good_will_loan', '=', True)])
        loans = self.env['hr.loan.line'].search([('employee_id', '=', employee.id),
                                                 ('date', '>=', payslip.date_from),
                                                 ('date', '<=', payslip.date_to),
                                                 ('paid', '=', False),
                                                 ('loan_id.loan_type', '=', loan_type.id),
                                                 ('loan_id.state', '=', 'paid')])


        if loans:
            payslip_id = self.search([('id', '=', payslip.id)])
            for loan in loans:
                amount += loan.amount
                if payslip_id.loan_ids:
                    payslip_id.loan_ids = [(4, loan.loan_id.id)]
                else:
                    payslip_id.loan_ids = [(4, loan.loan_id.id)]
        return amount

    def action_payslip_done(self):
        payslip = super(HrPayslip, self).action_payslip_done()
        self._action_paid_loan()
        return payslip

    def _action_paid_loan(self):
        for rec in self:
            if rec.state == 'done':
                for loan_line in rec.loan_ids.loan_lines.filtered(lambda l: rec.date_from <= l.date <= rec.date_to):
                    loan_line.paid = True
