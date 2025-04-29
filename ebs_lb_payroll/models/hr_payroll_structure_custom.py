# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date


class PayrollStructureCustom(models.Model):
    _inherit = 'hr.payroll.structure'

    # payroll_grade = fields.Selection(
    #     string='Payroll Grade',
    #     selection=[('1', 'Grade 1'),
    #                ('2', 'Grade 2'), ('3', 'Grade 3')],
    #     required=False, )
    use_worked_day_lines = fields.Boolean(default=True, help="Worked days won't be computed/displayed in payslips.",string="Attendance")
