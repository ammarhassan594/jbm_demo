# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date


class EbsPayrollExpenceTransfer(models.Model):
    _name = 'ebs.payroll.expense.transfer'
    _description = 'EBS Payroll Expense Transfer'
    _rec_name = 'name'

    name = fields.Char(string='Name',required=1)
    from_date = fields.Date(string='From Date',required=1)
    to_date = fields.Date(string='To Date',required=1)
    transfer_lines_ids = fields.One2many('ebs.payroll.expense.transfer.lines','expense_transfer_id',string="Transfer Lines")


class EbsPayrollExpenceTransferLine(models.Model):
    _name = 'ebs.payroll.expense.transfer.lines'
    _description = 'EBS Payroll Expense Transfer Lines '

    expense_transfer_id = fields.Many2one('ebs.payroll.expense.transfer',string="Payroll Expense Transfer")
    company_id = fields.Many2one('res.company',string="Company",required=1)
    from_account_ids = fields.Many2many('account.account',string="From Account",required=1)
    close_account_id = fields.Many2one('account.account',string="Close Account",required=1)
    main_expense_account = fields.Many2one('account.account',string="Main Expense Account",required=1)
    journal_id = fields.Many2one('account.journal',string="Journal")








