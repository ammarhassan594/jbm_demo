from odoo import api, fields, models, _


class Management_Structure(models.Model):
    _name = 'mgt.structure'
    _description = "partner_id"

    partner_id = fields.Many2one('res.partner', "Name")
    job_position_id = fields.Many2one('job.position', "Job Position")
    description = fields.Text("Description")


class Job_Position(models.Model):
    _name = 'job.position'
    _description = 'Job Position'

    name = fields.Char("Name")
