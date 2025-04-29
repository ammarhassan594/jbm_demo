from odoo import api, fields, models, _


class Company_Status(models.Model):
    _name = 'company.status'
    _description = "name"

    name = fields.Char("Name")
