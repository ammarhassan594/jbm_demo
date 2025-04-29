from odoo import fields, models, api
from dateutil.relativedelta import relativedelta
from datetime import date, datetime, timedelta
import logging
_logger = logging.getLogger(__name__)


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    ignore_hours_violation = fields.Boolean()

    def get_attendance_deduction(self, payslip, employee):
        amount = 0
        if not payslip.ignore_hours_violation:
            if not employee.out_of_attendance:
                self.env['hr.employee']._daily_exceed_allowed_hours()
                total_violation_hours = employee.exceed_allowed_violation_balance
                while total_violation_hours >= employee.resource_calendar_id.reference_violation:
                    amount += self.calculate_violation_hours_amount(employee, employee.resource_calendar_id.reference_violation)
                    total_violation_hours -= employee.resource_calendar_id.reference_violation
                    employee.counter += 1

        return amount

    def get_total_violation_hours(self, payslip, employee):
        if payslip.payslip_run_id:
            date_from = payslip.payslip_run_id.cust_off_date_to - timedelta(days= payslip.payslip_run_id.cust_off_date_to.day - 1)
            # date_from = payslip.payslip_run_id.cust_off_date_from
            date_to = payslip.payslip_run_id.cust_off_date_to
        else:
            date_from = payslip.date_from
            date_to = payslip.date_to
        total_violation_hours = 0
        attend_sheet_lines = self.env['hr.attendance.sheet'].search([
            ('employee_id', '=', employee.id),
            ('date', '>=', date_from),
            ('date', '<=', date_to)
        ])
        if attend_sheet_lines:
            total_late_hours = sum(attend_sheet_lines.mapped('late_check_in'))
            total_early_hours = sum(attend_sheet_lines.mapped('early_check_out'))
            total_break_hours = sum(attend_sheet_lines.mapped('break_time'))
            total_violation_hours += total_late_hours + total_early_hours + total_break_hours
        return total_violation_hours

    # def get_previous_month_hours(self, payslip, employee):
    #     month = payslip.date_to.month - 1
    #     violation_balance = self.env['violation.balance'].search([
    #         ('employee_id', '=', employee.id),
    #     ])
    #     violation_balance.filtered(lambda x: x.date.month == month)
    #     if violation_balance:
    #         return violation_balance.next_month_hours
    #     else:
    #         return 0

    def calculate_violation_hours_amount(self, employee, total_violation_hours):
        total_hour_deducted_wage = 0
        contract = employee.contract_id if employee.contract_id.state == 'open' else \
            self.env['hr.contract'].search([
                ('employee_id', '=', employee.id), ('state', '=', 'open')], limit=1)
        basic_salary = contract and contract.wage or 0.0
        calendar = contract.resource_calendar_id or employee.resource_calendar_id
        hours_per_day = calendar and calendar.hours_per_day or 0
        working_days = calendar and 30 or 0
        one_hour_wage = basic_salary / working_days / hours_per_day
        total_hour_deducted_wage += one_hour_wage * total_violation_hours

        return total_hour_deducted_wage

    def create_casual_allocation(self,payslip, employee, hours, date_to):
        pass
        # leave_type = self.env['hr.leave.type'].search([('is_casual_leave_type','=', True)])
        # res = {'name': 'Allocation to settle Violation hours',
        #        'date_from': date_to + relativedelta(days=1),
        #        'number_of_days': -(hours / employee.sudo().resource_calendar_id.hours_per_day),
        #        'employee_id': employee.id,
        #        'allocation_type': 'regular',
        #        'holiday_status_id': leave_type.id,
        #        'payslip_id': payslip.id
        #        # 'number_of_hours_display': -hours / employee.sudo().resource_calendar_id.hours_per_day
        #        }
        # allocation = self.env['hr.leave.allocation'].create(res)
        # allocation.write({'state': 'validate'})

