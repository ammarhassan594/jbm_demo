from odoo import models, fields, api, _
from odoo.exceptions import UserError



class HRApplicantInherit(models.Model):
    _inherit = 'hr.applicant'

    applicant_state = fields.Selection([
        ('draft', 'Initial Qualification'),
        ('first_interview', 'First Interview'),
        ('second_interview', 'Second Interview'),
        ('done', 'Confirm'),
        ('rejected', 'Rejected')], default='draft', string="Status")

    def action_hr_employee(self):
        self.applicant_state = 'first_interview'
        self.stage_id = self.env.ref('hr_recruitment.stage_job2').id

    def action_department_employee(self):
        if self.department_id and self.department_id.manager_id and self.department_id.manager_id.user_id:
            if self.env.user.id == self.department_id.manager_id.user_id.id:
            # if self.env.user.id == self.user_id.employee_id and self.user_id.employee_id.parent_id and self.user_id.employee_id.parent_id.user_id and self.user_id.employee_id.parent_id.user_id.id:
                self.applicant_state = 'second_interview'
                self.stage_id = self.env.ref('hr_recruitment.stage_job3').id
            else:
                raise UserError("Only Employee Manager Can Approve.")
        else:
            raise UserError("Please Check Manager User Of Department")


    def action_hr_manager(self):
        self.applicant_state = 'done'
        self.stage_id = self.env.ref('hr_recruitment.stage_job4').id

    def action_manager_refuse(self):
        self.applicant_state = 'rejected'
        
    def action_operational_employee(self):
        self.applicant_state = 'first_interview'
        self.stage_id = self.env.ref('hr_recruitment.stage_job2').id

    def action_operational_manager(self):
        self.applicant_state = 'second_interview'
        self.applicant_state = 'done'
        self.stage_id = self.env.ref('hr_recruitment.stage_job2').id
        self.stage_id = self.env.ref('hr_recruitment.stage_job4').id

