from odoo import api, fields, models, _


class EbsHistoryExperience(models.Model):
    _name = 'ebs.hobbies'
    _description = 'EBS Hobbies'
    _rec_name = 'type_hobbies'

    employee_id = fields.Many2one('hr.employee')
    type_hobbies = fields.Char("Type of Hobbies")
    frequency_activity = fields.Char("Frequency of activity")
    text = fields.Text("Others/Comments")
