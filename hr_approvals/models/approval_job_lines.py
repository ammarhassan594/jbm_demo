from odoo import fields, models, api


class ApprovalJobLines(models.Model):
    _name = 'approval.job.lines'
    _description = 'Approval Job Lines'

    job_id = fields.Many2one('hr.job', string="Job")
    description = fields.Char(string="Description")
    no_of_employees = fields.Integer(string="No of employees")
    approval_request_id = fields.Many2one('approval.request', string="Approval Request ID")
