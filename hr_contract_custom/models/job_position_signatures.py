from odoo import fields, models, api


class JobPositionSignature(models.Model):
    _name = 'hr.job.signature'
    _description = 'HR Job Signature'

    name = fields.Many2one(
        comodel_name='res.users',
        string='User',
        required=False)
    hr_job_id = fields.Many2one(
        comodel_name='hr.job',
        string='Job Position',
        required=True)
    sequence = fields.Integer(
        string='Sequence',
        required=False)
    hr_employee_id = fields.Many2one('hr.employee', string='Employee', compute='_get_employee')
    job_title_id = fields.Many2one('job.title', string='Job Title', compute='_get_employee')
    job_position_id = fields.Many2one('hr.job', string='Job Position', compute='_get_employee')

    @api.depends('name')
    def _get_employee(self):
        for rec in self:
            if rec.name:
                related_employee = self.env['hr.employee'].search([('user_id', '=', rec.name.id)], limit=1)
                rec.hr_employee_id = related_employee.id if related_employee else False
                rec.job_title_id = related_employee.contract_id.job_title.id if related_employee.contract_id.job_title else False
                rec.job_position_id = related_employee.contract_id.job_id.id if related_employee.contract_id.job_id else False
            else:
                rec.hr_employee_id = False
                rec.job_title_id = False
                rec.job_position_id = False
