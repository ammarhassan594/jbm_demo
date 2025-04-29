# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class Districts(models.Model):
    _name = 'ebspayroll.districts'
    _description = 'Districts'

    value = fields.Char(
        string='Value',
        required=True)
    name = fields.Char(
        string='Name',
        required=True)
    governorate = fields.Many2one(
        comodel_name='ebspayroll.governorate',
        string='Governorate',
        required=True)

    _sql_constraints = [
        ('value', 'unique(value)', _('Value field must be unique')),
        ('name', 'unique(name)', _('Name field must be unique'))
    ]
