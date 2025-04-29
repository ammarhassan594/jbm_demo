# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrEmployeeSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    company_stamp = fields.Binary(related='company_id.company_stamp', readonly=False)

    company_domain = fields.Many2many(related='company_id.company_domain', readonly=False, string="Company's domain")


class CompanyInherit(models.Model):
    _inherit = 'res.company'

    company_stamp = fields.Binary(string='Stamp')

    company_domain = fields.Many2many(comodel_name="company.domain", string="Company's domain")