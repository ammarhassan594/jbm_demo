from odoo import fields, models, api, _

class EmployeePenalty(models.Model):
    _name = 'employee.penalty'
    _description = 'Employee Penalty'

    employee_id = fields.Many2one('hr.employee','Employee')
    name = fields.Char('Name')
    penalty_issued_for = fields.Char('Penalty Issued For')
    type_of_penalty = fields.Char('Type of Penalty')
    case = fields.Many2one('ebs.legal.case','Cases')
    issued_date = fields.Date('Issued Date')
    comments = fields.Text('Others/Comments')