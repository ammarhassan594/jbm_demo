from odoo import models
import pytz
from datetime import datetime
from dateutil.relativedelta import relativedelta


class PayrollSummary(models.AbstractModel):
    _name = 'report.attendance_analysis_report.attendance_analysis_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def date_range(self, start_dt, end_dt, step=relativedelta(days=1)):
        dates = []

        while start_dt <= end_dt:
            dates.append(start_dt)
            start_dt += step

        return dates

    def get_day_status(self, employee, today):
        contract = employee.contract_ids.filtered(
            lambda contract: (contract.date_end and contract.date_start <= today <= contract.date_end) \
                             or (not contract.date_end and contract.date_start <= today)
        )
        weekend = str(today.weekday()) not in set(
            contract.resource_calendar_id.attendance_ids.mapped('dayofweek'))
        if weekend:
            return 'Weekend'

        public_holiday = contract.resource_calendar_id.global_leave_ids.filtered(
            lambda x: x.date_from.date() <= today <= x.date_to.date())
        if public_holiday:
            return 'Public Holiday'

        leaves = self.env['hr.leave'].search([('employee_id', '=', employee.id), ('request_date_from', '<=', today),
                                              ('request_date_to', '>=', today), ('state', '=', 'validate')], limit=1)
        if leaves:
            return leaves.holiday_status_id.name

        return 'Absence'

    def generate_xlsx_report(self, workbook, data, attendance_analysis):
        sheet = workbook.add_worksheet('Attendance Analysis')
        data_format = workbook.add_format({'align': 'center'})
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
        date_time_format = workbook.add_format({'num_format': 'DD/MM/YYYY HH:MM:SS'})

        header_row_style = workbook.add_format(
            {'bold': True, 'align': 'center', 'bg_color': 'white', 'border': True})
        for obj in attendance_analysis:
            row = 0
            col = 0
            # Header row

            sheet.set_column('A:A', 20)
            sheet.set_column('B:B', 40)
            sheet.set_column('C:C', 20)
            sheet.set_column('D:D', 20)
            sheet.set_column('E:E', 20)
            sheet.set_column('F:F', 20)
            sheet.write(row, col, 'Emp No', header_row_style)
            sheet.write(row, col + 1, 'Emp Name', header_row_style)
            sheet.write(row, col + 2, 'Date', header_row_style)
            sheet.write(row, col + 3, 'Check-In', header_row_style)
            sheet.write(row, col + 4, 'Check-Out', header_row_style)
            sheet.write(row, col + 5, 'Day Status', header_row_style)

            row += 1
            employees = obj.employee_ids or self.env['hr.employee'].search([])
            time_zone = pytz.timezone(self._context.get('tz') or 'Asia/Qatar')
            report_days = self.date_range(obj.date_from, obj.date_to)
            domain = [('employee_id', 'in', employees.ids)]
            if obj.date_from:
                search_date_from = datetime.combine(obj.date_from, datetime.min.time())
                domain.append(('check_in', '>=', search_date_from))
            if obj.date_to:
                search_date_to = datetime.combine(obj.date_to, datetime.max.time())
                domain.append(('check_in', '<=', search_date_to))

            attendances = self.env['hr.attendance'].read_group(
                domain=domain, fields=['ids:array_agg(id)', 'employee_id'],
                groupby=['employee_id'], orderby='check_in DESC', lazy=False)
            attendance_data = dict((item['employee_id'][0], item['ids']) for item in attendances)
            for employee_id, employee_attendance in attendance_data.items():
                employee_obj = self.env['hr.employee'].browse(employee_id)
                employee_attendance_obj = self.env['hr.attendance'].browse(employee_attendance)
                attendance_days = set([attendance.check_in.date() for attendance in employee_attendance_obj])
                for report_day in report_days:

                    sheet.write(row, col,
                                employee_obj.registration_number if employee_obj.registration_number else '',
                                data_format)

                    sheet.write(row, col + 1,
                                employee_obj.name,
                                data_format)

                    sheet.write(row, col + 2,
                                report_day,
                                date_format)
                    if report_day in attendance_days:
                        sheet.write(row, col + 3,
                                    employee_attendance_obj.filtered(
                                        lambda attendance: attendance.check_in.date() == report_day)[
                                        0].check_in.astimezone(tz=time_zone).replace(tzinfo=None), date_time_format)
                        last_check_out = employee_attendance_obj.filtered(lambda
                                                                              attendance: attendance.check_in.date() == report_day \
                                                                                          and attendance.check_out)
                        sheet.write(row, col + 4,
                                    last_check_out[-1].check_out.astimezone(tz=time_zone).replace(
                                        tzinfo=None) if last_check_out else '',
                                    date_time_format)

                        sheet.write(row, col + 5, '', data_format)

                    else:

                        sheet.write(row, col + 3, '', data_format)

                        sheet.write(row, col + 4, '', data_format)

                        sheet.write(row, col + 5, self.get_day_status(employee_obj, report_day), data_format)

                    row += 1
