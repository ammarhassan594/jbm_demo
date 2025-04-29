# -*- coding: utf-8 -*-
import base64
import calendar
import pytz
from dateutil.relativedelta import relativedelta

from datetime import datetime, date, time

from odoo import http
from odoo.http import request


def float_to_hours_minutes(float_hours):
    hours = int(float_hours)
    minutes = int((float_hours - hours) * 60)
    return f"{hours:02}:{minutes:02}"


def parse_date(date_string):
    try:
        # Try to parse with time format
        new_date = datetime.strptime(date_string, '%d/%m/%Y %H:%M:%S')
    except ValueError:
        try:
            # Try to parse without time format
            new_date = datetime.strptime(date_string, '%d/%m/%Y')
        except ValueError:
            raise ValueError("Invalid date format")

    return new_date


def serialize_data(data):
    if not isinstance(data, dict):
        return {}
    new_data = {}
    for key, value in data.items():
        if isinstance(value, tuple):
            new_data[key] = value[1]
        elif isinstance(value, (datetime, date)):
            fmt = "%d/%m/%Y %H:%M:%S"
            tz = pytz.timezone('Asia/Qatar')
            now_utc = datetime.now(pytz.timezone('UTC'))
            now_timezone = now_utc.astimezone(tz)
            UTC_OFFSET_TIMEDELTA = datetime.strptime(now_timezone.strftime(fmt), fmt) - datetime.strptime(
                now_utc.strftime(fmt), fmt)

            new_data[key] = datetime.strptime(value.strftime(fmt), fmt)
            new_data[key] = new_data[key] + UTC_OFFSET_TIMEDELTA
            new_data[key] = datetime.strftime(new_data[key], "%d/%m/%Y %H:%M:%S")
        else:
            new_data[key] = value if value else ''
    return new_data


class EmployeeApi(http.Controller):
    @http.route("/GetEmployee/", auth="public", type="json", methods=["POST"])
    def get_employee(self, **kwargs):
        data = []
        params = request.httprequest.args.to_dict()
        get_image = False
        if params.get("getImage"):
            get_image = params.get("getImage")

        if params.get("username"):
            username = params.get("username")
            user = request.env['res.users'].sudo().search([
                ('login', '=', username)
            ])
            if user:
                employees = request.env['hr.employee'].sudo().search([
                    ('user_id', '=', user.id)
                ])
                if employees:
                    if get_image:
                        for employee in employees:
                            systems = []
                            procedures = []
                            employee_image = False
                            if employee.image_1920:
                                employee_image = employee.image_1920
                            for system in employee.employee_system_ids:
                                systems.append({'name': system.employee_system_id.name,
                                                'link': system.link})
                            for procedure in employee.employee_procedure_ids:
                                procedures.append({'name': procedure.procedure_name_id.name})
                            data.append({"name": employee.arabic_name if employee.arabic_name else None,
                                         "work_phone": employee.work_phone if employee.work_phone else None,
                                         "birthday": employee.birthday if employee.birthday else '',
                                         "joining_date": employee.joining_date if employee.joining_date else '',
                                         "work_email": employee.work_email if employee.work_email else None,
                                         "department_id": employee.department_id.id if employee.department_id else None,
                                         "department_name": employee.department_id.name if employee.department_id and employee.department_id.name else None,
                                         "job_id": employee.job_id.id if employee.job_id else None,
                                         "job_name": employee.job_id.name if employee.job_id and employee.job_id.name else None,
                                         "office_floor": employee.office_floor if employee.office_floor else None,
                                         "office_no": employee.office_no if employee.office_no else None,
                                         "phone_personal": employee.phone_personal if employee.phone_personal else None,
                                         "Image": employee_image if employee_image else None,
                                         "systems": systems,
                                         "procedures": procedures
                                         })
                    if not get_image:
                        # employees_data = employees.read(
                        #     ['name', 'work_phone', 'birthday', 'joining_date', 'work_email'])
                        for employee in employees:
                            systems = []
                            procedures = []
                            for system in employee.employee_system_ids:
                                systems.append({'name': system.employee_system_id.name,
                                                'link': system.link})
                            for procedure in employee.employee_procedure_ids:
                                procedures.append({'name': procedure.procedure_name_id.name})

                            data.append({"name": employee.arabic_name if employee.arabic_name else None,
                                         "work_phone": employee.work_phone if employee.work_phone else None,
                                         "birthday": employee.birthday if employee.birthday else '',
                                         "joining_date": employee.joining_date if employee.joining_date else '',
                                         "work_email": employee.work_email if employee.work_email else None,
                                         "department_id": employee.department_id.id if employee.department_id else None,
                                         "department_name": employee.department_id.name if employee.department_id and employee.department_id.name else None,
                                         "job_id": employee.job_id.id if employee.job_id else None,
                                         "job_name": employee.job_id.name if employee.job_id and employee.job_id.name else None,
                                         "office_floor": employee.office_floor if employee.office_floor else None,
                                         "office_no": employee.office_no if employee.office_no else None,
                                         "phone_personal": employee.phone_personal if employee.phone_personal else None,
                                         "systems": systems,
                                         "procedures": procedures
                                         })
        elif params.get("department"):
            department_id = params.get("department")
            department = request.env['hr.department'].sudo().search([
                ('id', '=', int(department_id))
            ])
            if department:
                employees = request.env['hr.employee'].sudo().search([
                    ('department_id', '=', department[0].id)
                ])
                if employees:
                    if get_image:
                        for employee in employees:
                            systems = []
                            procedures = []
                            employee_image = False
                            if employee.image_1920:
                                employee_image = employee.image_1920
                            for system in employee.employee_system_ids:
                                systems.append({'name': system.employee_system_id.name,
                                                'link': system.link})
                            for procedure in employee.employee_procedure_ids:
                                procedures.append({'name': procedure.procedure_name_id.name})

                            data.append({"name": employee.arabic_name if employee.arabic_name else None,
                                         "work_phone": employee.work_phone if employee.work_phone else None,
                                         "birthday": employee.birthday if employee.birthday else '',
                                         "joining_date": employee.joining_date if employee.joining_date else '',
                                         "work_email": employee.work_email if employee.work_email else None,
                                         "department_id": employee.department_id.id if employee.department_id else None,
                                         "department_name": employee.department_id.name if employee.department_id and employee.department_id.name else None,
                                         "job_id": employee.job_id.id if employee.job_id else None,
                                         "job_name": employee.job_id.name if employee.job_id and employee.job_id.name else None,
                                         "office_floor": employee.office_floor if employee.office_floor else None,
                                         "office_no": employee.office_no if employee.office_no else None,
                                         "phone_personal": employee.phone_personal if employee.phone_personal else None,
                                         "Image": employee_image if employee_image else None,
                                         "systems": systems,
                                         "procedures": procedures
                                         })
                    if not get_image:
                        for employee in employees:
                            systems = []
                            procedures = []
                            for system in employee.employee_system_ids:
                                systems.append({'name': system.employee_system_id.name,
                                                'link': system.link})
                            for procedure in employee.employee_procedure_ids:
                                procedures.append({'name': procedure.procedure_name_id.name})

                            data.append({"name": employee.arabic_name if employee.arabic_name else None,
                                         "work_phone": employee.work_phone if employee.work_phone else None,
                                         "birthday": employee.birthday if employee.birthday else '',
                                         "joining_date": employee.joining_date if employee.joining_date else '',
                                         "work_email": employee.work_email if employee.work_email else None,
                                         "department_id": employee.department_id.id if employee.department_id else None,
                                         "department_name": employee.department_id.name if employee.department_id and employee.department_id.name else None,
                                         "job_id": employee.job_id.id if employee.job_id else None,
                                         "job_name": employee.job_id.name if employee.job_id and employee.job_id.name else None,
                                         "office_floor": employee.office_floor if employee.office_floor else None,
                                         "office_no": employee.office_no if employee.office_no else None,
                                         "phone_personal": employee.phone_personal if employee.phone_personal else None,
                                         "systems": systems,
                                         "procedures": procedures
                                         })
                        # employees_data = employees.read(
                        #     ['name', 'work_phone', 'birthday', 'joining_date', 'work_email', 'department_id'])
                        # for emp_data in employees_data:
                        #     data.append(serialize_data(emp_data))
            else:
                data = "This Department Not Founded!"
        else:
            employees = request.env['hr.employee'].sudo().search([])
            if get_image:
                for employee in employees:
                    systems = []
                    procedures = []
                    employee_image = False
                    if employee.image_1920:
                        employee_image = employee.image_1920
                    for system in employee.employee_system_ids:
                        systems.append({'name': system.employee_system_id.name,
                                        'link': system.link})
                    for procedure in employee.employee_procedure_ids:
                        procedures.append({'name': procedure.procedure_name_id.name})

                    data.append({"name": employee.arabic_name if employee.arabic_name else None,
                                 "work_phone": employee.work_phone if employee.work_phone else None,
                                 "birthday": employee.birthday if employee.birthday else '',
                                 "joining_date": employee.joining_date if employee.joining_date else '',
                                 "work_email": employee.work_email if employee.work_email else None,
                                 "department_id": employee.department_id.id if employee.department_id else None,
                                 "department_name": employee.department_id.name if employee.department_id and employee.department_id.name else None,
                                 "job_id": employee.job_id.id if employee.job_id else None,
                                 "job_name": employee.job_id.name if employee.job_id and employee.job_id.name else None,
                                 "office_floor": employee.office_floor if employee.office_floor else None,
                                 "office_no": employee.office_no if employee.office_no else None,
                                 "phone_personal": employee.phone_personal if employee.phone_personal else None,
                                 "Image": employee_image if employee_image else None,
                                 "systems": systems,
                                 "procedures": procedures
                                 })
            if not get_image:
                for employee in employees:
                    systems = []
                    procedures = []
                    for system in employee.employee_system_ids:
                        systems.append({'name': system.employee_system_id.name,
                                        'link': system.link})
                    for procedure in employee.employee_procedure_ids:
                        procedures.append({'name': procedure.procedure_name_id.name})

                    data.append({"name": employee.arabic_name if employee.arabic_name else None,
                                 "work_phone": employee.work_phone if employee.work_phone else None,
                                 "birthday": employee.birthday if employee.birthday else '',
                                 "joining_date": employee.joining_date if employee.joining_date else '',
                                 "work_email": employee.work_email if employee.work_email else None,
                                 "department_id": employee.department_id.id if employee.department_id else None,
                                 "department_name": employee.department_id.name if employee.department_id and employee.department_id.name else None,
                                 "job_id": employee.job_id.id if employee.job_id else None,
                                 "job_name": employee.job_id.name if employee.job_id and employee.job_id.name else None,
                                 "office_floor": employee.office_floor if employee.office_floor else None,
                                 "office_no": employee.office_no if employee.office_no else None,
                                 "phone_personal": employee.phone_personal if employee.phone_personal else None,
                                 "systems": systems,
                                 "procedures": procedures
                                 })
                # employees_data = employees.read(
                #     ['name', 'work_phone', 'birthday', 'joining_date', 'work_email', 'department_id'])
                # for emp_data in employees_data:
                #     data.append(serialize_data(emp_data))
            # data = employees.read(['name', 'work_phone', 'birthday', 'joining_date', 'work_email', 'department_id'])

        return data

    @http.route("/GetEmployeeAttendance/", auth="public", type="json", methods=["POST"])
    def get_employee_attendance(self, **kwargs):
        params = request.httprequest.args.to_dict()
        data = []
        if params.get("username") and params.get("date_from") and params.get("date_to"):
            username = params.get("username")
            try:
                date_from = parse_date(params.get('date_from'))
                date_from = date_from.strftime("%m/%d/%Y %H:%M:%S")

                date_to = parse_date(params.get('date_to'))
                date_to = date_to.strftime("%m/%d/%Y %H:%M:%S")
                print('date_from', date_from, date_to)
            except Exception as e:
                return {
                    'message': 'Invalid date format',
                    'error': 'date format must be DD/MM/YYYY HH:MM:SS or DD/MM/YYYY',
                    'code': 500,
                    'http_status': 500,
                }
            user = request.env['res.users'].sudo().search([
                ('login', '=', username)
            ])
            if user:
                employees = request.env['hr.employee'].sudo().search([
                    ('user_id', '=', user.id)
                ])
                if employees:
                    current_date = datetime.today().date()
                    attendance_date = []
                    attendance = request.env['hr.attendance'].sudo().search([
                        ('employee_id', '=', employees.id),
                        ('check_in', '>=', date_from),
                        # ('check_out', '<=', date_to)
                    ])
                    if attendance:
                        attendance_data = attendance.read(
                            ['employee_id', 'check_in', 'check_out', 'worked_hours', 'is_early_check_out',
                             'is_late_check_in'])

                        for att_data in attendance_data:
                            attendance_date.append(att_data['check_in'].date())
                            data.append(serialize_data(att_data))

                        if current_date not in attendance_date and current_date == parse_date(params.get('date_to')).date():
                            punch_time_from_date = datetime.combine(current_date, time(0, 0, 0))
                            punch_time_to_date = datetime.combine(current_date, time(23, 59, 59))
                            machine_attendance_record = request.env['machine.attendance.record'].sudo().search([
                                ('employee_id', '=', employees.id),
                                ('punch_type', '=', 'I'),
                                ('punch_time', '>=', punch_time_from_date),
                                ('punch_time', '<=', punch_time_to_date)
                            ], order='punch_time ASC', limit=1)
                            if machine_attendance_record:
                                fmt = "%d/%m/%Y %H:%M:%S"
                                tz = pytz.timezone('Asia/Qatar')
                                now_utc = datetime.now(pytz.timezone('UTC'))
                                now_timezone = now_utc.astimezone(tz)
                                UTC_OFFSET_TIMEDELTA = datetime.strptime(now_timezone.strftime(fmt), fmt) - datetime.strptime(now_utc.strftime(fmt), fmt)
                                punch_time = datetime.strptime(machine_attendance_record.punch_time.strftime(fmt), fmt)
                                punch_time = punch_time + UTC_OFFSET_TIMEDELTA

                                att_object = {
                                    "id": '',
                                    "employee_id": machine_attendance_record.employee_id.name,
                                    "check_in": datetime.strftime(punch_time, "%d/%m/%Y %H:%M:%S"),
                                    "check_out": None,
                                    "worked_hours": "",
                                    "is_early_check_out": "",
                                    "is_late_check_in": ""
                                }
                                data.insert(0, att_object)
                                data.append(att_object)
                    else:
                        punch_time_from_date = datetime.combine(current_date, time(0, 0, 0))
                        punch_time_to_date = datetime.combine(current_date, time(23, 59, 59))
                        machine_attendance_record = request.env['machine.attendance.record'].sudo().search([
                            ('employee_id', '=', employees.id),
                            ('punch_type', '=', 'I'),
                            ('punch_time', '>=', punch_time_from_date),
                            ('punch_time', '<=', punch_time_to_date)
                        ], order='punch_time ASC', limit=1)
                        if machine_attendance_record:
                            fmt = "%d/%m/%Y %H:%M:%S"
                            tz = pytz.timezone('Asia/Qatar')
                            now_utc = datetime.now(pytz.timezone('UTC'))
                            now_timezone = now_utc.astimezone(tz)
                            UTC_OFFSET_TIMEDELTA = datetime.strptime(now_timezone.strftime(fmt),
                                                                     fmt) - datetime.strptime(now_utc.strftime(fmt),
                                                                                              fmt)
                            punch_time = datetime.strptime(machine_attendance_record.punch_time.strftime(fmt), fmt)
                            punch_time = punch_time + UTC_OFFSET_TIMEDELTA
                            att_object = {
                                "id": "",
                                "employee_id": machine_attendance_record.employee_id.name,
                                "check_in": datetime.strftime(punch_time, "%d/%m/%Y %H:%M:%S"),
                                "check_out": None,
                                "worked_hours": "",
                                "is_early_check_out": "",
                                "is_late_check_in": ""
                            }
                            data.append(att_object)


        elif params.get("username") and not params.get("date_from") or not params.get("date_to"):
            username = params.get("username")
            user = request.env['res.users'].sudo().search([
                ('login', '=', username)
            ])
            if user:
                employees = request.env['hr.employee'].sudo().search([
                    ('user_id', '=', user.id)
                ])
                if employees:
                    attendance = request.env['hr.attendance'].sudo().search([
                        ('employee_id', '=', employees.id),
                        # ('check_in', '>=', date_from),
                        # ('check_out', '<=', date_to)
                    ])
                    if attendance:
                        attendance_date = []
                        attendance_data = attendance.read(
                            ['employee_id', 'check_in', 'check_out', 'worked_hours', 'is_early_check_out',
                             'is_late_check_in'])

                        for att_data in attendance_data:
                            attendance_date.append(att_data['check_in'].date())
                            data.append(serialize_data(att_data))

                        current_date = datetime.today().date()
                        if current_date not in attendance_date:
                            punch_time_from_date = datetime.combine(current_date, time(0, 0, 0))
                            punch_time_to_date = datetime.combine(current_date, time(23, 59, 59))
                            machine_attendance_record = request.env['machine.attendance.record'].sudo().search([
                                ('employee_id', '=', employees.id),
                                ('punch_type', '=', 'I'),
                                ('punch_time', '>=', punch_time_from_date),
                                ('punch_time', '<=', punch_time_to_date)
                            ], order='punch_time ASC', limit=1)
                            if machine_attendance_record:
                                fmt = "%d/%m/%Y %H:%M:%S"
                                tz = pytz.timezone('Asia/Qatar')
                                now_utc = datetime.now(pytz.timezone('UTC'))
                                now_timezone = now_utc.astimezone(tz)
                                UTC_OFFSET_TIMEDELTA = datetime.strptime(now_timezone.strftime(fmt), fmt) - datetime.strptime(now_utc.strftime(fmt), fmt)
                                punch_time = datetime.strptime(machine_attendance_record.punch_time.strftime(fmt), fmt)
                                punch_time = punch_time + UTC_OFFSET_TIMEDELTA

                                att_object = {
                                    "id": '',
                                    "employee_id": machine_attendance_record.employee_id.name,
                                    "check_in": datetime.strftime(punch_time, "%d/%m/%Y %H:%M:%S"),
                                    "check_out": None,
                                    "worked_hours": "",
                                    "is_early_check_out": "",
                                    "is_late_check_in": ""
                                },
                                # data.append(att_object)
                                print(type(att_object))
                                data.insert(0, att_object)

        return data

    def date_range(self, start_dt, end_dt, step=relativedelta(days=1)):
        dates = []

        while start_dt <= end_dt:
            dates.append(start_dt)
            start_dt += step

        return dates

    def _get_month_week_end(self, employee_calender, date_from, date_to):
        weekend_dates = []

        if employee_calender:

            resource_id_dayofweek_dict = {
                '0': 'Monday',
                '1': 'Tuesday',
                '2': 'Wednesday',
                '3': 'Thursday',
                '4': 'Friday',
                '5': 'Saturday',
                '6': 'Sunday'
            }
            attendance_list = set(employee_calender.attendance_ids.mapped('dayofweek'))
            week_end_days_numbers = [element for element in resource_id_dayofweek_dict if
                                     element not in attendance_list]
            week_end_days_names = [resource_id_dayofweek_dict.get(element) for element in week_end_days_numbers]

            num_days_in_month = (date_to - date_from).days + 1

            for day in range(date_from.day, num_days_in_month + 1):
                day_date = datetime(date_from.year, date_from.month, day).date()
                day_name = day_date.strftime("%A")
                if day_name in week_end_days_names:
                    weekend_dates.append(day_date)

        return weekend_dates

    def _get_month_public_holidays(self, date_from, date_to, employee_calendar):
        public_holiday_dates = []
        if employee_calendar:
            public_holiday_records = employee_calendar.global_leave_ids.filtered(
                lambda
                    public_holiday: (
                                            date_from <= public_holiday.date_from.date() and date_to >= public_holiday.date_to.date()) \
                                    or (
                                            public_holiday.date_from.date() <= date_from <= public_holiday.date_to.date()) \
                                    or (
                                            public_holiday.date_from.date() <= date_to <= public_holiday.date_to.date())
            )
            for public_holiday_record in public_holiday_records:
                if date_from <= public_holiday_record.date_from.date() and date_to >= public_holiday_record.date_to.date():
                    public_holiday_dates.extend(self.date_range(public_holiday_record.date_from.date(),
                                                                public_holiday_record.date_to.date(),
                                                                relativedelta(days=1)))

                elif public_holiday_record.date_from.date() <= date_from <= public_holiday_record.date_to.date():
                    public_holiday_dates.extend(self.date_range(date_from,
                                                                public_holiday_record.date_to.date(),
                                                                relativedelta(days=1)))


                elif public_holiday_record.date_from.date() <= date_to <= public_holiday_record.date_to.date():
                    public_holiday_dates.extend(self.date_range(public_holiday_record.date_from.date(),
                                                                date_to, relativedelta(days=1)))
        return public_holiday_dates

    def _get_month_not_paid_holidays(self, date_from, date_to, employee):
        not_absence_leave_dates = []
        not_absence_leave_records = request.env['hr.leave'].sudo().search([
            ('holiday_status_id.is_unpaid', '=', False), ('employee_id', '=', employee.id), ('state', '=', 'validate')
        ]).filtered(lambda leave: (
                                          date_from <= leave.request_date_from and date_to >= leave.request_date_to) \
                                  or (
                                          leave.request_date_from <= date_from <= leave.request_date_to) \
                                  or (
                                          leave.request_date_from <= date_to <= leave.request_date_to))
        for leave in not_absence_leave_records:
            if date_from <= leave.request_date_from and date_to >= leave.request_date_to:
                not_absence_leave_dates.extend(self.date_range(leave.request_date_from,
                                                               leave.request_date_to, relativedelta(days=1)))

            elif leave.request_date_from <= date_from <= leave.request_date_to:
                not_absence_leave_dates.extend(self.date_range(date_from,
                                                               leave.request_date_to, relativedelta(days=1)))


            elif leave.request_date_from <= date_to <= leave.request_date_to:
                not_absence_leave_dates.extend(self.date_range(leave.request_date_from.date.date(),
                                                               date_to, relativedelta(days=1)))
        return not_absence_leave_dates

    def _get_planned_attendance_dates(self, date_from, date_to, official_absence_dates):
        all_month_range = set(self.date_range(date_from, date_to, relativedelta(days=1)))
        remaining_range = all_month_range - official_absence_dates
        return remaining_range

    def _get_contract_attendance_rate(self, employee, employee_calendar, attendances, planned_attendance_dates, month,
                                      year):
        working_hours = len(planned_attendance_dates) * employee_calendar.hours_per_day
        employee_violation_records = employee.attendance_sheet_ids.filtered(
            lambda x: x.attendance_state not in ['attendance'] and x.date.month == month and x.date.year == year)
        violation_hours = sum(
            employee_violation_records.mapped('late_check_in') + employee_violation_records.mapped('early_check_out'))
        max_allowed_hours = employee.company_id.max_allowed_hours
        violation_hours = violation_hours if violation_hours < max_allowed_hours else max_allowed_hours
        if working_hours - violation_hours > 0:
            attendance_hours = 0.0
            for attendance_day in planned_attendance_dates:
                all_check_in = attendances.filtered(
                    lambda attendance: attendance.check_in.date() == attendance_day).mapped('check_in')
                first_check_in = min(all_check_in) if all_check_in else False
                all_check_out = attendances.filtered(
                    lambda attendance: attendance.check_out and attendance.check_out.date() == attendance_day).mapped(
                    'check_out')
                last_check_out = max(all_check_out) if all_check_out else False
                if first_check_in and last_check_out:
                    attendance_hours += (last_check_out - first_check_in).seconds / (60 * 60)
            return attendance_hours / (working_hours - violation_hours) * 100

    @http.route("/GetAttendanceRate/", auth="public", type="json", methods=["POST"], csrf=False)
    def get_attendance_rate(self, **kwargs):
        params = request.httprequest.args.to_dict()

        if params.get("username") and params.get("month") and params.get("year"):
            username = params.get("username")
            user = request.env['res.users'].sudo().search([
                ('login', '=', username)
            ])
            month = params.get("month")
            year = params.get("year")
            if not user:
                return {
                    'message': 'Invalid User name',
                    'error': 'Entered user name isn\'t a system user',
                    'code': 500,
                    'http_status': 500,
                }
            if not (month.isnumeric() and 1 <= int(month) <= 12):
                return {
                    'message': 'Insert Valid Month',
                    'error': 'Month number must be between 1 and 12',
                    'code': 500,
                    'http_status': 500,
                }
            if not (year.isnumeric() and (date.today().year - 10) < int(year) <= date.today().year):
                return {
                    'message': 'Insert Valid Year',
                    'error': 'Year Must not be earlier than 10 years or more than current year',
                    'code': 500,
                    'http_status': 500,
                }

            month_int = int(month)
            year_int = int(year)
            last_month_day = calendar.monthrange(year_int, month_int)[1]
            date_from = datetime(year_int, month_int, 1).date()
            date_to = datetime(year_int, month_int, last_month_day).date()
            if date_to > date.today():
                date_to = date.today()

            employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
            if employee:

                employee_contracts = employee.contract_ids.filtered(
                    lambda contract: contract.date_start <= date_from and (
                            (contract.date_end and contract.date_end >= date_to)
                            or (not contract.date_end)))

                attendance_rate = 0.0

                for contract in employee_contracts:
                    contract_date_from = date_from if date_from >= contract.date_start else contract.date_start
                    contract_date_to = date_to if not contract.date_end or date_to <= contract.date_end else contract.date_end
                    employee_calendar = contract.resource_calendar_id
                    month_week_ends = self._get_month_week_end(employee_calendar, contract_date_from,
                                                               contract_date_to)
                    month_public_holidays = self._get_month_public_holidays(contract_date_from, contract_date_to,
                                                                            employee_calendar)
                    month_not_paid_holidays = self._get_month_not_paid_holidays(contract_date_from,
                                                                                contract_date_to,
                                                                                employee)
                    official_absence_dates = set(month_week_ends + month_public_holidays + month_not_paid_holidays)
                    search_date_from = datetime.combine(date_from + relativedelta(days=-1), datetime.min.time())
                    search_date_to = datetime.combine(date_to + relativedelta(days=1), datetime.max.time())

                    attendances = request.env['hr.attendance'].sudo().sudo().search([
                        ('employee_id', '=', employee.id),
                        ('check_in', '>=', search_date_from),
                        ('check_in', '<=', search_date_to)
                    ]).filtered(lambda
                                    attendance: contract_date_from <= attendance.check_in.date() <= contract_date_to and attendance.check_in.date() not in official_absence_dates)
                    planned_attendance_dates = self._get_planned_attendance_dates(contract_date_from,
                                                                                  contract_date_to,
                                                                                  official_absence_dates)
                    attendance_rate += self._get_contract_attendance_rate(employee, employee_calendar, attendances,
                                                                          planned_attendance_dates, month_int,
                                                                          year_int)
                return {
                    'attendance_rate': (attendance_rate / len(employee_contracts)) if (attendance_rate / len(employee_contracts)) <= 100 else 100
                }

            else:
                return {
                    'message': 'Invalid User',
                    'error': 'Entered user doesn\'t have related employee',
                    'code': 500,
                    'http_status': 500,
                }

        else:
            return {
                'message': 'Missing Parameter',
                'error': 'You must enter user name, month and year to get attendance rate',
                'code': 500,
                'http_status': 500,
            }

    @http.route("/GetPhoneEmployee/", auth="public", type="json", methods=["POST"])
    def get_phone_employee(self, **kwargs):

        data = []
        params = request.httprequest.args.to_dict()
        if params.get("name"):
            name = params.get("name")
            employees = request.env['hr.employee'].sudo().search([
                ('name', 'ilike', name)
            ])
            if employees:
                data = employees.read(['work_phone'])
        else:
            employees = request.env['hr.employee'].sudo().search([])
            # data = employees.read(['name', 'work_phone'])
            for employee in employees:
                data.append({
                    'name': employee.name if employee.name else None,
                    'work_phone': employee.work_phone if employee.work_phone else None,
                })

        return data

    @http.route("/GetEmployeeQID/", auth="public", type="json", methods=["POST"])
    def get_qid_employee(self, **kwargs):

        data = []
        params = request.httprequest.args.to_dict()
        if params.get("username"):
            username = params.get("username")
            user = request.env['res.users'].sudo().search([
                ('login', '=', username)
            ])
            if user and user.employee_id:
                if user.employee_id.employee_qid_number:
                    data = user.employee_id.employee_qid_number

        else:
            users = request.env['res.users'].sudo().search([])
            if users:
                for user in users:
                    if user and user.employee_id:
                        if user.employee_id.employee_qid_number:
                            data.append({
                                'employee_name': user.employee_id.name,
                                'QID': user.employee_id.employee_qid_number,
                            })
                            # data = user.employee_id.employee_qid_number

        return data

    @http.route("/GetEmployeeJustifiedHours/", auth="public", type="json", methods=["POST"])
    def get_employee_justified_hours(self, **kwargs):
        params = request.httprequest.args.to_dict()
        data = [
            {
                'justified_hours': 0,
                'approved_hours': 0,
                'rejected_hours': 0,
            }
        ]
        if params.get("username") and params.get("year") and params.get("month"):
            username = params.get("username")
            year = int(params.get("year"))
            month = int(params.get("month"))
            month_first_day = datetime(year, month, 1)
            last_day = calendar.monthrange(month_first_day.year, month_first_day.month)[1]
            month_last_day = datetime(year, month, last_day)
            user = request.env['res.users'].sudo().search([
                ('login', '=', username)
            ])

            if user:
                employees = request.env['hr.employee'].sudo().search([
                    ('user_id', '=', user.id)
                ], limit=1)
                if employees:
                    attendances = request.env['hr.attendance'].sudo().search([
                        ('employee_id', '=', employees.id),
                        ('check_in', '>=', month_first_day),
                        ('check_out', '<=', month_last_day),
                    ])

                    justified_hours = sum(attendances.mapped('early_check_store') +
                                          attendances.mapped('late_check_store'))
                    approved_hours = sum(
                        attendances.filtered(lambda x: x.attendance_status_early == 'approved')
                        .mapped('early_check_store') +
                        attendances.filtered(lambda x: x.attendance_status == 'approved')
                        .mapped('late_check_store'))
                    rejected_hours = sum(
                        attendances.filtered(lambda x: x.attendance_status_early == 'rejected')
                        .mapped('early_check_store') +
                        attendances.filtered(lambda x: x.attendance_status == 'rejected')
                        .mapped('late_check_store'))
                    employee_violation_records = employees.attendance_sheet_ids.filtered(
                        lambda x: x.attendance_state not in [
                            'attendance'] and x.date.month == month and x.date.year == year)
                    violation_hours = sum(
                        employee_violation_records.mapped('late_check_in') + employee_violation_records.mapped(
                            'early_check_out'))
                    max_allowed_hours = employees.company_id.max_allowed_hours
                    violation_hours_balance = max_allowed_hours - violation_hours if max_allowed_hours - violation_hours > 0 else 0.0
                    data = [{
                        'justified_hours': violation_hours_balance,
                        'all_justified_hours': justified_hours,
                        'approved_hours': approved_hours,
                        'rejected_hours': rejected_hours,
                    }]

        return data
