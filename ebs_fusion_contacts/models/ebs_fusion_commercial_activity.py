from odoo import api, fields, models, _


class Commercial_Activity(models.Model):
    _name = 'commercial.activity'
    _description = "name"

    name = fields.Char("Name")
    code = fields.Char("Code")
