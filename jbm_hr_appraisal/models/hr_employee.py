from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError


class InheritHrEmployee(models.Model):
    _inherit = 'hr.employee'

    job_code = fields.Char(related='job_id.job_code')

    @api.onchange('department_id')
    def onchange_department_id(self):
        pass

    @api.onchange('department_id')
    def _onchange_department(self):
        pass

    @api.onchange('job_id')
    @api.constrains('job_id')
    def _onchange_job_id(self):
        for employee in self:
            if employee.job_id:
                if employee.job_id.parent_id.employee_ids:
                    selected_employee = employee.job_id.parent_id.employee_ids[0]
                    employee.parent_id = selected_employee.id
                    if employee.job_id.department_id:
                        employee.department_id = employee.job_id.department_id.id
                elif employee.job_id.department_id:
                    employee.department_id = employee.job_id.department_id.id
                    employee.parent_id = employee.job_id.department_id.manager_id.id
                elif employee.department_id:
                    employee.parent_id = employee.department_id.manager_id.id
            elif employee.department_id:
                employee.parent_id = employee.department_id.manager_id.id

    @api.constrains('job_id')
    def _check_number_of_employees(self):
        for employee in self:
            if employee.job_id:
                current_n_employees = len(employee.job_id.employee_ids)
                if current_n_employees > employee.job_id.n_allowed_employees:
                    raise ValidationError(_(f'Not allowed change to job {employee.job_id.name}'
                                            f' because job is limit to number {employee.job_id.n_allowed_employees}'))


class InheritHrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    parent_id = fields.Many2one('hr.employee', 'Manager',
                                domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    @api.depends('department_id')
    def _compute_parent_id(self):
        pass
