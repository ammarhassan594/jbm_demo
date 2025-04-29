# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class CNSS(models.Model):
    _name = 'ebspayroll.cnss'
    _description = 'CNSS'

    name = fields.Char(
        string='Name',
        required=True)
    fromdate = fields.Date(
        string='From Date',
        required=True)
    todate = fields.Date(
        string='To Date',
        required=True)
    currency = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        required=True
        , default=99)
    wife_amount = fields.Float(
        string='Wife Amount',
        required=True, default=0.0)
    child_amount = fields.Float(
        string='Child Amount',
        required=True, default=0.0)
    illness_user_limit = fields.Float(
        string='Illness and Motherhood User Limit',
        required=True, default=0.0)
    illness_user_percentage = fields.Float(
        string='Illness and Motherhood User Percentage',
        required=True, default=0.0)

    illness_limit = fields.Float(
        string='Illness and Motherhood Limit',
        required=True, default=0.0)
    illness_percentage = fields.Float(
        string='Illness and Motherhood Percentage',
        required=True, default=0.0)

    end_of_service_limit = fields.Float(
        string='End of Service Limit',
        required=True, default=0.0)
    end_of_service_percentage = fields.Float(
        string='End of Service Percentage',
        required=True, default=0.0)

    family_limit = fields.Float(
        string='Family Compensation Limit',
        required=True, default=0.0)

    family_percentage = fields.Float(
        string='Family Compensation Percentage',
        required=True, default=0.0)
