from odoo import models, fields, api


class InheritHrSalaryRule(models.Model):
    _inherit = "hr.salary.rule"

    input_element = fields.Boolean(string="Input Element")
