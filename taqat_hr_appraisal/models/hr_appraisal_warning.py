# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import datetime


class HrAppraisalWarningLine(models.Model):
    _name = 'hr.appraisal.warning.line'
    _description = 'Hr Appraisal Warning Line'

    hr_appraisal_id = fields.Many2one('hr.appraisal', string="Employee Appraisal")
    warning_description = fields.Char(string="Warning Description")
    warning_date = fields.Date("Warning Date")
    warning_reason = fields.Char(string="Warning Reason")
    warning_type = fields.Char(string="Warning Type")
