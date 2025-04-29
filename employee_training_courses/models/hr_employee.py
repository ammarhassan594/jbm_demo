from odoo import fields, models, api


class InheritHrEmployee(models.Model):
    _inherit = 'hr.employee'

    employee_course_ids = fields.One2many('employee.course', 'employee_id')
