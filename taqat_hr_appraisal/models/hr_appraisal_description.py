# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import datetime


class HrAppraisalDescriptionLine(models.Model):
    _name = 'hr.appraisal.description.line'
    _description = 'Hr Appraisal Description Line'

    hr_appraisal_id = fields.Many2one('hr.appraisal', string="Employee Appraisal")
    description = fields.Char(string="Description")
