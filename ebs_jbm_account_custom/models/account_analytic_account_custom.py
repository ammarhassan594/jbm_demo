# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime


class AccountAnalyticAccountCustom(models.Model):
    _inherit = 'account.analytic.account'

    account_ids = fields.Many2many('account.account', string='Accounts')
