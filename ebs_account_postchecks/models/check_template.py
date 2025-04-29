# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class CheckTemplates(models.Model):
    _name = 'ebs.checks.templates'
    _description = "Check templates"

    # logo = fields.Binary(string="Bank Logo", required=True)

    name = fields.Char(
        string='Name',
        required=True)

    bank_id = fields.Many2one(
        comodel_name='res.bank',
        string='Bank',
        required=True)

    account_for_post_checks = fields.Many2one(
        comodel_name='account.account',
        string='Bank Account for Post Checks',
        required=True)

    # padding = fields.Integer(
    #     string='Padding',
    #     required=True)
    # sequence = fields.Integer(
    #     string='Sequence',
    #     required=False, default=0)


    # template = fields.Many2one(
    #     'ir.actions.report',
    #     string='Template',
    #     required=True,
    #     domain="[('model', '=', 'account.payment')]")



    # def print_check_number_with_padding(self, number):
    #     return str(number).zfill(self.padding)
    #
    # def get_check_sequence(self):
    #     sequence = self.sequence
    #     self.sequence += 1
    #     return sequence
