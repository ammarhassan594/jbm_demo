import logging

from odoo import models, fields, api, _
import json
from datetime import datetime, date, time, timedelta
import pytz
import math
import requests

from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

MACHINE_ATTENDANCE_RECORD = ['machine_record_id', 'punch_time', 'punch_type',
                             'employee_id']


def convert_decimal_hours_to_time(decimal_hours):
    # Extract the integer part for hours
    hours = int(decimal_hours)
    # Extract the fractional part and convert to minutes
    minutes = math.ceil((decimal_hours - hours) * 60)
    # Format the result with leading zeros for hours and minutes
    formatted_time = f"{hours:02d}:{minutes:02d}"
    return formatted_time

class MachineAttendanceRecord(models.Model):
    _name = 'machine.attendance.record'
    _description = 'Machine Attendance Record'
    _order = 'punch_time DESC'

    machine_record_id = fields.Char(
        string='Record ID', help='ID of record on the attendance machine',
        index=True, required=False)
    punch_time = fields.Datetime(required=True, help="Time of punch form Attendance Machine")
    punch_date = fields.Date(string="Punch_date", compute='_compute_punch_date', store=True)
    punch_type = fields.Selection([
        ('O', 'خروج'),
        ('I', 'دخول'),
    ], required=True, help="Type of punch, o means check out, i means check in")
    employee_id = fields.Many2one('hr.employee', required=True)
    state = fields.Selection([
        ('success', 'Success'),
        ('failure', 'Failure'),
        ('skip', 'Skip'),
    ],
        string='Status', help='State of record')
    error_message = fields.Text('Error Message')
    created_from_machine = fields.Boolean(string="Created From Machine")
    # UNIQUE(machine_record_id, employee_id)
    _sql_constraints = [
        ('unique_record', 'UNIQUE(machine_record_id, employee_id)',
         'Record already exists')
    ]

    @api.depends('punch_time')
    def _compute_punch_date(self):
        for rec in self:
            rec.punch_date = rec.punch_time.date() if rec.punch_time else False

    @api.model_create_multi
    def create(self, vals_list):
        for val in vals_list:
            if not val.get('machine_record_id'):
                val.update({
                    'machine_record_id': self.env['ir.sequence'].next_by_code('machine.attendance.record')
                })
            if self._context.get('gui_create'):
                val.update({
                    'state': 'failure'
                })
        records = super(MachineAttendanceRecord, self).create(vals_list)
        for rec in records:
            today = date.today()
            attendance = self.env['machine.attendance.record'].search([('employee_id', '=', rec.employee_id.id), ('punch_type', '=', 'I'), ('punch_date', '=', today)])
            if len(attendance) <= 1:
                if rec.employee_id:
                    employee = self.env['hr.employee'].search([('id', '=', rec.employee_id.id), ('out_of_attendance', '!=', True)])
                    if employee:
                        if rec.punch_type == 'I':
                            day = str(date.today().weekday())
                            # day = '0'
                            hour_from = employee.resource_calendar_id.attendance_ids.filtered(lambda s: s.dayofweek == day).filtered(
                                lambda s: s.day_period == 'morning').hour_from
                            if hour_from:
                                hour = (rec.punch_time + timedelta(hours=3)).strftime("%H")
                                min = (rec.punch_time + timedelta(hours=3)).strftime("%M")
                                total_time = float(hour) + ((float(min) * 0.5) / 30)
                                if total_time > hour_from:
                                    diff = total_time - hour_from
                                    diff = convert_decimal_hours_to_time(diff)
                                    # h, m = math.modf(diff)
                                    message = f"تم تسجيل تأخيرك عن الدوام لمدة {diff} بتاريخ {date.today()}"
                                    employee.sudo().with_context(message=message).send_sms_message()
                                type(hour)
        return records

    @api.model
    def update_or_create_attendance_record(self, **values):
        """Update or create a machine attendance record.
        Before update or create the record, we have to check if the record exists or not.
        @param values: The values to update or create.
        @type values: dict

        @return: The record is updated or created.
        @rtype: Object from machine.attendance.record
        """

        valid_fields = {key: values.get(key) for key in values if key in MACHINE_ATTENDANCE_RECORD}
        if not valid_fields:
            raise ValidationError(_('Required fields of the attendance sheet were not provided.'))
        exists_record = self.search(
            [('machine_record_id', '=', values.get('machine_record_id'))])
        if exists_record:
            exists_record.write(values)
            self.env.cr.commit()
            return exists_record
        elif values.get('machine_record_id'):
            machine_record = self.create({
                'machine_record_id': values.get('machine_record_id'),
                'punch_time': values.get('punch_time'),
                'punch_type': values.get('punch_type'),
                'employee_id': values.get('employee_id'),
            })
            self.env.cr.commit()
            return machine_record
        # Check if the record exists or not
        # If it exists, update with new values
        # If new create a new record
        # Return the record id

    def _remove_duplication_data(self, data=[]):
        if data:
            seen = set()
            new_list = []
            for d in data:
                t = tuple(d.items())
                if t not in seen:
                    seen.add(t)
                    new_list.append(d)
            return new_list

    def _get_not_exist_attendance_data(self, attendance_data):
        """Checks if the Machine record exists."""
        record_ids = [str(item.get('record_ID')) for item in attendance_data]
        self._cr.execute(
            """SELECT machine_record_id FROM machine_attendance_record WHERE machine_record_id in %s""",
            [tuple(record_ids)])
        existing_record_ids = self._cr.fetchall()
        if existing_record_ids:
            existing_record_ids = [rec_id[0] for rec_id in list(existing_record_ids)]
            return [item for item in attendance_data if str(item.get('record_ID')) not in existing_record_ids]
        else:
            return attendance_data

    def get_attendance_data(self):
        try:
            url = self.env['ir.config_parameter'].sudo().get_param('attendance_api_link')
            if url:

                response = requests.get(url=url, headers={'Content-Type': 'application/json'})
                response.raise_for_status()
                attendance_data = json.loads(response.text)

                if attendance_data:
                    attendance_data = sorted(attendance_data, key=lambda x: (
                        (datetime.strptime(x['punch_time'].split('T', 1)[0], '%Y-%m-%d').date())))

                    attendance_data = self._remove_duplication_data(attendance_data)
                    attendance_data = self._get_not_exist_attendance_data(attendance_data)

                    vals_list = []
                    for attendance in attendance_data:
                        qid = attendance['employee_ID']
                        employee_id = self._get_employee(qid)

                        if not employee_id:
                            continue

                        punch_type = attendance.get('punch_type')
                        punch_time_str = attendance.get('punch_time')
                        punch_time_native = datetime.strptime(punch_time_str, '%Y-%m-%dT%H:%M:%S')
                        rec_id = attendance.get('record_ID')
                        punch_time = self._convert_punch_time(punch_time_native)

                        vals_list.append({
                            'machine_record_id': rec_id,
                            'punch_time': punch_time,
                            'employee_id': employee_id.id,
                            'punch_type': punch_type,
                            'created_from_machine': True
                        })

                    self.create(vals_list)

        except Exception as e:
            _logger.info(e)
            raise ValueError(e)

    def _get_employee(self, qid):
        """Get the employee based on the qid."""
        return self.env['hr.employee'].sudo().search([
            ('employee_qid_number', '=', str(qid))],
            limit=1)

    @staticmethod
    def _convert_punch_time(punch_time):
        fmt = "%Y-%m-%d %H:%M:%S"
        tz = pytz.timezone('Asia/Qatar')
        now_utc = datetime.now(pytz.timezone('UTC'))
        now_timezone = now_utc.astimezone(tz)
        UTC_OFFSET_TIMEDELTA = datetime.strptime(now_timezone.strftime(fmt), fmt) - datetime.strptime(
            now_utc.strftime(fmt), fmt)

        punch_time = datetime.strptime(punch_time.strftime(fmt), fmt)
        return punch_time - UTC_OFFSET_TIMEDELTA

    def action_create_attendance(self):
        attendance_vals_list = []
        for employee in self.filtered(lambda rec: rec.punch_type != 'skip').mapped('employee_id'):
            employee_attendance_days = list(
                set(self.filtered(lambda rec: rec.employee_id == employee).mapped('punch_date')))
            employee_attendance_days.sort()
            for day in employee_attendance_days:
                day_machine_records = self.filtered(
                    lambda rec: rec.employee_id == employee and rec.punch_date == day).sorted('punch_time')
                day_log_in_employee_records = day_machine_records.filtered(lambda rec: rec.punch_type == 'I')
                day_log_out_employee_records = day_machine_records.filtered(lambda rec: rec.punch_type == 'O')
                if len(day_machine_records) % 2 != 0:
                    day_machine_records.write({
                        'state': 'failure',
                        'error_message': 'number of day records not an even number'
                    })
                    continue
                if len(day_log_in_employee_records) != len(day_log_out_employee_records):
                    day_machine_records.write({
                        'state': 'failure',
                        'error_message': 'number of log in records not equal to log out records'
                    })
                    continue
                for time in range(len(day_log_in_employee_records)):
                    if day_log_in_employee_records[time].punch_time >= day_log_out_employee_records[time].punch_time:
                        day_machine_records.write({
                            'state': 'failure',
                            'error_message': 'log out equal or greater than log in'
                        })
                        continue

                for time in range(len(day_log_in_employee_records)):
                    attendance_vals_list.append({
                        'employee_id': employee.id,
                        'check_in': day_log_in_employee_records[time].punch_time,
                        'check_out': day_log_out_employee_records[time].punch_time,
                    })
                day_machine_records.write({'state': 'success'})
        self.env['hr.attendance'].create(attendance_vals_list)

    def action_skip_record(self):
        self.write({'state': 'skip'})

    # def unlink(self):
    #     for rec in self:
    #         if rec.machine_record_id.split()[0] != 'CMAR':
    #             pass
    #             #raise ValidationError(_("You can\'t delete attendance record created from machine........"))
    #     return super(MachineAttendanceRecord, self).unlink()

    def set_state_success(self):
        self.write({'state': 'success'})
    def set_state_failure(self):
        self.write({'state': 'failure'})

    def set_state_skip(self):
        self.write({'state': 'skip'})
