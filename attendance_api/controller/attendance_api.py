from odoo import http
from logging import getLogger
from odoo.http import request
from datetime import datetime
from dateutil.relativedelta import relativedelta

_logger = getLogger("Attendance API Call")


class AttendanceAPi(http.Controller):

    @http.route('/api/attendance/insert', type='json', auth='none', methods=['POST'])
    def attendance_insert(self, **additional_values):
        env = request.env
        data = request.jsonrequest

        res_config = env['res.config.settings'].sudo().search(
            [('attendance_api_token', '=', request.httprequest.values['token'])])
        try:
            if res_config:
                if data:
                    if data.get('attendance_records'):
                        for record in data.get('attendance_records'):
                            punch_id = record['punch_id']
                            date = datetime.strptime(record['date'], '%m/%d/%Y %H:%M:%S')
                            date = date - relativedelta(hours=3)
                            employee_id = record['employee_id']
                            punch_type = record['punch_type']
                            employee_record_id = env['hr.employee'].sudo().search([('punch_user_id', '=', employee_id)])
                            if not employee_record_id:
                                request.env['attendance.api.log'].sudo().create({
                                    'employee_id' : employee_id,
                                    'punch_type' : punch_type,
                                    'date' : date,
                                    'punch_id' : punch_id,
                                    'error' : 'Employee is not exist in system'
                                })
                                continue
                            if punch_type == 'in':
                                attendance_id = env['hr.attendance'].sudo().search([('employee_id', '=', employee_record_id.id),
                                                                                    ('check_in_punch_id', '=', punch_id)])
                                if attendance_id:
                                    request.env['attendance.api.log'].sudo().create({
                                        'employee_id': employee_id,
                                        'punch_type': punch_type,
                                        'date': date,
                                        'punch_id': punch_id,
                                        'error': 'You have already Check by same punch id',
                                        'attendance_id' : attendance_id.id
                                    })
                                    continue
                                employee_check_in_attendance_id = env['hr.attendance'].sudo().search([('check_in', '!=', False),
                                                                                                       ('check_out', '=', False),
                                                                                                       ('employee_id', '=', employee_record_id.id)]
                                                                                                      ,limit=1)
                                if employee_check_in_attendance_id:
                                    request.env['attendance.api.log'].sudo().create({
                                        'employee_id': employee_id,
                                        'punch_type': punch_type,
                                        'date': date,
                                        'punch_id': punch_id,
                                        'error': 'You have already Check In with other punch id',
                                        'attendance_id' : employee_check_in_attendance_id.id
                                    })
                                    continue
                                    # return 'You have already Check In with other punch id'
                                new_attendance = env['hr.attendance'].sudo().create({
                                    'employee_id': employee_record_id.id,
                                    'check_in': date,
                                    'check_in_punch_id': punch_id,
                                })
                                if new_attendance:
                                    request.env['attendance.api.log'].sudo().create({
                                        'employee_id': employee_id,
                                        'punch_type': punch_type,
                                        'date': date,
                                        'punch_id': punch_id,
                                        'attendance_id' : new_attendance.id
                                    })
                                    continue
                            elif punch_type == 'out':
                                attendance_id = env['hr.attendance'].sudo().search([('employee_id', '=', employee_record_id.id)])
                                attendance_id = attendance_id.filtered(lambda s: s.check_in.date() == date.date())
                                if attendance_id and attendance_id.check_out:
                                    request.env['attendance.api.log'].sudo().create({
                                        'employee_id': employee_id,
                                        'punch_type': punch_type,
                                        'date': date,
                                        'punch_id': punch_id,
                                        'attendance_id' : attendance_id.id,
                                        'error' : 'You have already Check Out'
                                    })
                                    continue
                                if attendance_id and attendance_id.check_in > date:
                                    request.env['attendance.api.log'].sudo().create({
                                        'employee_id': employee_id,
                                        'punch_type': punch_type,
                                        'date': date,
                                        'punch_id': punch_id,
                                        'error' : 'Check out time is earlier than check in time'
                                    })
                                    continue
                                elif attendance_id:
                                    attendance_id.sudo().write({
                                        'check_out': date,
                                        'check_out_punch_id': punch_id
                                    })
                                    request.env['attendance.api.log'].sudo().create({
                                        'employee_id': employee_id,
                                        'punch_type': punch_type,
                                        'date': date,
                                        'punch_id': punch_id,
                                        'attendance_id': attendance_id.id,
                                    })
                                    continue
                        return 'Attendance records updated Successfully'
            else:
                return 'Authentication is failed due to token is wrong'
        except Exception as e:
            return e
