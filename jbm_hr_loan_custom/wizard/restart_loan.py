# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class RestartLoanWizard(models.TransientModel):
    _name = 'restart.loan'
    _description = 'Restart loan wizard for stopped a loan for period and restart again'

    restart_loan_date = fields.Date(default=lambda self: fields.Date.context_today(self),
                                    required=True)
    loan_id = fields.Many2one('hr.loan')

    def _check_loan(self, loan):
        """Check if the loan has loan lines and selected date between loan dates lines."""
        assert loan is not False, 'Must be provided a loan'
        # assert selected_date is not False, 'Must be provided a restart loan date'
        if not self.restart_loan_date:
            raise UserError(_('Must be provided a restart loan date'))
        if not loan.loan_lines:
            raise UserError(_('Must be found instalments on this loan'))
        first_installment, last_installment = (loan.loan_lines[0], loan.loan_lines[-1])
        if not (first_installment.date <= self.restart_loan_date <= last_installment.date):
            raise UserError(_(f'Must be selected date between {first_installment.date}, {last_installment.date}'))
        selected_loan_line = loan.loan_lines.filtered(lambda l: l.date.month == self.restart_loan_date.month and
                                                      l.date.year == self.restart_loan_date.year)
        if selected_loan_line.paid:
            raise UserError(_(f'The selected date has a paid loan on date {selected_loan_line.date}'))

    def approve_stop_loan(self):
        assert self.restart_loan_date is not False, "Must be provided restart loan date"
        if self._context.get('active_id') and self._context.get('active_model') == 'hr.loan':
            loan = self.env['hr.loan'].browse(self._context.get('active_id')) or self.loan_id
            self._check_loan(loan)
            loan.restart_loan(self.restart_loan_date)
        return True

    @api.model
    def default_get(self, fields):
        res = super(RestartLoanWizard, self).default_get(fields)
        if self._context.get('active_id') and self._context.get('active_model') == 'hr.loan':
            loan = self.env['hr.loan'].browse(self._context.get('active_id'))
            if loan:
                res.update({'loan_id': loan.id})

        return res
