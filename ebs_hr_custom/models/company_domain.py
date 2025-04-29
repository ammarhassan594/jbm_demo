from odoo import models, fields, api, _


class CompanyDomain(models.Model):
    _name = 'company.domain'
    _description = 'Company Domains'

    name = fields.Char(string="Domain", default="", required=False)

    _sql_constraints = [('unique_group', 'unique(name)',
                         'This domain already exists!\nPlease, enter another name')]
