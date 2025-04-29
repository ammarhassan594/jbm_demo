from odoo import api, fields, models, _


class EbsPenalty(models.Model):
    _name = 'ebs.penalty'
    _description = 'EBS Penalty'
    _rec_name = 'name'

    employee_id = fields.Many2one('hr.employee')
    name = fields.Char("Name")
    penalty_issue = fields.Date("Penalty Issued for")
    penalty_type = fields.Char("Type of Penalty")
    cases = fields.Char("Cases")
    issue_date = fields.Date("Issued Date")
    text = fields.Text("Others/Comments")
