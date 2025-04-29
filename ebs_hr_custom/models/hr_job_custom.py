# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import AccessError, UserError,ValidationError


class HRJobCustom(models.Model):
    _inherit = 'hr.job'

    employee_payroll_groups = fields.Many2one(comodel_name="employee.payroll.group", string="Grade",
                                              required=False)
    job_number = fields.Char()
    job_arabic_name = fields.Char("Job Arabic Name")

