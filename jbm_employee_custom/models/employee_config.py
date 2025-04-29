from odoo import fields, models, api


class EmployeeConfig(models.TransientModel):
    _inherit = ['res.config.settings']

    applied_on_date = fields.Date(related='company_id.applied_on_date', readonly=False, string='Applied Date')


class CompanyInherit(models.Model):
    _inherit = 'res.company'

    applied_on_date = fields.Date(string='Applied Date')
