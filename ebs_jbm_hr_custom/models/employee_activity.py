from odoo import fields, models, api, _


class EmployeeActivity(models.Model):
    _name = 'employee.activity'
    _description = 'Employee Description'

    model_id = fields.Many2one('ir.model', string="Model")
    number_of_record_created = fields.Integer(string="Number of records Created")
    number_of_record_updated = fields.Integer(string="Number of records Updated")
    employee_id = fields.Many2one('hr.employee', string="Employee")
