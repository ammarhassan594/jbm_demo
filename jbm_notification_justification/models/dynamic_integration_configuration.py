from odoo import models, fields, api


class InheritDynamicIntegrationConfiguration(models.Model):
    _inherit = 'dynamic.integration.configuration'

    @api.model
    def _get_dynamic_integration_model_names(self):
        res = super(InheritDynamicIntegrationConfiguration, self)._get_dynamic_integration_model_names()
        res.append('hr.attendance')
        return res
