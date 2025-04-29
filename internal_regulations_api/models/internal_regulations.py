from odoo import models, fields, api, _


class InternalRegulations(models.Model):
    _name = 'internal.regulations'
    _description = 'Internal Regulation'

    name = fields.Char(string="Name", required=True)
    description = fields.Char(string="Description")
    date_from = fields.Date(string="Valid From Date")
    date_to = fields.Date(string="Valid To Date")
    attachment = fields.Binary(string="Attachment")
