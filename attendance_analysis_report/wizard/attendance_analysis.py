from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime
from pytz import timezone

def convert_TZ_UTC(mydate, tz):
    fmt = "%Y-%m-%d %H:%M:%S"
    # Current time in UTC
    now_utc = datetime.now(timezone('UTC'))
    # Convert to current user time zone
    now_timezone = now_utc.astimezone(tz)
    UTC_OFFSET_TIMEDELTA =  datetime.strptime(now_timezone.strftime(fmt),fmt) - datetime.strptime(now_utc.strftime(fmt), fmt)
    local_datetime = datetime.strptime(mydate.strftime(fmt), fmt)
    result_utc_datetime = local_datetime + UTC_OFFSET_TIMEDELTA
    return result_utc_datetime


def get_float_from_time(time):
    ts_qatar = timezone('Asia/Qatar')
    time = convert_TZ_UTC(time, ts_qatar)
    time_type = datetime.strftime(time, "%H:%M")
    signOnP = [int(n) for n in time_type.split(":")]
    signOnH = signOnP[0] + signOnP[1] / 60.0
    return signOnH


def convert_float_to_time(time):
    ts_qatar = timezone('Asia/Qatar')
    time = convert_TZ_UTC(time, ts_qatar)
    print('time', time)
    str_time = str((time.hour + time.minute / 60))
    official_hour = str_time.split('.')[0]
    official_minute = ("%2d" % int(str(float("0." + str_time.split('.')[1]) * 60).split('.')[0])).replace(' ', '0')
    str_time = official_hour + ":" + official_minute
    str_time = datetime.strptime(str_time, "%H:%M").time()
    return str_time


class AttendanceAnalysis(models.TransientModel):
    _name = "attendance.analysis"

    date_from = fields.Date(string="Period From", required=True)
    date_to = fields.Date(string="Period To", required=True)
    employee_ids = fields.Many2many(comodel_name='hr.employee', string='Employees')

    @api.constrains('date_to')
    def _check_end_date(self):
        for rec in self:
            date_from = rec.date_from
            date_to = rec.date_to
            if all((date_from, date_to, date_to < date_from)):
                raise ValidationError(_("End Date Must be greater than date start date"))

    def _get_report_filename(self):
        report_name = 'Attendance Analysis Report'
        return report_name


    def print_attendance_analysis_report(self):
        data = {
        }
        return self.env.ref('attendance_analysis_report.attendance_analysis_report').with_context(
            landscape=True).report_action(self, data=data)
