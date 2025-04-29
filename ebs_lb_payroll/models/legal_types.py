# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class LegalTypes(models.Model):
    _name = 'ebspayroll.legal.types'
    _description = 'Legal Types'

    value = fields.Char(
        string='Value',
        required=True)
    name = fields.Char(
        string='Name',
        required=True)

    _sql_constraints = [
        ('value', 'unique(value)', _('Value field must be unique')),
        ('name', 'unique(name)', _('Name field must be unique'))
    ]
