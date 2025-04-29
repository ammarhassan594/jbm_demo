from odoo import models, fields, api, _


class JustificationCompanyInherit(models.Model):
    _inherit = 'res.company'

    reject_after = fields.Float(string='Reject After (Hours)')


class JustificationResConfigSetting(models.TransientModel):
    _inherit = 'res.config.settings'

    reject_after = fields.Float(related='company_id.reject_after', readonly=False, string='Reject After (Hours)')
