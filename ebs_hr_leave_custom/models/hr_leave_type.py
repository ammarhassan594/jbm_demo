# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError


class HRLeaveTypeCustom(models.Model):
    _inherit = 'hr.leave.type'

    emergency = fields.Boolean(required=False)
    legal = fields.Boolean(string="Legal", default=False)
    leave_validation_type = fields.Selection([
        ('no_validation', 'No Validation'),
        ('hr', 'Leave Officer'),
        ('manager', 'Team Leader'),
        ('both', 'Team Leader and Leave Officer')], default='hr', string='Validation')

    default_days = fields.Integer("Default Number Of Days")
    calendar_day = fields.Integer(string="Calendar day")
    qatari_fully_paid_months = fields.Integer(string="Qatari fully Paid(months)")
    expait_fully_paid = fields.Integer(string="Expait fully paid")
    expait_half_paid = fields.Integer(string="Expait half paid")
    expait_unpaid = fields.Integer(string="Expait unpaid")
    inhouse_fully_paid = fields.Integer(string="Inhouse fully paid")
    inhouse_half_paid = fields.Integer(string="Inhouse half paid")
    inhouse_unpaid = fields.Integer(string="Inhouse unpaid")

    # custom fields for deduction
    is_in_calendar_days = fields.Boolean(default=False, string="Is Calendar Days?")
    is_sick_leave = fields.Boolean(string="Is sick Leave?", default=False)
    is_leave_deduction = fields.Boolean(string="Leave Deduction", default=False)
    # custom fields for doc required
    is_doc_required = fields.Boolean(string="Document is required ?", default=False)
    # qatari_leave_start = fields.Integer(string="Qatari Leave Start")
    qatari_leave_end = fields.Integer(string="Qatari Leave End")
    expait_leave_start = fields.Integer(string="Expait Leave Start")
    expait_leave_end = fields.Integer(string="Expait Leave End")
    inhouse_leave_start = fields.Integer(string="InHouse Leave Start")
    inhouse_leave_end = fields.Integer(string="InHouse Leave End")

    is_permission = fields.Boolean(string='Is permission', )

    permission_config_ids = fields.One2many(comodel_name="permission.config", inverse_name="leave_type_id")

    def get_days(self, employee_id):
        return self.get_employees_days([employee_id])[employee_id]

    @api.constrains('permission_config_ids')
    def prevent_permission_config_duplication(self):
        for rec in self:
            my_list = []
            for line in rec.permission_config_ids:
                for inner in my_list:
                    if inner == line.permission_leave_type:
                        raise ValidationError("Duplication on permission configurations is  not allowed")

                my_list.append(line.permission_leave_type)
