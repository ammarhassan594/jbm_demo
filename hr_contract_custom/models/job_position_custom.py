from odoo import fields, models, api


class JobPositionCustom (models.Model):
    _inherit = 'hr.job'

    required_signatures = fields.One2many('hr.job.signature', 'hr_job_id', string='Required Signatures')
    


