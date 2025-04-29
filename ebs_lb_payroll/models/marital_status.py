# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class MaritalStatus(models.Model):
    _name = 'ebspayroll.marital.status'
    _description = 'Marital Status'

    value = fields.Char(
        string='Value',
        required=True)
    name = fields.Char(
        string='Name',
        required=True)
    marital = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('widower', 'Widower'),
        ('divorced', 'Divorced')
    ], string='Marital Status', required=True)
