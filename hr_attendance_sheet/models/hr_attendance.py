# -*- coding: utf-8 -*-
""" init object """
from odoo import fields, models, api, _, tools, SUPERUSER_ID
from odoo.exceptions import ValidationError


class Attendance(models.Model):
    _inherit = 'hr.attendance'

    late_in = fields.Float("Late In", )
    diff_time = fields.Float("Diff Time", help="Diffrence between the working time and attendance time(s) ", )
    # todo : move it to another module
    overtime_created = fields.Boolean(string='Overtime Created', default=False, copy=False)
    emp_number = fields.Char(string="Employee Number", related="employee_id.registration_number", store=True)
    num_of_working_hours = fields.Integer(string="Number of Working Hours", default=8, required=False, )
    break_hours = fields.Integer(string="Break", default=1, required=False, )
    normal_hours = fields.Integer(string="Normal Hours", default=8, required=False, )
    overtime_hours = fields.Integer(string="Normal OT Hours", default=0, required=False, )
    special_overtime = fields.Integer(string="Special OT Hours", default=0, required=False, )
    actual_sign_in = fields.Float("Actual sign in", readonly=False)
    actual_sign_out = fields.Float("Actual sign out", readonly=False)
    machine_in = fields.Char("Machine In", readonly=False)
    machine_out = fields.Char("Machine Out", readonly=False)
    # employee_project = fields.Many2one(comodel_name="project_project", string="Project", required=False)
    project_id = fields.Many2one('project.project', string='Project')

    day_from = fields.Date(string="", compute='get_day_from', required=False, store=True)
    day_to = fields.Date(string="", compute='get_day_to', required=False, store=True)

    @api.depends('check_in')
    def get_day_from(self):
        for rec in self:
            rec.day_from = rec.check_in.date()

    @api.depends('check_out')
    def get_day_to(self):
        for rec in self:
            if rec.check_out:
                rec.day_to = rec.check_out.date()
            else:
                pass

    @api.constrains('check_in', 'check_out')
    def _check_date_in_same_day(self):
        for record in self:
            if record.check_in and record.check_out and record.check_out.date() != record.check_in.date():
                raise ValidationError(_('Check out must be same day of check in'))
