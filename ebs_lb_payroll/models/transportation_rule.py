# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


class TrasportationRule(models.Model):
    _name = 'ebspayroll.transportation.rule'
    _description = 'Transportation Rule'

    payment_date = fields.Date(
        string='Payment Date',
        required=True)
    description = fields.Text(
        string="Description",
        required=False)
    active = fields.Boolean(
        string='Active', default=True,
        required=False)
    lines = fields.One2many(
        comodel_name='ebspayroll.transportation.rule.lines',
        inverse_name='transportation_rule_id',
        string='Lines',
        required=False, copy=True)

    def copy(self, default=None):
        default = dict(default or {})
        default['payment_date'] = self.payment_date + relativedelta(months=1)
        return super(TrasportationRule, self).copy(default)

    @api.constrains('payment_date')
    def _check_payment_date(self):
        for record in self:
            if len(self.env['ebspayroll.transportation.rule'].search(
                    [('payment_date', '=', record.payment_date), ('active', '=', True), ('id', '!=', record.id)])) > 0:
                raise ValidationError(_("Date already exists"))
