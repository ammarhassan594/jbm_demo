from odoo import models, fields, api, _

class InheritResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ooredoo_customerEmail = fields.Char('Customer Email', store=True)
    ooredoo_customerID = fields.Char('Customer ID', store=True)
    ooredoo_username = fields.Char('User Name', store=True)
    ooredoo_password = fields.Char('Password', store=True)
    ooredoo_url = fields.Char('URl', store=True)
    ooredoo_message = fields.Char('Message', store=True)
    ooredo_originator = fields.Char(string="Originator", store=True)

    @api.model
    def get_values(self):
        res = super(InheritResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        ooredoo_customerEmail = params.get_param('ooredoo_customerEmail')
        ooredoo_customerID = params.get_param('ooredoo_customerID')
        ooredoo_username = params.get_param('ooredoo_username')
        ooredoo_password = params.get_param('ooredoo_password')
        ooredoo_url = params.get_param('ooredoo_url')
        ooredoo_message = params.get_param('ooredoo_message')
        ooredo_originator = params.get_param('ooredo_originator')
        res.update(
            ooredoo_customerEmail=ooredoo_customerEmail,
            ooredoo_customerID=ooredoo_customerID,
            ooredoo_username=ooredoo_username,
            ooredoo_password=ooredoo_password,
            ooredoo_url=ooredoo_url,
            ooredoo_message=ooredoo_message,
            ooredo_originator=ooredo_originator,
        )
        return res


    def set_values(self):
        super(InheritResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("ooredoo_customerEmail", self.ooredoo_customerEmail)
        self.env['ir.config_parameter'].sudo().set_param("ooredoo_customerID", self.ooredoo_customerID)
        self.env['ir.config_parameter'].sudo().set_param("ooredoo_username", self.ooredoo_username)
        self.env['ir.config_parameter'].sudo().set_param("ooredoo_password", self.ooredoo_password)
        self.env['ir.config_parameter'].sudo().set_param("ooredoo_url", self.ooredoo_url)
        self.env['ir.config_parameter'].sudo().set_param("ooredoo_message", self.ooredoo_message)
        self.env['ir.config_parameter'].sudo().set_param("ooredo_originator", self.ooredo_originator)
