import logging
from odoo import models, fields, api, _
from datetime import datetime, time
from dateutil import tz
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from odoo.addons.ake_attendance_sheet.tools.custom_dateutil import convert_to_timezone, time_to_float
import pytz

_logger = logging.getLogger(__name__)


class HRAttendanceCustom(models.Model):
    _name = 'hr.attendance'
    _inherit = ['hr.attendance', 'mail.thread', 'mail.activity.mixin']

    is_late_check_in = fields.Boolean("Late Check In")
    is_early_check_out = fields.Boolean("Early check out")
    justification = fields.Text("Justification")
    justification_type_id = fields.Many2one("justification.type", "Justification Type")
    attendance_status = fields.Selection([
        ('department_manager_approve', 'Department Manager'),
        ('hr_manager', 'HR Manager'),
        ('approved', 'Approved'), ('rejected', 'Rejected')], string='Activity State Late',
        default='department_manager_approve', readonly=True)
    attendance_status_early = fields.Selection([
        ('department_manager_approve', 'Department Manager'),
        ('hr_manager', 'HR Manager'),
        ('approved', 'Approved'), ('rejected', 'Rejected')], string='Activity State Early',
        default='department_manager_approve', readonly=True)
    early_check_out_hour = fields.Float(string="Early check out hour")
    late_check_in_hour = fields.Float(string="Late check in hour")
    early_check_store = fields.Float(string="Early check out hour")
    late_check_store = fields.Float(string="Late check in hour")
    is_early_check_out_hour_added = fields.Boolean(string="Is early check out hour added")
    is_late_check_in_hour_added = fields.Boolean(string="is late check in hour added")
    leave_id = fields.Many2one('hr.leave', string="Leave")
    can_approve_attendance = fields.Boolean(string="Have Approve Permission",
                                            compute="_compute_can_approve_attendance")
    attendance_sheet_id = fields.Many2one('hr.attendance.sheet')
    reject_after = fields.Integer(string="Reject After")
    total_late_early_hours = fields.Float(string="Total Violation Hours", compute="_get_total_violation_hours",
                                          store=True)
    total_hours = fields.Float(string="Total Hours", compute="_get_total_hours", store=True)

    @api.depends("early_check_store", "late_check_store")
    def _get_total_violation_hours(self):
        for rec in self:
            if rec.early_check_store or rec.late_check_store:
                rec.total_late_early_hours = rec.early_check_store + rec.late_check_store
            else:
                rec.total_late_early_hours = 0

    @api.depends("early_check_out_hour", "late_check_in_hour")
    def _get_total_hours(self):
        for rec in self:
            if rec.early_check_out_hour or rec.late_check_in_hour:
                rec.total_hours = rec.early_check_out_hour + rec.late_check_in_hour
            else:
                rec.total_hours = 0

    def _compute_can_approve_attendance(self):
        for attend in self:
            attend.can_approve_attendance = False
            if attend.employee_id.parent_id.sudo().user_id == self.env.user and \
                    (attend.is_late_check_in or attend.is_early_check_out):
                attend.can_approve_attendance = True

    def _enable_late_check_in(self, late_check_in_hours):
        """Enable late check in fields
        @param late_check_in_hours: Late check in hours of attendance
        """
        self.ensure_one()
        self.late_check_in_hour = late_check_in_hours
        self.late_check_store = late_check_in_hours
        self.is_late_check_in = True
        self.is_late_check_in_hour_added = False
        # self.activity_update('add_late_check_in')

    def _disable_late_check_in(self):
        """Disable late check in fields"""
        self.ensure_one()
        self.is_late_check_in = False
        self.late_check_in_hour = 0
        self.is_late_check_in_hour_added = False
        # self.activity_update('remove_late_check_in')

    def _enable_early_check_out(self, early_check_out_hours):
        """Enable early check out fields
        @param early_check_out_hours: Early check out hours of attendance
        """
        self.ensure_one()
        self.early_check_out_hour = early_check_out_hours
        self.early_check_store = early_check_out_hours
        self.is_early_check_out = True
        self.is_early_check_out_hour_added = False
        # manager_id = employee_attendaces.employee_id.parent_id
        # users = employee_attendaces._get_users_late_attendance()
        # self.activity_update('add_early_check_out')

    def _disable_early_check_out(self):
        """Disable early check out fields"""
        self.ensure_one()
        self.early_check_out_hour = 0
        self.is_early_check_out = False
        self.is_early_check_out_hour_added = False
        # self.activity_update('remove_early_check_out')

    @api.constrains('check_in', 'check_out')
    def _check_late_in_early_out(self):
        attendance_days = [attendance.check_in.date() for attendance in self]
        unique_attendance_days = list(set(attendance_days))
        unique_attendance_days.sort()
        employees = self.filtered(lambda attendance: not attendance.employee_id.out_of_attendance).mapped('employee_id')
        attendance_from_date = datetime.combine(unique_attendance_days[0], time(0, 0, 0))
        attendance_to_date = datetime.combine(unique_attendance_days[-1], time(23, 59, 59))
        domain = [('check_in', '>=', attendance_from_date), ('check_in', '<=', attendance_to_date),
                  ('employee_id', 'in', employees.ids)]

        all_days_attendance = self.env['hr.attendance'].search(domain, order='check_in')

        for employee in self.mapped('employee_id'):
            for day in unique_attendance_days:
                all_day_attendance = all_days_attendance.filtered(
                    lambda attendance: attendance.employee_id == employee and attendance.check_in.date() == day).sorted(
                    'check_in')

                first_check_in_record = all_day_attendance[0] if all_day_attendance else False
                if first_check_in_record and not first_check_in_record.employee_id.out_of_attendance:
                    first_check_in_record.get_late_checkin_attendance()

                # as check out field not required
                last_check_out_record = all_day_attendance[-1] if all_day_attendance else False

                for record in reversed(range(len(all_day_attendance))):
                    if all_day_attendance[record].check_out:
                        last_check_out_record = all_day_attendance[record]
                        break

                if last_check_out_record and last_check_out_record.check_out and \
                        not last_check_out_record.employee_id.out_of_attendance:
                    last_check_out_record.get_early_check_out_attendance()

        self.env['hr.attendance'].reject_justification_after_time()

    def get_late_checkin_attendance(self):
        """Check if attendance is late form expected based on employee calendar"""
        self.ensure_one()
        employee_attendance = self
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz('Asia/Qatar' or self._context.get('tz'))
        _logger.info("to_zone {}".format(to_zone))
        attendance_checkin_utc = datetime.strptime(str(employee_attendance.check_in), '%Y-%m-%d %H:%M:%S')
        attendance_checkin_utc = attendance_checkin_utc.replace(tzinfo=from_zone)
        attendance_checkin_central = attendance_checkin_utc.astimezone(to_zone)
        _logger.info("attendance_checkin_utc {}, attendance_checkin_central {}".
                     format(attendance_checkin_utc, attendance_checkin_central))
        # and dict(x._fields['day_period'].selection).get(x.day_period) == 'Morning'
        attend_time_minutes = attendance_checkin_central.time().hour + (
                attendance_checkin_central.time().minute / 60)
        # get morning
        calendar_attend = employee_attendance.employee_id.resource_calendar_id.attendance_ids.filtered(
            lambda x: dict(x._fields['dayofweek'].selection).get(
                x.dayofweek) == attendance_checkin_central.strftime('%A')
                      and x.day_period == 'morning'
        )
        _logger.info("attend_time_minutes {}, calendar_attend {}".
                     format(attend_time_minutes, calendar_attend))
        if len(calendar_attend) > 1:
            calendar_attend = calendar_attend[0]
        if calendar_attend and attend_time_minutes > calendar_attend.hour_from:
            diff = attend_time_minutes - calendar_attend.hour_from
            justification = self.env['justification.type'].search([
                ('daily_grace_period', '=', True), ('to_time', '!=', False)
            ])
            is_allowed_late = justification.is_checked_in_justification(attend_time_minutes,
                                                                        calendar_attend.hour_from)
            if not is_allowed_late:
                diff = diff - justification.to_time if diff > justification.to_time else diff
                employee_attendance.justification_type_id = False
                today_date_time = attendance_checkin_central.replace(hour=0, minute=0, second=0)
                leaves = self.env['hr.leave'].sudo().search(
                    [('employee_id', '=', employee_attendance[0].employee_id.id),
                     ('request_date_from', '<=', attendance_checkin_utc.date()),
                     ('request_date_to', '>=', attendance_checkin_utc.date()),
                     ('state', '=', 'validate')
                     ])
                public_holiday = employee_attendance.employee_id.contract_id.resource_calendar_id.global_leave_ids.filtered(
                    lambda x: x.date_from.date() <= attendance_checkin_utc.date() <= x.date_to.date()) \
                    if employee_attendance.employee_id.contract_id else False
                if public_holiday:
                    public_holiday_morning = public_holiday.filtered(
                        lambda x: x.date_from.astimezone(to_zone).time().hour <= calendar_attend.hour_from)
                    if public_holiday_morning:
                        if attendance_checkin_utc <= public_holiday_morning.date_to.replace(tzinfo=from_zone):
                            employee_attendance._disable_late_check_in()
                        else:
                            public_holiday_diff = (attendance_checkin_central.time().hour + (
                                    attendance_checkin_central.time().minute / 60)) - (
                                                          public_holiday_morning.date_to.astimezone(
                                                              to_zone).time().hour + (
                                                                  public_holiday_morning.date_to.astimezone(
                                                                      to_zone).time().minute / 60))
                            employee_attendance._enable_late_check_in(public_holiday_diff)

                elif leaves:
                    for leave in leaves:
                        hour_from = time_to_float(leave.date_from.astimezone(to_zone).time())
                        if hour_from == calendar_attend.hour_from:
                            if diff > leave.number_of_hours_display:
                                employee_attendance.leave_id = leave.id
                                remaining_diff_after_leave = diff - leave.number_of_hours_display
                                employee_attendance._enable_late_check_in(remaining_diff_after_leave)
                            else:
                                employee_attendance._disable_late_check_in()
                        else:
                            employee_attendance._enable_late_check_in(diff)
                else:
                    employee_attendance._enable_late_check_in(diff)
            else:
                employee_attendance.justification_type_id = justification.id
                employee_attendance._disable_late_check_in()
        else:
            employee_attendance._disable_late_check_in()
            # check if existing attendance sheet record
            if employee_attendance.attendance_sheet_id:
                employee_attendance.attendance_sheet_id.remove_late_check_in()

    def get_early_check_out_attendance(self):
        """Check if attendance is earlier than expected based on employee calendar"""
        self.ensure_one()
        employee_attendance = self
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz('Asia/Qatar' or self._context.get('tz'))
        _logger.info("to_zone {}".format(to_zone))
        attendance_checkout_utc = datetime.strptime(str(employee_attendance.check_out), '%Y-%m-%d %H:%M:%S')
        attendance_checkout_utc = attendance_checkout_utc.replace(tzinfo=from_zone)
        attendance_checkout_central = attendance_checkout_utc.astimezone(to_zone)
        # get afternoon calendar
        evening_data = employee_attendance.employee_id.resource_calendar_id.attendance_ids.filtered(
            lambda x: dict(x._fields['dayofweek'].selection).get(x.dayofweek) == attendance_checkout_central.strftime(
                '%A') and x.day_period == 'afternoon')
        if len(evening_data) > 1:
            evening_data = evening_data[0]
        time_in_minutes = employee_attendance.check_out and \
                          attendance_checkout_central.time().hour + \
                          (attendance_checkout_central.time().minute / 60)
        if time_in_minutes < evening_data.hour_to:
            diff = evening_data.hour_to - time_in_minutes
            today_date_time = attendance_checkout_central.replace(hour=int(evening_data.hour_to), minute=59,
                                                                  second=59)
            leaves = self.env['hr.leave'].sudo().search(
                [('employee_id', '=', employee_attendance[-1].employee_id.id),
                 ('request_date_from', '<=', attendance_checkout_utc.date()),
                 ('request_date_to', '>=', attendance_checkout_utc.date()),
                 ('state', '=', 'validate')])
            public_holiday = employee_attendance.employee_id.contract_id.resource_calendar_id.global_leave_ids.filtered(
                lambda x: x.date_from.date() <= attendance_checkout_central.date() <= x.date_to.date()) \
                if employee_attendance.employee_id.contract_id else False

            if public_holiday:
                public_holiday_evening = public_holiday.filtered(
                    lambda x: x.date_to.astimezone(to_zone).time().hour >= evening_data.hour_to)
                if public_holiday_evening:
                    if attendance_checkout_utc <= public_holiday_evening.date_to.replace(tzinfo=from_zone):
                        employee_attendance._disable_early_check_out()
                    else:
                        public_holiday_diff = (public_holiday_evening.date_to.astimezone(to_zone).time().hour + (
                                                       public_holiday_evening.date_to.astimezone(
                                                           to_zone).time().minute / 60)) - (
                                                      attendance_checkout_central.time().hour + (
                                                      attendance_checkout_central.time().minute / 60))
                        employee_attendance._enable_early_check_out(public_holiday_diff)
            elif leaves:
                for leave in leaves:
                    hour_to = time_to_float(leave.date_to.astimezone(to_zone).time())
                    if hour_to >= evening_data.hour_to:
                        employee_attendance.leave_id = leave.id
                        if diff > leave.number_of_hours_display:
                            employee_attendance.leave_id = leave.id
                            remaining_diff_after_leave = diff - leave.number_of_hours_display
                            employee_attendance._enable_early_check_out(remaining_diff_after_leave)
                        else:
                            employee_attendance._disable_early_check_out()
                    else:
                        employee_attendance._enable_early_check_out(diff)

            else:
                employee_attendance._enable_early_check_out(diff)
        else:
            employee_attendance._disable_early_check_out()
            # check if existing attendance sheet record
            if employee_attendance.attendance_sheet_id:
                employee_attendance.attendance_sheet_id.remove_early_check_out()

    def action_department_manager_approve(self):
        if self.env.user.id == self.employee_id.parent_id.user_id.id or \
                self.user_has_groups('hr_attendance.group_hr_attendance_user'):
            action = self.env.ref('ake_early_late_attandence.approve_late_early_attendance_wizard').sudo().read()[0]
            return action
        else:
            raise UserError("Only Employee Manager and Officer Attendance Can Approve.")

    def action_manager_refuse(self):
        if self.env.user.id == self.employee_id.parent_id.user_id.id or \
                self.user_has_groups('hr_attendance.group_hr_attendance_user'):
            action = self.env.ref('ake_early_late_attandence.action_justification_attendance_wizard').sudo().read()[0]
            return action
        else:
            raise UserError("Only Employee Manager and Officer Attendance Can Approve.")

    def _get_user_approval_activities(self, user, activity_type_id):
        domain = [
            ('res_model', '=', 'hr.attendance'),
            ('res_id', 'in', self.ids),
            ('activity_type_id', '=', activity_type_id),
            ('user_id', '=', user.id)
        ]
        activities = self.env['mail.activity'].search(domain)
        return activities

    def _get_users_late_attendance(self):
        """Retrieve the manager's user and the users of attendance administrators groups"""
        self.ensure_one()
        return self.employee_id.sudo().parent_id.user_id

    def activity_update(self, state=''):
        """Update the activity of approve or refuse and when change attendance check in or check out.
         @param state: the state of attendance can be add_late_check_in,add_early_check_out,
                       remove_late_check_in,remove_early_check_out
         """
        for attend in self:
            #  send notification for manager of employee and employee
            users = attend._get_users_late_attendance()
            if state == 'add_late_check_in':
                note = _(
                    'New Attendance %(name)s late check in on employee %(employee)s',
                    name=attend.name_get()[0][1],
                    employee=attend.employee_id.name,
                )
                for user in users:
                    attend.activity_schedule(
                        'ake_early_late_attandence.mail_activity_approve_late_check_in_attendance',
                        note=note,
                        user_id=user.id)
                """ Committed This Part of code to fix issue with user(SamehAli) In Create Attendance Action  """
                # if attend.employee_id.user_id:
                #     note = _('You have late check in on {}'.format(attend.check_in.strftime("%Y-%m-%d")))
                #     attend.activity_schedule(
                #         'ake_early_late_attandence.mail_activity_approve_late_check_in_attendance',
                #         note=note,
                #         user_id=attend.employee_id.user_id.id)
            elif state == 'remove_late_check_in':
                attend.activity_unlink([
                    'ake_early_late_attandence.mail_activity_approve_late_check_in_attendance'
                ])
            elif state == 'add_early_check_out':
                note = _(
                    'New Attendance %(name)s early check out on employee %(employee)s',
                    name=attend.name_get()[0][1],
                    employee=attend.employee_id.name,
                )
                for user in users:
                    attend.activity_schedule(
                        'ake_early_late_attandence.mail_activity_approve_early_check_out_attendance',
                        note=note,
                        user_id=user.id)
                """ Committed This Part of code to fix issue with user(SamehAli) In Create Attendance Action  """
                # if attend.employee_id.user_id:
                #     note = _('You have early check out on {}'.format(attend.check_out.strftime("%Y-%m-%d")))
                #     attend.activity_schedule(
                #         'ake_early_late_attandence.mail_activity_approve_late_check_in_attendance',
                #         note=note,
                #         user_id=attend.employee_id.user_id.id)
            elif state == 'remove_early_check_out':
                attend.activity_unlink([
                    'ake_early_late_attandence.mail_activity_approve_early_check_out_attendance'
                ])
            else:
                attend.activity_unlink([
                    'ake_early_late_attandence.mail_activity_approve_early_check_out_attendance',
                    'ake_early_late_attandence.mail_activity_approve_late_check_in_attendance'
                ])

    @api.model
    def reject_justification_after_time(self):
        justifications = self.search(['|', ('is_late_check_in', '=', True), ('is_early_check_out', '=', True),
                                      ('attendance_status', 'not in', ['approved', 'rejected'])]). \
            filtered(lambda justification: justification.reject_after and \
                                           (justification.create_date + relativedelta(
                                               days=justification.reject_after)).date() <= fields.Date.today())
        for justification in justifications:
            all_day_attendance = self.env['hr.attendance']
            attendance_day_start = justification.check_in.replace(hour=0, minute=0, second=0).astimezone(
                pytz.UTC).replace(tzinfo=None).strftime('%Y-%m-%d %H:%M:%S')
            attendance_day_end = justification.check_in.replace(hour=23, minute=59, second=59).astimezone(
                pytz.UTC).replace(tzinfo=None).strftime('%Y-%m-%d %H:%M:%S')
            query = """SELECT id FROM hr_attendance WHERE employee_id = %s AND check_in BETWEEN %s AND %s """
            self._cr.execute(query, (justification.employee_id.id, attendance_day_start, attendance_day_end))
            existing_record_ids = self._cr.fetchall()
            if existing_record_ids:
                existing_record_ids = [rec_id[0] for rec_id in list(existing_record_ids)]
                all_day_attendance = self.env['hr.attendance'].browse(existing_record_ids).sorted('check_in')
            from_zone = tz.gettz('UTC')
            to_zone = tz.gettz('Asia/Qatar' or self._context.get('tz'))
            justification_checkin_utc = justification.check_in and \
                                        datetime.strptime(str(justification.check_in), '%Y-%m-%d %H:%M:%S').replace(
                                            tzinfo=from_zone)
            justification_checkout_utc = justification.check_out and \
                                         datetime.strptime(str(justification.check_out), '%Y-%m-%d %H:%M:%S').replace(
                                             tzinfo=from_zone)
            justification_checkin_central = justification_checkin_utc and \
                                            justification_checkin_utc.astimezone(to_zone)
            justification_checkout_central = justification_checkout_utc and \
                                             justification_checkout_utc.astimezone(to_zone)
            # activity = self.env.ref('ake_early_late_attandence.mail_activity_approve_attendance').id
            # attendance.sudo()._get_user_approval_activities(user=self.env.user, activity_type_id=activity).action_feedback()
            justification_date = justification_checkin_utc.date().strftime("%Y-%m-%d")
            if all_day_attendance:
                qatar_tz = pytz.timezone('Asia/Qatar')
                check_in = all_day_attendance[0].check_in.astimezone(qatar_tz).replace(tzinfo=None)
                check_out = all_day_attendance[-1].check_out.astimezone(qatar_tz).replace(tzinfo=None)
            else:
                check_in = justification_checkin_central
                check_out = justification_checkout_central
            vals = {
                "check_in": time_to_float(check_in),
                "check_out": time_to_float(check_out),
                "attendance_id": justification.id
            }

            if justification.is_early_check_out and justification.early_check_out_hour > 0.0:
                vals.update({
                    "early_check_out": justification.early_check_out_hour,
                })
                justification.attendance_sheet_id = justification.employee_id.updated_or_create_attendance_sheet(
                    attendance_date=justification_date,
                    **vals)
                justification.is_early_check_out_hour_added = True
                justification.is_early_check_out = False
                justification.activity_update('remove_early_check_out')

            if justification.is_late_check_in and justification.late_check_in_hour > 0.0:
                # violation_hours = attendance.employee_id.violation_hours + attendance.late_check_in_hour
                # attendance.employee_id.sudo().write({'violation_hours': violation_hours})
                vals.update({
                    "late_check_in": justification.late_check_in_hour,
                })
                justification.attendance_sheet_id = justification.employee_id.updated_or_create_attendance_sheet(
                    attendance_date=justification_date,
                    **vals)
                justification.is_late_check_in_hour_added = True
                justification.is_late_check_in = False
                justification.activity_update('remove_late_check_in')

            justification.attendance_status = 'rejected'


class JustificationType(models.Model):
    _name = 'justification.type'

    def default_justification_type(self):
        justification_types = self.search([('default_justification_type', '=', True)])
        if justification_types:
            return False
        return True

    def default_affects_casual_leave(self):
        casual_leave_type = self.env['hr.leave.type'].search([('is_casual_leave_type', '=', True)])
        if casual_leave_type:
            return True
        else:
            return False

    name = fields.Char("Name")
    operation = fields.Selection([('gt', '>'), ('lt', '<'), ('between', 'Between')], string="Operation", default=">")
    category = fields.Selection([('official', 'Official'), ('personal', 'Personal')], string="Category",
                                default="official")
    from_time = fields.Float(string="From time")
    to_time = fields.Float(string="To time")
    affects_attendance = fields.Boolean(string="Affects Attendance")
    affects_casual_leave = fields.Boolean(string="Affects Casual Leave", default=default_affects_casual_leave)
    payroll_salary = fields.Selection(
        [('does_not_affect', 'Does not affect'),
         ('after_leave_balance_consumed', 'after leave balance is consumed'),
         ('affects_payroll', 'affects payroll')], string="Payroll Salary")
    default_justification_type = fields.Boolean(string="Default justification type",
                                                default=default_justification_type)
    code = fields.Char("Char")
    daily_grace_period = fields.Boolean(string="Daily Grace Period")

    def is_checked_in_justification(self, check_in_time, check_in_calendar):
        """Check if check_in is located on the interval of justification time"""
        allow_time = check_in_calendar + self.to_time
        if self.operation == 'gt':
            return check_in_time >= check_in_calendar
        elif self.operation in ['lt', 'between']:
            return check_in_time <= allow_time

    # duration = fields.Float(string="Duration", compute="compute_duration")
    #
    # @api.depends('from_time', 'to_time')
    # def compute_duration(self):
    #     for record in self:
    #         if record.from_time > record.to_time:
    #             record.duration = record.from_time - record.to_time
    #         elif record.to_time > record.from_time:
    #             record.duration = record.to_time - record.from_time
