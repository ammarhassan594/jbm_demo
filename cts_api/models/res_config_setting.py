# -*- coding: utf-8 -*-


from odoo import models, fields, api, _


class InheritResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    cts_auth_url = fields.Char('Authentication URl', store=True)
    cts_url = fields.Char('URl', store=True)
    cts_username = fields.Char('User Name', store=True)
    cts_password = fields.Char('Password', store=True)
    ssl_certificate_url = fields.Char('SSL certificate Url',store=True)

    @api.model
    def get_values(self):
        res = super(InheritResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        cts_auth_url = params.get_param('cts_auth_url')
        cts_url = params.get_param('cts_url')
        cts_username = params.get_param('cts_username')
        cts_password = params.get_param('cts_password')
        ssl_certificate_url = params.get_param('ssl_certificate_url')
        res.update(
            cts_auth_url=cts_auth_url,
            cts_url=cts_url,
            cts_username=cts_username,
            cts_password=cts_password,
            ssl_certificate_url=ssl_certificate_url,
        )
        return res

    def set_values(self):
        super(InheritResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("cts_auth_url", self.cts_auth_url)
        self.env['ir.config_parameter'].sudo().set_param("cts_url", self.cts_url)
        self.env['ir.config_parameter'].sudo().set_param("cts_username", self.cts_username)
        self.env['ir.config_parameter'].sudo().set_param("cts_password", self.cts_password)
        self.env['ir.config_parameter'].sudo().set_param("ssl_certificate_url", self.ssl_certificate_url)
