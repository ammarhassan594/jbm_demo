# -*- coding: utf-8 -*-

from odoo import models, fields, api,_


class TransportationRuleLines(models.Model):
    _name = 'ebspayroll.transportation.rule.lines'
    _description = 'Transportation Rule Lines'

    transportation_rule_id = fields.Integer(
        string='Transportation Rule',
        required=True)

    employee = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        required=True)

    days = fields.Integer(
        string='Days',
        required=True)

    amount = fields.Float(
        string='Amount',
        required=True)

    _sql_constraints = [
        ('transportation_line_emp_unique', 'unique(employee,transportation_rule_id)', _("Employee already exists"))
    ]