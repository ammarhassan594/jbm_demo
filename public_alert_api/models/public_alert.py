from odoo import fields, models, api, _


class PublicAlert(models.Model):
    _name = 'public.alert'
    _description = 'Public Alert'
    _rec_name = 'title'

    title = fields.Char(string="Title")
    date = fields.Date(string="Date")
    attachment = fields.Binary(string="Attachment")
    description = fields.Text(string="Description")
