from odoo import api, fields, models, _


class OvertimeLines(models.Model):
    _name = "hr.overtime.line"
    _description = "Overtime Line"

    date = fields.Date(string="Date", required=True, help="The Day that the employee has overtime")
    employee_id = fields.Many2one('hr.employee', string="Employee", help="Employee")
    hours = fields.Float(string="Hours", required=True, help="Hours")
    paid = fields.Boolean(string="Paid", help="Paid")
    overtime_id = fields.Many2one('hr.overtime', string="Overtime Ref.", help="Overtime dates")
    overtime_type = fields.Selection(string="Type", default="",
                                     selection=[('normal', 'Normal'), ('special', 'Special')],
                                     required=False, )
    project_id = fields.Many2one('project.project', string='Project')

