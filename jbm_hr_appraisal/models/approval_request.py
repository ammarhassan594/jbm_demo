from odoo import fields, models, api


class InheritApprovalRequest(models.Model):
    _inherit = 'approval.request'

    def update_employee_in_job(self):
        if self.approval_job_line_ids:
            for line in self.approval_job_line_ids:
                if line.job_id and line.no_of_employees > 0:
                    line.job_id.sudo().write({
                        'no_of_recruitment': line.job_id.sudo().n_allowed_employees + line.no_of_employees,
                        'n_allowed_employees': line.job_id.sudo().n_allowed_employees +
                                               line.no_of_employees,
                    })
            self.sudo().write({
                'job_updated': True,
            })
