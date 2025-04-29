from odoo import models, fields, api, _


class LetterResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    max_number_letter = fields.Char('Max Number Letter',
                                    config_parameter='jbm_letter_request.max_number_letter')

    print_signature_stamp = fields.Boolean('Print Signature / Stamp',
                                           config_parameter='jbm_letter_request.print_signature_stamp')

    stamp_width = fields.Float(string="Stamp Width (cm)",
                               config_parameter='jbm_letter_request.stamp_width')

    stamp_height = fields.Float(string="Stamp Height (cm)",
                                config_parameter='jbm_letter_request.stamp_height')

    signature_width = fields.Float(string="Signature width (cm)",
                                   config_parameter='jbm_letter_request.signature_width')

    signature_height = fields.Float(string="Signature height (cm)",
                                    config_parameter='jbm_letter_request.signature_height')

    new_value = fields.Float(string="new value", config_parameter='jbm_letter_request.new_value')


