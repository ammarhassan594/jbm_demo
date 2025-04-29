from odoo import fields, models, api


class HrContract(models.Model):
    _inherit = 'hr.contract'

    department_id = fields.Many2one('hr.department', compute='_compute_employee_contract',
                                    store=False, readonly=True,
                                    domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                    string="Department")
    job_id = fields.Many2one('hr.job', compute='_compute_employee_contract',
                             store=False, readonly=True,
                             domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                             string='Job Position')

    department = fields.Many2one('hr.department', compute='_compute_employee_contract',
                                 store=False, readonly=True,
                                 domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                 string="Department")

    @api.depends('employee_id')
    def _compute_employee_contract(self):
        for rec in self:
            if rec.employee_id:
                for contract in rec.filtered('employee_id'):
                    contract.job_id = contract.employee_id.job_id
                    contract.department_id = contract.employee_id.department_id
                    contract.department = contract.employee_id.department_id
                    contract.resource_calendar_id = contract.employee_id.resource_calendar_id
                    contract.company_id = contract.employee_id.company_id
            else:
                rec.job_id = None
                rec.department_id = None
                rec.department = None
                rec.resource_calendar_id = None
                rec.company_id = None
