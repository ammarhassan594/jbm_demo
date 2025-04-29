# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class TaxRules(models.Model):
    _name = 'ebspayroll.tax.rules'
    _description = 'Tax Rules'

    name = fields.Char(
        string='Name',
        required=True)
    currency = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        required=True
        , default=99)
    frequency = fields.Selection(
        string='Frequency',
        selection=[('Daily', 'Daily'),
                   ('Weekly', 'Weekly'),
                   ('Monthly', 'Monthly'),
                   ('Yearly', 'Yearly')],
        required=True,
        default='Monthly')
    fromdate = fields.Date(
        string='From Date',
        required=True)

    todate = fields.Date(
        string='To Date',
        required=True)
    description = fields.Text(
        string="Description",
        required=False)
    type = fields.Selection(
        string='Type',
        selection=[('T', 'Tax'),
                   ('TR', 'Tax Reduction'), ],
        required=True,
        default='T')

    tax_rule_lines = fields.One2many(
        comodel_name='ebspayroll.tax.rules.lines',
        inverse_name='tax_rule',
        string='Tax Rule Lines',
        required=False)
    tax_rule_reductions = fields.One2many(
        comodel_name='ebspayroll.tax.rules.reductions',
        inverse_name='tax_rule',
        string='Tax Rule Reductions',
        required=False)


class TaxRulesLines(models.Model):
    _name = 'ebspayroll.tax.rules.lines'
    _description = 'Tax Rules Lines'

    from_amount = fields.Float(
        string='From Amount',
        required=True)
    to_amount = fields.Float(
        string='To Amount',
        required=False)
    percentage = fields.Float(
        string='Percentage',
        required=True)
    tax_rule = fields.Many2one(
        comodel_name='ebspayroll.tax.rules',
        string='Tax Rule',
        required=True)


class TaxRulesReduction(models.Model):
    _name = 'ebspayroll.tax.rules.reductions'
    _description = 'Tax Rules Reductions'

    main_amount = fields.Float(
        string='Main Amount',
        required=True)
    spouse_amount = fields.Float(
        string='Spouse Amount',
        required=True)
    child_amount = fields.Float(
        string='Child Amount',
        required=True)
    # gender = fields.Selection(
    #     string='Gender',
    #     selection=[('Male', 'Male'),
    #                ('Female', 'Female'), ],
    #     required=False, )


    # family_situation = fields.Selection(
    #     string='Family Situation',
    #     selection=[('W', 'Widowed'),
    #                ('S', 'Single'),
    #                ('M', 'Married'),
    #                ('D', 'Divorced'), ],
    #     required=False, )
    tax_rule = fields.Many2one(
        comodel_name='ebspayroll.tax.rules',
        string='Tax Rule',
        required=True)
