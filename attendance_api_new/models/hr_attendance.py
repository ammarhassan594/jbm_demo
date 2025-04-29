import logging
from odoo import models, fields, api, _
import requests
import json
from datetime import datetime
import pytz
from datetime import timedelta

_logger = logging.getLogger(__name__)


class HrAttendanceCustom(models.Model):
    _inherit = 'hr.attendance'

    check_in_record_id = fields.Integer('Check in Record ID')
    check_out_record_id = fields.Integer('Check out Record ID')

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

    def get_attendance_data(self):
        try:
            url = self.env['ir.config_parameter'].sudo().get_param('attendance_api_link')
            if url:
                response = requests.get(
                    url=url,
                    headers={
                        'Content-Type': 'application/json',
                    }, )
                response.raise_for_status()
                attendance_data = json.loads(response.text)
                attendance_data = sorted(attendance_data, key=lambda x: (
                    (datetime.strptime(x['punch_time'].split('T', 1)[0], '%Y-%m-%d').date())))
                attendance_data = self._remove_duplication_data(attendance_data)
                # attendance_data = attendance_data[:1]
                hr_att_obj = self.env['hr.attendance']

                another_data = []
                for data in attendance_data:
                    qid = data.get('employee_ID')
                    punch_type = data.get('punch_type')
                    punch_time_str = data.get('punch_time')
                    punch_time = datetime.strptime(punch_time_str, '%Y-%m-%dT%H:%M:%S')
                    rec_id = data.get('record_ID')
                    all_attendance = hr_att_obj.sudo().search([])

                    att_record_ids = all_attendance and all_attendance.sudo().filtered(
                        lambda x: x.employee_id.employee_qid_number == str(qid)) or False
                    full_attendance = att_record_ids and att_record_ids.sudo().filtered(
                        lambda x: x.check_in and x.check_out) or False
                    attendance_yet_to_check_out = att_record_ids and att_record_ids.sudo().filtered(
                        lambda x: x.check_in and not x.check_out) or False
                    employee_id = self.env['hr.employee'].sudo().search([('employee_qid_number', '=', str(qid))], limit=1)
                    check_in_recs = all_attendance.mapped('check_in_record_id')
                    check_out_recs = all_attendance.mapped('check_out_record_id')
                    if employee_id:
                        fmt = "%Y-%m-%d %H:%M:%S"
                        tz = pytz.timezone('Asia/Qatar')
                        now_utc = datetime.now(pytz.timezone('UTC'))
                        now_timezone = now_utc.astimezone(tz)
                        UTC_OFFSET_TIMEDELTA = datetime.strptime(now_timezone.strftime(fmt), fmt) - datetime.strptime(
                            now_utc.strftime(fmt), fmt)

                        punch_time = datetime.strptime(punch_time.strftime(fmt), fmt)
                        punch_time = punch_time - UTC_OFFSET_TIMEDELTA

                        if attendance_yet_to_check_out and punch_type == 'O' and punch_time > \
                                attendance_yet_to_check_out[0].check_in and rec_id not in check_out_recs:
                            attendance_yet_to_check_out[0].sudo().write({
                                'check_out': punch_time,
                                'check_out_record_id': rec_id,
                            })

                        elif not attendance_yet_to_check_out and punch_type == 'I' and rec_id not in check_in_recs:
                            if full_attendance:
                                days = [x.check_in.date() for x in full_attendance if
                                        x.check_in <= punch_time <= x.check_out]

                                if punch_time.date() not in days:
                                    hr_att_obj.sudo().create({
                                        'check_in': punch_time,
                                        'check_in_record_id': rec_id,
                                        'employee_id': employee_id[0].id
                                    })
                            else:
                                hr_att_obj.sudo().create({
                                    'check_in': punch_time,
                                    'check_in_record_id': rec_id,
                                    'employee_id': employee_id[0].id
                                })

                        elif attendance_yet_to_check_out and punch_type == 'I' and rec_id not in check_in_recs:
                            if attendance_yet_to_check_out[0].check_in.date() <= punch_time.date():
                                attendance_yet_to_check_out[0].sudo().write({
                                    'check_out': attendance_yet_to_check_out[0].check_in + timedelta(seconds=1),
                                    'check_out_record_id': rec_id,
                                })

                                hr_att_obj.sudo().create({
                                    'check_in': punch_time,
                                    'check_in_record_id': rec_id,
                                    'employee_id': employee_id[0].id
                                })

                        else:
                            continue
                    else:
                        _logger.info('No Employee found with the qid : %s', qid)
                        continue

        except Exception as e:
            _logger.info(e)
            raise ValueError(e)
