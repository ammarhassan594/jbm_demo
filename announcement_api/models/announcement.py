from odoo import models, fields, api, _


class Announcement(models.Model):
    _name = "announcement"

    name = fields.Char(string="Name")
    date = fields.Date(string="Date")
    attachment = fields.Binary(string="Attachment")