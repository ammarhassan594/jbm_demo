from odoo import fields, models, api


class InheritHrEmployee(models.Model):
    _inherit = 'hr.employee'

    employee_excellence_ids = fields.One2many('excellence.element', 'employee_id')
