
from odoo import models, api, fields


class Payslip(models.Model):
    _inherit = 'hr.payslip'

    def calculate_overtime_amount(self, payslip, employee):
        special_ot = 0
        normal_ot = 0
        overtime_allowance = 0
        if payslip:
            overtime = self.env['hr.overtime'].search([('state', '=', 'approved'),
                                                       ('date_from', '>=', payslip.date_from),
                                                       ('date_to', '<=', payslip.date_to),
                                                       ('employee_id', '=', employee.id)], limit=1)
            normal_rate = self.env['overtime.rate'].search([('type', '=', 'normal')], limit=1).rate
            special_rate = self.env['overtime.rate'].search([('type', '=', 'special')], limit=1).rate
            normal_ot += overtime.t_normal_hours
            special_ot += overtime.t_special_hours
            total_hours = normal_ot + special_ot
            hour_wage = employee.contract_id.wage / 21.75 / 8
            overtime_allowance += (special_ot * special_rate * hour_wage) + (normal_ot * normal_rate * hour_wage)
        return overtime_allowance

