import logging
# import pandas as pd
import os

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
    attend_record_log_check_in_id = fields.Many2one('machine.attendance.record',
                                                    string='Attendance Record Log Check IN')
    attend_record_log_check_out_id = fields.Many2one('machine.attendance.record',
                                                     string='Attendance Record Log Check Out')

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

    @staticmethod
    def get_data_from_excel():
        path = os.getcwd()
        # Example usage
        file_path = path + '/attendance_api_new/attendance/JBMAttendance17Sep2023.xlsx'  # Replace with the path to your Excel file
        sheet_name = 'Sheet 1'  # Replace with the name of your sheet in the Excel file

        # Define a mapping of old column names to new column names
        column_mapping = {
            'TR_ID': 'record_ID',
            'TR_IOFLAG': 'punch_type',
            'CARD_NO': 'employee_ID',
            'TR_TIME': 'punch_time',
        }

        try:
            # Read the Excel file into a pandas DataFrame
            df = pd.read_excel(file_path, sheet_name=sheet_name)

            # Rename columns based on the provided mapping
            df = df.rename(columns=column_mapping)
            columns_to_drop = ['TR_CARDNUM', 'TR_EMPID']
            df = df.drop(columns=columns_to_drop)
            df['punch_time'] = df['punch_time'].dt.strftime('%Y-%m-%dT%H:%M:%S')
            df['employee_ID'] = df['employee_ID'].astype(str)

            # Convert the DataFrame to a dictionary
            data_dict = df.to_dict(orient='records')

            return data_dict
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return None

    def get_attendance_data(self):
        # attendance_data = self.get_data_from_excel()
        try:
            url = self.env['ir.config_parameter'].sudo().get_param('attendance_api_link')
            if url:
                _logger.info("--> Running Fetch Attendance")
                response = requests.get(
                    url=url,
                    headers={
                        'Content-Type': 'application/json',
                    }, )
                response.raise_for_status()
                attendance_data = json.loads(response.text)
                # attendance_data = []
                attendance_data = sorted(attendance_data, key=lambda x: (
                    (datetime.strptime(x['punch_time'].split('T', 1)[0], '%Y-%m-%d').date())))
                attendance_data = self._remove_duplication_data(attendance_data)
                attendance_dict = {}
                for attend_data in attendance_data:
                    if attend_data.get('employee_ID') in attendance_dict:
                        attendance_dict[attend_data['employee_ID']].append(attend_data)
                    else:
                        attendance_dict[attend_data.get('employee_ID')] = [attend_data]
                _logger.info("--> attendance_dict {}".format(attendance_dict))
                for qid, records_list in attendance_dict.items():
                    _logger.info("---> Checking existing attendance")

                    self._check_attendance_record_exists(records_list)
                    # after remove existing record
                    # add cases for entering attendances in attendance_dict
                    self._insert_attendance_records(qid, records_list)

        except Exception as e:
            _logger.info(e)
            raise ValueError(e)

    def _insert_attendance_records(self, qid, attendance_list):
        """Base method to insert the records."""
        _logger.info("Qid of employee {}".format(qid))
        _logger.info("Records {}".format(attendance_list))
        for record in attendance_list:
            employee_id = self._get_employee(qid)

            if not employee_id:
                return
            punch_type = record.get('punch_type')
            punch_time_str = record.get('punch_time')
            punch_time_native = datetime.strptime(punch_time_str, '%Y-%m-%dT%H:%M:%S')
            # punch_time = punch_time_native
            rec_id = record.get('record_ID')

            punch_time = self._convert_punch_time(punch_time_native)
            vals = {
                'punch_time': punch_time,
                'rec_id': rec_id,
                'employee_id': employee_id,
                'punch_time_native': punch_time_native,
            }
            _logger.info("Qid of employee {}".format(qid))
            _logger.info("Inserting record with vals {}".format(vals))
            machine_attendance_record = self.env['machine.attendance.record'].update_or_create_attendance_record(
                machine_record_id=rec_id,
                punch_time=punch_time_native,
                employee_id=employee_id.id,
                punch_type=punch_type,
            )
            try:
                if punch_type == 'I':
                    skip = self._check_validity_check_in(employee_id, punch_time_native)
                    if skip:
                        if machine_attendance_record:
                            machine_attendance_record.state = 'skip'
                            self.env.cr.commit()
                        _logger.info("Invalid Punch IN {}, qid {}".format(vals, qid))
                        # write status of log
                        continue
                    vals['machine_attendance_record'] = machine_attendance_record
                    self._insert_check_in(**vals)
                elif punch_type == 'O':
                    skip = self._check_validity_check_out(employee_id, punch_time_native)
                    if skip:
                        if machine_attendance_record:
                            machine_attendance_record.state = 'skip'
                            self.env.cr.commit()
                        _logger.info("Invalid Punch OUT {}, qid {}".format(vals, qid))
                        # write status of log
                        continue
                    vals['machine_attendance_record'] = machine_attendance_record
                    self._insert_check_out(**vals)

                if machine_attendance_record:
                    machine_attendance_record.state = 'success'
                    self.env.cr.commit()
                # write status of log
            except Exception as e:
                if machine_attendance_record:
                    machine_attendance_record.write({
                       'state':  'failure',
                       'error_message':  str(e)
                    })
                    # self.env.cr.execute(
                    #     f"UPDATE machine_attendance_record SET state = 'failure', error_message ='{str(e)}' WHERE id = {machine_attendance_record.id}"
                    # )
                    self.env.cr.commit()
                raise Exception()

    def _insert_check_in(self, **kwargs):
        """Insert check in."""
        _logger.info('--> Insert check in')
        _logger.info('--> Checking cases of check in')
        employee_id = kwargs.get("employee_id")
        rec_id = kwargs.get("rec_id")
        punch_time = kwargs.get("punch_time")
        machine_attendance_record = kwargs.get("machine_attendance_record")
        last_attendance = self._get_last_attendance_check_in(employee_id)
        if not last_attendance:
            _logger.info('--> Case 1 not exist last attendance')
            _logger.info('--> Add new attendance')
            self.sudo().create({
                'check_in': punch_time,
                'check_in_record_id': rec_id,
                'employee_id': employee_id[0].id,
                'attend_record_log_check_in_id': machine_attendance_record and machine_attendance_record.id,
            })
            self.env.cr.commit()
            return True
        _logger.info("---> Last Attendance {}, check_in {}, check_out {}".
                     format(last_attendance, last_attendance.check_in, last_attendance.check_out))

        if last_attendance and not last_attendance.check_out:
            _logger.info('--> Case 2 exist last attendance and not check out')
            _logger.info('--> Add check out to last attendance')
            _logger.info('--> Insert new attendance')
            last_attendance.sudo().write({
                'check_out': last_attendance[0].check_in + timedelta(seconds=1),
                'check_out_record_id': rec_id,
            })
            self.sudo().create({
                'check_in': punch_time,
                'check_in_record_id': rec_id,
                'employee_id': employee_id[0].id,
                'attend_record_log_check_in_id': machine_attendance_record and machine_attendance_record.id,
            })

            self.env.cr.commit()
            return True
        elif last_attendance and last_attendance.check_out:
            _logger.info('--> Case 3 exist attendance and check out')
            _logger.info('--> Add new attendance')
            self.sudo().create({
                'check_in': punch_time,
                'check_in_record_id': rec_id,
                'employee_id': employee_id[0].id,
                'attend_record_log_check_in_id': machine_attendance_record and machine_attendance_record.id
            })
            self.env.cr.commit()
            return True
        # else:
        #     self.sudo().create({
        #         'check_in': punch_time,
        #         'check_in_record_id': rec_id,
        #         'employee_id': employee_id[0].id
        #     })

        # self.env.cr.commit()
        # return True

    def _insert_check_out(self, **kwargs):
        """Insert check out."""
        _logger.info('--> Insert check out')
        _logger.info('--> Checking cases of check out')
        employee_id = kwargs.get("employee_id")
        rec_id = kwargs.get("rec_id")
        punch_time = kwargs.get("punch_time")
        punch_time_native = kwargs.get("punch_time_native")
        machine_attendance_record = kwargs.get("machine_attendance_record")
        last_attendance_no_check_out = self._get_last_attendance_check_out(employee_id, punch_time_native)
        if not last_attendance_no_check_out:
            _logger.info("---> Not found last last_attendance_no_check_out")
            _logger.info("---> Skipping this record {}", kwargs)
            return False
        _logger.info("punch_time_native {}".format(punch_time_native))
        _logger.info("punch_time {}".format(punch_time))
        _logger.info("---> Last Attendance {}, check_in {}, check_out {}".
                     format(last_attendance_no_check_out,
                            last_attendance_no_check_out.check_in,
                            last_attendance_no_check_out.check_out))
        if last_attendance_no_check_out and \
                not last_attendance_no_check_out.check_out and punch_time_native > \
                last_attendance_no_check_out[0].check_in:
            _logger.info("---> Case 1, Not exist check_out")
            _logger.info("---> Add a new check_out")
            last_attendance_no_check_out[0].sudo().write({
                'check_out': punch_time,
                'check_out_record_id': rec_id,
                'attend_record_log_check_out_id': machine_attendance_record and machine_attendance_record.id
            })
        elif last_attendance_no_check_out and last_attendance_no_check_out.check_out and punch_time_native > \
                last_attendance_no_check_out[0].check_in:
            _logger.info("---> Case 2, Exist check_out")
            _logger.info("---> Update check_out")
            last_attendance_no_check_out[0].sudo().write({
                'check_out': punch_time,
                'check_out_record_id': rec_id,
                'attend_record_log_check_out_id': machine_attendance_record and machine_attendance_record.id
            })
        else:
            _logger.info("---> Attendance not entered yet")

        self.env.cr.commit()
        return True

    def _get_last_attendance_check_in(self, employee_id):
        self._cr.execute("""SELECT id FROM hr_attendance 
        WHERE employee_id = %s AND check_in IS NOT NULL 
        ORDER BY check_in DESC LIMIT 1""" % employee_id.id)
        res_id = self._cr.fetchone()
        res_id = res_id and res_id[0]
        if not res_id:
            return False
        return self.browse(res_id)

    def _get_last_attendance_check_out(self, employee_id, punch_time):
        beginning_date = punch_time.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = (beginning_date + timedelta(days=1)) - timedelta(microseconds=1)
        beginning_date_str = beginning_date.strftime('%Y-%m-%d %H:%M:%S')
        end_date_str = end_date.strftime('%Y-%m-%d %H:%M:%S')
        _logger.info("Get lasted attendance check out")
        _logger.info("beginning_date_str {}, end_date_str {}".format(beginning_date_str, end_date_str))
        self._cr.execute("""
            SELECT *
            FROM hr_attendance
            WHERE employee_id = %s AND 
                  check_out IS NULL 
            ORDER BY check_in DESC LIMIT 1
        """ % (employee_id.id))
        res_id = self._cr.fetchone()
        res_id = res_id and res_id[0]
        if not res_id:
            return False
        return self.browse(res_id)

    def get_last_attendance_before_check_in(self, employee_id, punch_time_utc_str):
        self._cr.execute("""SELECT id FROM hr_attendance 
                WHERE employee_id = %s AND check_in <= '%s'
                ORDER BY check_in DESC LIMIT 1""" % (employee_id.id, punch_time_utc_str))
        last_attendance_before_check_in = self._cr.fetchone()
        last_attendance_before_check_in = last_attendance_before_check_in and last_attendance_before_check_in[0]
        return last_attendance_before_check_in

    def get_last_attendance_before_check_out(self, employee_id, punch_time_utc_str):
        self._cr.execute("""SELECT id FROM hr_attendance 
                   WHERE employee_id = %s AND check_in < '%s' AND check_out IS NULL
                   ORDER BY check_in DESC LIMIT 1""" % (employee_id.id, punch_time_utc_str))
        last_attendance_before_check_out = self._cr.fetchone()
        last_attendance_before_check_out = last_attendance_before_check_out and last_attendance_before_check_out[0]
        return last_attendance_before_check_out

    def _check_validity_check_in(self, employee_id, punch_time):
        """ Verifies the validity of the attendance record compared to the others from the same employee.
            For the same employee we must have :
                * maximum 1 "open" attendance record (without check_out)
                * no overlapping time slices with previous employee records
            Return True if incorrect punch_time otherwise return False
        """
        # Convert punch_time to UTC timezone to use in sql raw query.
        punch_time_utc = self.convert_to_datetime_utc(punch_time)
        punch_time_utc_str = punch_time_utc.strftime('%Y-%m-%d %H:%M:%S')
        _logger.info("Checking validity punch in")
        _logger.info("punch_time_utc {}".format(punch_time_utc))
        _logger.info("punch_time {}".format(punch_time))
        last_attendance_before_check_in = self. \
            get_last_attendance_before_check_in(employee_id, punch_time_utc_str)
        if not last_attendance_before_check_in:
            return False
        last_attendance_before_check_in = self.browse(last_attendance_before_check_in)
        _logger.info("last_attendance_before_check_in {}, check_in {}, check_out {}"
                     .format(last_attendance_before_check_in,
                             last_attendance_before_check_in.check_in,
                             last_attendance_before_check_in.check_out))
        if last_attendance_before_check_in and last_attendance_before_check_in.check_in == punch_time_utc:
            return True
        elif last_attendance_before_check_in and last_attendance_before_check_in.check_out and \
                last_attendance_before_check_in.check_out > punch_time_utc:
            return True
        return False

    def _check_validity_check_out(self, employee_id, punch_time):
        """ Verifies the validity of the attendance record compared to the others from the same employee.
            For the same employee we must have :
                * maximum 1 "open" attendance record (without check_out)
                * no overlapping time slices with previous employee records
            Return True if incorrect punch_time otherwise return False
        """
        # Convert punch_time to UTC timezone to use in sql raw query.
        punch_time_utc = self.convert_to_datetime_utc(punch_time)
        punch_time_utc_str = punch_time_utc.strftime('%Y-%m-%d %H:%M:%S')
        _logger.info("Checking validity punch out")
        _logger.info("punch_time_utc {}".format(punch_time_utc))
        _logger.info("punch_time {}".format(punch_time))
        last_attendance_before_check_in = self.get_last_attendance_before_check_in(employee_id, punch_time_utc_str)
        last_attendance_before_check_out = self.get_last_attendance_before_check_out(employee_id, punch_time_utc_str)
        if not (last_attendance_before_check_in and last_attendance_before_check_out):
            return False

        last_attendance_before_check_in = self.browse(last_attendance_before_check_in)
        last_attendance_before_check_out = self.browse(last_attendance_before_check_out)
        _logger.info("last_attendance_before_check_in {}, check_in {}, check_out {}"
                     .format(last_attendance_before_check_in,
                             last_attendance_before_check_in.check_in,
                             last_attendance_before_check_in.check_out))
        _logger.info("last_attendance_before_check_out {}, check_in {}, check_out {}"
                     .format(last_attendance_before_check_out,
                             last_attendance_before_check_out.check_in,
                             last_attendance_before_check_out.check_out))
        if last_attendance_before_check_out and last_attendance_before_check_out != last_attendance_before_check_in:
            return True
        return False

    def _check_attendance_record_exists(self, records_list):
        """Checks if the attendance record exists."""
        for record in records_list:
            record_ID = record.get('record_ID')
            self._cr.execute("""SELECT check_in_record_id,check_out_record_id 
            FROM hr_attendance WHERE check_in_record_id = %s OR check_out_record_id = %s""" % (record_ID, record_ID))
            if self._cr.fetchone():
                _logger.info("Exists record {}".format(record_ID))
                records_list.remove(record)
                _logger.info("--> Delete exist attendance")

    def _get_employee(self, qid):
        """Get the employee based on the qid."""
        return self.env['hr.employee'].sudo().search([
            ('employee_qid_number', '=', str(qid))],
            limit=1)

    @staticmethod
    def convert_to_datetime_utc(punch_time):
        local_tz = pytz.timezone('Asia/Qatar')
        utc_tz = pytz.timezone('UTC')
        punch_time_local = local_tz.localize(punch_time, is_dst=None)  # Make sure punch_time is localized
        punch_time_utc = punch_time_local.astimezone(utc_tz).replace(tzinfo=None)
        return punch_time_utc

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
