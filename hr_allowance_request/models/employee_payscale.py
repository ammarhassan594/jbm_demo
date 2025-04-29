from odoo import fields, models, api


class InheritEmployeePayscale(models.Model):
    _inherit = 'employee.payscale'

    leave_allowance_factor = fields.Float('Factor', default=1.0)
    number_of_dependent = fields.Integer('Number Of Dependents', default=0)
