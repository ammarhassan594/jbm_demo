# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date


class HRJobCustom(models.Model):
    _inherit = 'hr.job'

    # payroll_grade = fields.Selection(
    #     string='Payroll Grade',
    #     selection=[('1', 'Grade 1'),
    #                ('2', 'Grade 2'), ('3', 'Grade 3')],
    #     required=False, )
