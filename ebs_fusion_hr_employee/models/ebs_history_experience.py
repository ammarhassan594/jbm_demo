from odoo import api, fields, models, _


class EbsHistoryExperience(models.Model):
    _name = 'ebs.history.experience'
    _description = 'EBS History Experience'
    _rec_name = 'company_worked'

    employee_id = fields.Many2one('hr.employee')
    company_worked = fields.Char("Company Worked for")
    location = fields.Char("Location")
    cancel_noc = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Cancelled/NOC")
    text = fields.Text("Others/Comments")
