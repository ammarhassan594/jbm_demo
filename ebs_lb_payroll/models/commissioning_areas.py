# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class CommissioningArea(models.Model):
    _name = 'ebspayroll.commissioning.area'
    _description = 'Commissioning Area'

    value = fields.Char(
        string='Value',
        required=True)
    name = fields.Char(
        string='Name',
        required=True)

    _sql_constraints = [
        ('value', 'unique(value)', _('Value field must be unique'))
    ]
