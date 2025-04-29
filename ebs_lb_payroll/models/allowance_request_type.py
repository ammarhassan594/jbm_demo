# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, date
from dateutil.relativedelta import relativedelta


class AllowanceRequestType(models.Model):
    _name = 'ebs.payroll.allowance.request.type'
    _description = 'Allowance Request Type'

    name = fields.Char(
        string='Name',
        required=True)

