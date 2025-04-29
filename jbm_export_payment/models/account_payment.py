# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountPaymentCustom(models.Model):
    _inherit = 'account.payment'

    purpose_of_transfer = fields.Char(string="Purpose of Transfer")
