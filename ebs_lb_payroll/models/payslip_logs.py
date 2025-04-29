# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PayslipLogs(models.Model):
    _name = 'ebspayroll.payslip.logs'
    _description = 'Payslip Logs'

    employee = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        required=True, readonly=True)
    payslip = fields.Many2one(
        comodel_name='hr.payslip',
        string='Payslip',
        required=True, readonly=True)

    date = fields.Date(
        string='Date',
        required=True, readonly=True)

    tax_reduction_amount = fields.Float(
        string='Tax Reduction Amount',
        required=False, readonly=True)
    cnss_earnings_amount = fields.Float(
        string='CNSS Earnings Amount',
        required=False, readonly=True)
    end_service_amount = fields.Float(
        string='End of Service Amount',
        required=False, readonly=True)
    illness_motherhood_amount_user = fields.Float(
        string='Illness and Motherhood from User Amount',
        required=False, readonly=True)
    illness_motherhood_amount = fields.Float(
        string='Illness and Motherhood from Company Amount',
        required=False, readonly=True)
    family_compensation_amount = fields.Float(
        string='Family Compensation Amount',
        required=False, readonly=True)
