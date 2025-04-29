# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date


class EmployeeTransferConfig(models.Model):
    _name = 'ebs.payroll.emp.transfer.config'
    _description = 'EBS Payroll Employee Expense Config'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee',string="Employee",required=1)
    line_ids = fields.One2many('ebs.payroll.emp.transfer.config.lines','transfer_config_id',string="Config Lines")


class EmployeeTransferConfigLines(models.Model):
    _name = 'ebs.payroll.emp.transfer.config.lines'
    _description = 'EBS Payroll Employee Expense Config Lines'

    transfer_config_id = fields.Many2one('ebs.payroll.emp.transfer.config',string="Config Id")
    company_id = fields.Many2one('res.company',string="Company",required=1)
    percentage = fields.Float('Percentage',required=1)


