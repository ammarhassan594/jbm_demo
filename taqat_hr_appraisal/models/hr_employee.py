from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrEmployeeInherit(models.Model):
    _inherit = 'hr.employee'

    employee_degree = fields.Char('Employee Degree')
    employee_degree_date = fields.Date("Employee Degree Date")
    employee_Profession = fields.Char('Employee Profession')
    degree_field = fields.Char('Field')
