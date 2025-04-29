# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ebsHrEosOtherEntitlementsTypes(models.Model):
    _name = 'ebs.hr.eos.other.entitlements.types'
    _description = 'EOS Other Entitlement Types'

    name = fields.Char(string="Name")
    # account_id = fields.Many2one('account.account', string="Account")
    eos_config_id = fields.Many2one('ebs.hr.eos.config', string="Eos Config")
