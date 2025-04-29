# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
import json
class HrLoanType(models.Model):
    _inherit = 'hr.loan.type'

    show_in_loan = fields.Boolean(string="Show In Loan", )

class HrLoan(models.Model):
    _inherit = 'hr.loan'

    # loan_type = fields.Many2one(domain=[('show_in_loan', '=', True)])
    loan_type_domain = fields.Char(compute="_get_loan_type_domain", readonly=True)

    @api.depends('employee_id')
    def _get_loan_type_domain(self):
        for rec in self:
            if rec.employee_id:
                if rec.employee_id.collaborator:
                    rec.loan_type_domain = json.dumps([('id', '=', False)])
                else:
                    rec.loan_type_domain = json.dumps([('show_in_loan', '=', True)])
            else:
                rec.loan_type_domain = json.dumps([('id', '=', False)])

    def restart_loan(self, restart_date):
        """
            Restarts the loan to the specified restart date.

            Args:
                restart_date (datetime.date): The restart date.

            Raises:
                ValidationError: If restart_date is not provided or
                                 If the loan lines are not found.
            Returns:
                None
            """
        self.ensure_one()
        if not restart_date:
            raise ValidationError(_("Restart date must be provided"))

        if not self.loan_lines:
            raise ValidationError(_("Installment lines must be found"))

        shift_loans = self.loan_lines.filtered(
            lambda l: (l.date < restart_date or restart_date <= l.date) and not l.paid). \
            sorted(lambda s: s.date)
        next_date = restart_date
        for loan_line in shift_loans:
            loan_line.write({
                'date': next_date
            })
            next_date += relativedelta(months=1)

