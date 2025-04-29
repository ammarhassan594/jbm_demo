# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class Governorate(models.Model):
    _name = 'ebspayroll.governorate'
    _description = 'Governorates'

    value = fields.Char(
        string='Value',
        required=True)
    name = fields.Char(
        string='Name',
        required=True)
    district = fields.One2many(
        comodel_name='ebspayroll.districts',
        inverse_name='governorate',
        string='Districts',
        required=False)
    _sql_constraints = [
        ('value', 'unique(value)', _('Value field must be unique')),
        ('name', 'unique(name)', _('Name field must be unique'))
    ]
