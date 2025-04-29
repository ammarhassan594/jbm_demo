from odoo import fields, models, api


class WorkCertificate(models.TransientModel):
    _name = 'emp.work.certificate.wizard'
    _description = 'Work Certificate Wizard'

    name = fields.Char('Name', required=True)

    def print_work_certificate(self):
        employees = self.env['hr.employee']
        if self.env.context.get('active_model') == 'hr.employee' and self.env.context.get('active_ids'):
            employees = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_ids'))
        for employee in employees:
            employee.sudo().write({'wizard_name': self.name})
        report = self.env.ref('taqat_hr_employee.employee_work_certificate_action').with_context(
            name=self.name).report_action(employees)
        return report
