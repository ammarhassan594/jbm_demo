# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError


class AdditionalElements(models.Model):
    _name = 'ebspayroll.additional.elements'
    _description = 'Additional Elements'
    _order = "payment_date desc"
    type = fields.Many2one(
        comodel_name='ebspayroll.additional.element.types',
        string='Element Type',
        required=True,
        ondelete='restrict')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('cancel', 'Cancel'),


    ], string="Status", default="draft")



    rule_type = fields.Selection(
        string='Type',
        related="type.type",
        required=False, )

    name = fields.Char(
        string='Name', compute="compute_name",
        required=False)
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
        comodel_name='ebspayroll.additional.element.lines',
        inverse_name='additional_element_id',
        string='Lines',
        required=False,
        copy=True)

    company_id = fields.Many2one('res.company', string="Main Company", default=lambda self: self.env.company)

    client_id = fields.Many2one('res.partner', string="Company/Client", domain=[('is_customer', '=', True), ('is_company', '=', True), ('parent_id', '=', False)])
    from_date = fields.Date(
        string='From Date')
    to_date = fields.Date(
        string='To Date')
    is_recurring = fields.Boolean(compute="get_element_type")

    @api.depends('type')
    def get_element_type(self):
        for rec in self:
            if rec.type and rec.type.recurring:
                rec.is_recurring = True
            else:
                rec.is_recurring = False


    def confirm_element(self):
        self.state = "confirm"

    def cancel_element(self):
        self.state = "cancel"

    def reset_to_draft_element(self):
        self.state = 'draft'

    def copy(self, default=None):
        default = dict(default or {})
        default['payment_date'] = self.payment_date + relativedelta(months=1)
        return super(AdditionalElements, self).copy(default)

    @api.constrains('payment_date')
    def _check_payment_date(self):
        for record in self:
            if len(self.env['ebspayroll.additional.elements'].search(
                    [('type', '=', record.id),
                     ('payment_date', '=', record.payment_date),
                     ('active', '=', True),
                     ('state', '=', 'confirm'),
                     ('id', '!=', record.id)])) > 0:
                raise ValidationError(_("Date already exists"))

    @api.depends('type')
    def compute_name(self):
        for rec in self:
            rec.name = rec.type.name

    def unlink(self):
        for rec in self:
            if rec.state in ['confirm', 'cancel']:
                raise UserError("Record can only be deleted in draft state.")
        rec = super(AdditionalElements, self).unlink()
        return rec

