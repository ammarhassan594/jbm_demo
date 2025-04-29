from odoo import fields, models, api


class EmployeeCourse(models.Model):
    _name = 'employee.course'
    _description = 'Employee Course'

    employee_id = fields.Many2one('hr.employee', string="Employee")
    course_training_id = fields.Many2one('training.course', string="Training Course")
    date_taken = fields.Date(string="Date Taken")
    location = fields.Char(string="Location")
    remarks = fields.Text(string="Remarks")
    passed = fields.Boolean(string="Passed")

    @api.onchange('course_training_id')
    def _onchange_course_training_id(self):
        for employee_course in self:
            if employee_course.course_training_id:
                employee_course.location = employee_course.course_training_id.location
                employee_course.remarks = employee_course.course_training_id.remarks
            else:
                employee_course.location = ''
