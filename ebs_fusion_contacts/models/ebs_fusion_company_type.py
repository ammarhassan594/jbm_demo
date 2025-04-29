from odoo import api, fields, models, _


class Company_Type(models.Model):
    _name = 'company.type'
    _description = "name"

    name = fields.Char("Name")