from odoo import models, fields, api
from datetime import datetime, date, timedelta, time
import pytz


class InheritHrLeave(models.Model):
    _inherit = 'hr.leave'

    @api.model_create_multi
    def create(self, vals_list):
        holidays = super(InheritHrLeave, self).create(vals_list)
        for holiday in holidays:
            message = f"تم تقديم طلب الإجازة ({holiday.holiday_status_id.with_context(lang='ar_001').name}) بتاريخ من {holiday.request_date_from} إلى {holiday.request_date_to} للموظف {holiday.employee_ids.arabic_name if holiday.employee_ids.arabic_name else ''}"  # message = "تم تقديم طلب الإجازة {} بتاريخ من {}".format(
            # print("message:", message)
            for employee in holiday.sudo().employee_ids:
                user = employee.sudo().leave_manager_id
                if user:
                    employee_manager = self.env['hr.employee'].search([('user_id', '=', user.id)])
                    # employee_manager.sudo().with_context(message=message).send_sms_message()
                # employee.sudo().with_context(message=message).send_sms_message()
        return holidays

    def action_validate(self):
        if self.sudo().employee_ids:
            employee_model = self.sudo().env['ir.model'].search([
                ('model', '=', 'hr.employee')
            ])
            if employee_model:
                ooredo_employee_conf = self.sudo().env['dynamic.integration.configuration'].sudo().search([
                    ('model_id', '=', employee_model.id)
                ])
                if ooredo_employee_conf:
                    message = f")تم اعتماد طلب الإجازة {self.holiday_status_id.with_context(lang='ar_001').name} بتاريخ من ({self.request_date_from} إلي {self.request_date_to}"
                    message = "تم اعتماد طلب الإجازة (%s) بتاريخ من %s إلى %s " % (
                    self.holiday_status_id.with_context(lang="ar_001").name, self.request_date_from,
                    self.request_date_to)
                    # for employee in self.sudo().employee_ids:
                    #     employee.sudo().with_context(message=message).send_sms_message()
        res = super(InheritHrLeave, self).action_validate()
        if self.state == 'validate':

            domain = [('punch_date', '>=', self.request_date_from), ('punch_date', '<=', self.request_date_to),
                      ('state', '=', 'success')]
            domain.append(('employee_id', 'in', self.sudo().employee_ids.ids))
            matching_machine_records = self.env['machine.attendance.record'].sudo().search(domain)
            if matching_machine_records:
                today = date.today()
                if today.year == self.request_date_from.year and today.month == self.request_date_from.month:
                    if today.day - self.request_date_from.day <= int(
                            self.env['ir.config_parameter'].sudo().get_param('max_days_to_approve')):
                        to_date_time = datetime.combine(self.request_date_to, time(23, 59, 59))
                        domain = [('employee_id', 'in', self.sudo().employee_ids.ids), ('check_in', '<=', to_date_time)]
                        if self.request_date_from:
                            from_date_time = datetime.combine(self.request_date_from, time(0, 0, 0))
                            domain.append(('check_in', '>=', from_date_time))

                        self.env['hr.attendance'].search(domain).sudo().unlink()

                        self.env['hr.attendance'].with_context(cron_job=False).download_attendance_from_machine(
                            self.request_date_from,
                            self.request_date_to,
                            self.sudo().employee_ids
                        )
                        violation_allocation = self.env['hr.leave.allocation'].search(
                            [('employee_id', '=', self.employee_id.id), ('date_from', '>=', self.request_date_from), ('date_from', '<=', self.request_date_to),
                             ('created_from_violation_hours', '=', True), ('state', '=', 'validate')])
                        if violation_allocation:
                            violation_allocation.sudo().write({'state': 'draft'})
                            violation_allocation.sudo().unlink()
                            self.employee_id.sudo().counter -= 1

        return res

    def action_refuse(self):
        if self.sudo().employee_ids:
            employee_model = self.sudo().env['ir.model'].search([
                ('model', '=', 'hr.employee')
            ])
            if employee_model:
                ooredo_employee_conf = self.sudo().env['dynamic.integration.configuration'].sudo().search([
                    ('model_id', '=', employee_model.id)
                ])
                if ooredo_employee_conf:
                    message = "تم رفض طلب الإجازة (%s) بتاريخ من %s إلى %s " % (
                        self.holiday_status_id.with_context(lang="ar_001").name, self.request_date_from,
                        self.request_date_to)
                    for employee in self.sudo().employee_ids:
                        employee.sudo().with_context(message=message).send_sms_message()
        return super(InheritHrLeave, self).action_refuse()
