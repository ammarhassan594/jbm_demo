from odoo import models, fields, api, _


class ResConfigSetting(models.TransientModel):
    _inherit = 'res.config.settings'

    max_allowed_hours = fields.Float(related='company_id.max_allowed_hours', readonly=False, string='Max Allowed Hours')


class CompanyInherit(models.Model):
    _inherit = 'res.company'

    max_allowed_hours = fields.Float(string='Max Allowed Hours')
