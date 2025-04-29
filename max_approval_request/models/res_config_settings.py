from odoo import models, fields, api, _


class InheritResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    max_number_requests = fields.Char('Max Number Requests', config_parameter='max_approval_request.max_number_requests')

    # def set_values(self):
    #     super(InheritResConfigSettings, self).set_values()
    #     select_type = self.env['ir.config_parameter'].sudo()
    #     select_type.set_param('res.config.settings.max_number_requests', self.max_number_requests)
    #
    # @api.model
    # def get_values(self):
    #     res = super(InheritResConfigSettings, self).get_values()
    #     select_type = self.env['ir.config_parameter'].sudo()
    #     max_number_requests = select_type.get_param('res.config.settings.max_number_requests')
    #     res.update({'max_number_requests': max_number_requests})
    #     return res
