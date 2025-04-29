# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class WageType(models.Model):
    _name = 'ebspayroll.wage.type'
    _description = 'Wage Type'

    value = fields.Char(
        string='Value',
        required=True)
    name = fields.Char(
        string='Name',
        required=True)
    wage_type = fields.Selection(
        [('monthly', 'Monthly Fixed Wage'),
         ('daily', 'Daily Wage'),
         ('hourly', 'Hourly Wage')], default='monthly',
        required=True)
