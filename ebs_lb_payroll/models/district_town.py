# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class DistrictTowns(models.Model):
    _name = 'ebspayroll.district.towns'
    _description = 'District Towns'

    value = fields.Char(
        string='Value',
        required=True)
    name = fields.Char(
        string='Name',
        required=True)
    district = fields.Many2one(
        comodel_name='ebspayroll.districts',
        string='District',
        required=True)

    _sql_constraints = [
        ('value', 'unique(value)', _('Value field must be unique'))
    ]
