from odoo import api, fields, models, _


class Ebs_Designation_Description(models.Model):
    _name = 'ebs.designation.description'
    _description = 'EBS Designation Description'
    _rec_name = 'job_description'

    employee_id = fields.Many2one('hr.employee')

    job_description = fields.Char("Job Description")
    communication_chart = fields.Char("Communication Chart")
    designation_risk = fields.Char("Designation Risk")
    rules = fields.Char("Rules")
    authority = fields.Char("Authority")
    responsibility = fields.Char("Responsibility")
    line_manager = fields.Char("Line Manager")
    department = fields.Char("Department")
    other = fields.Text("Other")
