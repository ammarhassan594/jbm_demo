from odoo import models, fields, api, _


class ExcellenceBoard(models.Model):
    _name = 'excellence.board'

    name = fields.Char(string="Title", required=True)
    code = fields.Char(string="Code", required=True)
    issue_date = fields.Date(string="Issue Date", required=True)
    attachment = fields.Binary(string="Attachment")
    file_name_attachment = fields.Char(string='File Name')