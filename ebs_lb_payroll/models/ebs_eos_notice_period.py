# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ebsEosNoticePeriod(models.Model):
    _name = 'ebs.eos.notice.period'
    _description = 'EOS Notice Period'

    from_year = fields.Float(string="From(Year)")
    to_year = fields.Float(string="To(Year)")
    notice_period_months = fields.Integer(string="Notice Period(Months)")
    eos_config_id = fields.Many2one('ebs.hr.eos.config', string="Eos Config")
