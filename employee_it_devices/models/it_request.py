from odoo import models, fields, api


class ItDevices(models.Model):
    _name = 'it.request'

    name = fields.Char()
    show_description = fields.Boolean()