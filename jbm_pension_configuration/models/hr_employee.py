from odoo import models, fields, api, _


class InheritHrEmployee(models.Model):
    _inherit = 'hr.employee'

    out_of_pension = fields.Boolean(string="Out Of Pension", default=False)