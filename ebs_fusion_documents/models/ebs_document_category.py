from odoo import api, fields, models


class EbsDocumentCategory(models.Model):
    _name = 'ebs.document.category'
    _description = 'Ebs Document Category'

    name = fields.Char(string='Name')
