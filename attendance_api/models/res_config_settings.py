from odoo import models, fields, api, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    attendance_api_token = fields.Char(string="API Token")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        attendance_api_token = params.get_param('attendance_api_token')
        res.update(
            attendance_api_token=attendance_api_token,
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("attendance_api_token", self.attendance_api_token)
