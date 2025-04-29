# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HousingSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    check_housing_duration = fields.Boolean(
        string='Check Housing Duration',
        required=False, default=True)

    def set_values(self):
        super(HousingSettings, self).set_values()
        select_type = self.env['ir.config_parameter'].sudo()
        if self.check_housing_duration:
            select_type.set_param('res.config.settings.check_housing_duration', self.check_housing_duration)
        else:
            select_type.set_param('res.config.settings.check_housing_duration', False)

    @api.model
    def get_values(self):
        res = super(HousingSettings, self).get_values()
        select_type = self.env['ir.config_parameter'].sudo()
        check_housing_duration = select_type.get_param('res.config.settings.check_housing_duration')

        res.update({'check_housing_duration': check_housing_duration})
        return res
