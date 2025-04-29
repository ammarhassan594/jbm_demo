from odoo import models, fields, api, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    attendance_api_link = fields.Char(string="API Link", store=True)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        attendance_api_link = params.get_param('attendance_api_link')
        res.update(
            attendance_api_link=attendance_api_link,
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("attendance_api_link", self.attendance_api_link)
