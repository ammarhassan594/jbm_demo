from odoo import models, fields, api, _
from datetime import datetime, date


class AllowanceDependent(models.Model):
    _name = 'allowance.dependent'
    _rec_name = 'dependent_name'

    allowance_id = fields.Many2one(
        comodel_name='allowance.request',
        string='Allowance', default=lambda self: self._context.get('active_id'), readonly=True)
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        related='allowance_id.employee_id')
    dependent_name = fields.Many2one(
        comodel_name='hr.emp.child',
        domain="[('emp_id', '=', employee_id)]",
        string="Dependent", required=True)
