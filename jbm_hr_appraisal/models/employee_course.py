from odoo import fields, models, api


class InheritEmployeeCourse(models.Model):
    _inherit = 'employee.course'

    course_ids = fields.Many2many(related='employee_id.job_id.course_ids',
                                  string="Course", readonly=True)
