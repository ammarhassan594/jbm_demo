from odoo import models, fields, api, _


class LetterResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    report_signature_width = fields.Float(string="Signature width (cm)",
                                   config_parameter='ebs_jbm_hr_holiday_custom.report_signature_width')

    report_signature_height = fields.Float(string="Signature height (cm)",
                                    config_parameter='ebs_jbm_hr_holiday_custom.report_signature_height')