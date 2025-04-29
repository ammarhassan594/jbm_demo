from odoo import models, fields, api

class InheritHrEmployeePublic(models.Model):
    _inherit = ["hr.employee.public"]

    arabic_name = fields.Char(string='Arabic Name')
