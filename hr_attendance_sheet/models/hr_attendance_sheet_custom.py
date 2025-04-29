# -*- coding: utf-8 -*-
from odoo import fields, models, api


class AttendanceSheet(models.Model):
    _inherit = 'attendance.sheet'

    contract_id = fields.Many2one('hr.contract', compute="_get_employee_running_contract", store=True)
    employee_type = fields.Selection(string="Employment Category",
                                     selection=[('temp', 'Temporary Employee'), ('perm_in_house', 'Permanent In house'),
                                                ('perm_staff', 'Permanent Staff')], compute="_get_employee_running_contract", readonly=False, store=True)
    accommodation_allowance = fields.Float()
    transportation_allowance = fields.Float()
    food_allowance = fields.Float()
    site_allowance = fields.Float()
    mobile_allowance = fields.Float()
    other_allowance = fields.Float()
    ticket_allowance = fields.Float()
    earning_allowance = fields.Float()
    overtime_allowance = fields.Float()
    leave_allowance = fields.Float()
    special_allowance = fields.Float()
    fixed_overtime_allowance = fields.Float()
    overtime_100_allowance = fields.Float()
    basic_deduction = fields.Float()
    other_deduction = fields.Float()
    staff_hotel_deduction = fields.Float()
    car_loan_deduction = fields.Float()
    marriage_loan_deduction = fields.Float()
    transportation_deduction = fields.Float()
    accommodation_deduction = fields.Float()
    mobile_deduction = fields.Float()
    uniform_deduction = fields.Float()
    social_deduction = fields.Float()
    site_deduction = fields.Float()
    overtime_deduction = fields.Float()
    deduction_settlements = fields.Float()
    loan_deduction = fields.Float()

    @api.depends('employee_id')
    def _get_employee_running_contract(self):
        for rec in self:
            if rec.employee_id:
                rec.contract_id = rec.employee_id.contract_id.id
                rec.employee_type = rec.employee_id.wassef_employee_type
            else:
                rec.contract_id = None
                rec.employee_type = None
