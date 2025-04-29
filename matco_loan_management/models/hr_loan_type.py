# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrLoanType(models.Model):
    _name = 'hr.loan.type'
    _description = "Loan Type"

    name = fields.Char(string="Loan Type Name", readonly=False, help="Name of the loan Type")
    marriage_loan = fields.Boolean(string="Marriage Loan", default=False)
    car_loan = fields.Boolean(string="Car Loan", default=False)
    personal_loan = fields.Boolean(string="Personal Loan", default=False)
    good_will_loan = fields.Boolean(string="Good Will Loan", default=False)
    purpose_code = fields.Char(string="Purpose Code")
    num_of_installments = fields.Integer(string="(Qatar) Numbers of Installments", default=1)
    non_qatar_num_of_installments = fields.Integer(string="(Non Qatar) Numbers of Installments", default=1)
    sponsor_ids = fields.Many2many(comodel_name="hr.employee.sponsor", string="Sponsorship")
    allowed_for = fields.Selection([
        ('qatari', 'Qatari'),
        ('not_qatari', 'Not Qatari'),
        ('both', 'Both')
    ], default='qatari', required=True, string="Allowed For")
    years_to_pass = fields.Integer(string="Years To Pass")
    loan_amount_configuration = fields.Selection([
        ('m_salary_element', 'Multiplier, salary element'),
        ('max_amount', 'Max Amount'),
    ], string='Amount Configuration')

    multiplier_amount = fields.Integer(string="Multiplier Amount")
    max_amount = fields.Float(string="Amount")

    @api.constrains("loan_amount_configuration", 'max_amount')
    def _check_loan_max_amount(self):
        for record in self:
            if record.loan_amount_configuration == 'max_amount'\
                    and record.max_amount <= 0:
                raise ValidationError(_("Amount should be greater than zero"))
