# -*- coding: utf-8 -*-
import datetime

from odoo import models, fields, api, _


class HrEmployeeCustom(models.Model):
    _inherit = "hr.employee"

    violation_hours = fields.Float(string="Violation hours")
    justification_type_ids = fields.Many2many('justification.type', string="Justification type")
    is_request_approval = fields.Boolean(string="Is request approval")

    def send_notification_violation(self):
        employees = self.search([('violation_hours', '>', 0), ('parent_id', '!=', False)])
        justification_types = self.env['justification.type'].search([])
        first_priority_justification_types = justification_types.filtered(lambda s: s.operation == 'lt')
        second_priority_justification_types = justification_types.filtered(lambda s: s.operation == 'between')
        third_priority_justification_types = justification_types.filtered(lambda s: s.operation == 'gt')
        if first_priority_justification_types:
            for first_priority_justification_type in first_priority_justification_types.sorted(lambda s: s.to_time):
                filtered_employees = employees.filtered(
                    lambda s: s.violation_hours < first_priority_justification_type.to_time)
                for employee in filtered_employees:
                    if first_priority_justification_type not in employee.justification_type_ids:
                        employee.activity_schedule(
                            'ake_early_late_attandence.mail_activity_notification_violation_hour',
                            user_id=employee.parent_id.user_id.id)
                        employee.sudo().justification_type_ids = [(4, first_priority_justification_type.id)]
                        employee.is_request_approval = True
                        employees -= employee
        if second_priority_justification_types:
            for second_priority_justification_type in second_priority_justification_types.sorted(lambda s: s.to_time):
                filtered_employees = employees.filtered(lambda
                                                            s: second_priority_justification_type.from_time < s.violation_hours < second_priority_justification_type.to_time)
                for employee in filtered_employees:
                    if second_priority_justification_type not in employee.justification_type_ids:
                        employee.activity_schedule(
                            'ake_early_late_attandence.mail_activity_notification_violation_hour',
                            user_id=employee.parent_id.user_id.id)
                        employee.sudo().justification_type_ids = [(4, second_priority_justification_type.id)]
                        employee.is_request_approval = True
                        employees -= employee
        if third_priority_justification_types:
            for third_priority_justification_type in third_priority_justification_types.sorted(lambda s: s.from_time):
                filtered_employees = employees.filtered(
                    lambda s: s.violation_hours > third_priority_justification_type.from_time)
                for employee in filtered_employees:
                    if third_priority_justification_type not in employee.justification_type_ids:
                        employee.activity_schedule(
                            'ake_early_late_attandence.mail_activity_notification_violation_hour',
                            user_id=employee.parent_id.user_id.id)
                        employee.sudo().justification_type_ids = [(4, third_priority_justification_type.id)]
                        employee.is_request_approval = True
                        employees -= employee

    def approve_violation_hour(self):
        self.violation_hours = 0.0
        self.justification_type_ids = False
        self.action_done_activities()
        self.is_request_approval = False

    def refuse_violation_hour(self):
        self.action_done_activities()
        self.is_request_approval = False

    def action_done_activities(self):
        activity_type_id = self.env.ref('ake_early_late_attandence.mail_activity_notification_violation_hour').id
        domain = [
            ('res_model', '=', 'hr.employee'),
            ('res_id', 'in', self.ids),
            ('activity_type_id', '=', activity_type_id),
            ('user_id', '=', self.env.user.id)
        ]
        activities = self.env['mail.activity'].search(domain)
        activities.action_feedback()

    def deduct_leave_balance_from_employee(self):
        employees = self.search([('violation_hours', '>', 0),
                                 ('justification_type_ids', '!=', False)])
        for employee in employees:
            print('-----------------------------------', employee.name)
            casual_leave_type_justification = employee.justification_type_ids.filtered(lambda s: s.affects_casual_leave)
            if casual_leave_type_justification:
                casual_leave_type = self.env['hr.leave.type'].sudo().search([('is_casual_leave_type', '=', True)])
                if casual_leave_type:
                    employee_leave_allocations = self.env['hr.leave.allocation'].sudo().search(
                        [('employee_id', '=', employee.id),
                         ('holiday_status_id', '=', casual_leave_type.id),
                         ('state', '=', 'validate'),
                         '|',
                         ('date_to', '=', False),
                         ('date_to', '>=', datetime.date.today())])
                    if employee_leave_allocations:
                        for employee_leave_allocation in employee_leave_allocations:
                            leave_hours = sum(
                                employee_leave_allocation.taken_leave_ids.mapped('number_of_hours_display'))
                            remaining_leave_balance = employee_leave_allocation.number_of_hours_display - leave_hours
                            if remaining_leave_balance > employee.violation_hours:
                                date_from = datetime.date.today().replace(day=1)
                                date_to = datetime.date.today()
                                attendance_from_date = datetime.datetime.now().replace(day=1, hour=0, minute=0,
                                                                                       second=0)
                                attendance_to_date = datetime.datetime.now().replace(hour=23, minute=59, second=59)
                                attendance_ids = self.env['hr.attendance'].sudo().search(
                                    [('employee_id', '=', employee.id), ('check_in', '>=', attendance_from_date),
                                     ('check_in', '<=', attendance_to_date),
                                     '|',
                                     ('is_early_check_out_hour_added', '=', True),
                                     ('is_late_check_in_hour_added', '=', True)
                                     ])
                                vals = {
                                    'employee_id': employee.id,
                                    'date_from': date_from,
                                    'date_to': date_to,
                                    'violation_hours': employee.violation_hours,
                                    'casual_leave_justification_types': [(6, 0, casual_leave_type_justification.ids)],
                                    'attendance_ids': [(6, 0, attendance_ids.ids)],
                                    'casual_leave_allocation_id': employee_leave_allocation.id

                                }
                                record = self.env['employee.shortage.hour'].sudo().create(vals)
                                if record:
                                    record.approve_employee_shortage_hour()
                                # current_leave_balance = remaining_leave_balance - employee.violation_hours
                                #
                                # if employee.resource_calendar_id and employee.resource_calendar_id.hours_per_day > 0:
                                #     number_of_days = current_leave_balance / employee.resource_calendar_id.hours_per_day
                                # else:
                                #     number_of_days = current_leave_balance / 8
                                # employee_leave_allocation.sudo().write(
                                #     {'number_of_days': number_of_days})
                                # employee.sudo().write({'violation_hours': 0.0, 'justification_type_ids': False})
                                break
            print('-------------------------------------------------')
