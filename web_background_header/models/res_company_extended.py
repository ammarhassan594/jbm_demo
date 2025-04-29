from odoo import models, fields, api

class ResCompanyInherited(models.Model):
    _inherit = 'res.company'

    header_color_picker = fields.Char("Header Color Picker")
    background_color_picker = fields.Char("Background Color Picker")
    # background_image = fields.Binary(string="Home Background Image", attachment=True)
