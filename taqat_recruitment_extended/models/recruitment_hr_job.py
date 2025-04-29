from odoo import models, fields, api, _
from odoo.exceptions import UserError



class HRJobInherit(models.Model):
    _inherit = 'hr.job'

    employee_type = fields.Selection(
        [('main_company_employee', 'Main Company Employee'), ('outsourced_employee', 'Outsourced Employee')],
        default='main_company_employee')

    state = fields.Selection([
        ('recruit', 'Recruitment in Progress'), ('open', 'Not Recruiting'),
        ('department_manager', 'Confirm'), ('hr_manager', 'Approved'),
        ('account_manager', 'Validate'), ('rejected', 'Rejected')], default='department_manager', string="Status")

    def action_department_manager_approve(self):
        if self.env.user.id == self.user_id and self.user_id.employee_id and self.user_id.employee_id.parent_id and self.user_id.employee_id.parent_id.user_id and self.user_id.employee_id.parent_id.user_id.id:
            self.state = 'hr_manager'
        else:
            raise UserError("Only Employee Manager Can Approve.")


    def action_hr_manager(self):
        self.state = 'account_manager'

    def action_account_manager(self):
        self.state = 'recruit'

    def action_manager_refuse(self):
        self.state = 'rejected'

    def action_department_manager(self):
        if self.env.user.id == self.user_id and self.user_id.employee_id and self.user_id.employee_id.parent_id and self.user_id.employee_id.parent_id.user_id and self.user_id.employee_id.parent_id.user_id.id:
            self.state = 'recruit'
        else:
            raise UserError("Only Employee Manager Can Approve.")


    def action_operational_employee(self):
        self.state = 'account_manager'

    def action_operational_manager(self):
        self.state = 'hr_manager'



