from odoo import api, fields, models, _
from datetime import datetime, date
import io
import xlwt
import base64
from io import BytesIO
from xlwt import Workbook, easyxf
import xlsxwriter
from odoo.http import request


class EmployeeCustomReport(models.TransientModel):
    _name = "custom.reports"

    from_date = fields.Date(string="Date")
    to_date = fields.Date(string="To Date")
    report_type = fields.Selection(
        [('employee_end', 'WASEEF END EMPLOYEE INFORMATION REPORT'),
         ('employee_info', 'WASEEF EMPLOYEE INFORMATION REPORT'),
         ('employee_info_as_date', 'WASEEF EMPLOYEE INFORMATION AS DATE'),
         ('employee_info_arabic', 'WASEEF EMPLOYEE INFORMATION REPORT- ARABIC'),
         ('leave_balance', 'LEAVE BALANCE REPORT')],
        string="Report", required=True)

    in_house_employee = fields.Boolean(string="In-House")
    staff_employee = fields.Boolean(string="Staff")
    temporary_employee = fields.Boolean(string="Temporary")

    def print_report(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/generate/custom_report/%s' % (self.id),
            'target': 'new',
        }

    def generate_xlsx_report(self):
        file_name = dict(self._fields['report_type'].selection).get(self.report_type)
        request.context = dict(request.context, file_name=file_name)
        if self.report_type == 'employee_end':
            return self.export_end_employee_info_report()
        if self.report_type == 'employee_info':
            return self.export_employee_info_report()
        if self.report_type == 'employee_info_as_date':
            return self.export_employee_info_as_date_report()
        if self.report_type == 'employee_info_arabic':
            return self.export_employee_info_arabic_report()
        if self.report_type == 'leave_balance':
            return self.action_print_leave_balance()

    def _get_sick_leave_details(self, employee):
        for rec in self:
            sick_leaves = rec.env['hr.leave'].search(
                [('employee_id', '=', employee.id), ('state', '=', 'validate'),
                 ('holiday_status_id.is_sick_leave', '=', True),
                 ('date_from', '<=', rec.from_date)])
            sick_allocations = rec.env['hr.leave.allocation'].search(
                [('employee_id', '=', employee.id), ('state', '=', 'validate'),
                 ('holiday_status_id.is_sick_leave', '=', True),
                 ('create_date', '<=', rec.from_date.strftime('%Y-%m-%d %H:%M:%S'))])

            sick_leave = sick_leaves.filtered(lambda x: x.holiday_status_id.code == 'SL')
            s_sick_leave = sick_leaves.filtered(lambda x: x.holiday_status_id.code == 'SSL')
            l_sick_leave = sick_leaves.filtered(lambda x: x.holiday_status_id.code == 'LSL')
            sl_allocation = sick_allocations.filtered(lambda x: x.holiday_status_id.code == 'SL')
            ssl_allocation = sick_allocations.filtered(lambda x: x.holiday_status_id.code == 'SSL')
            lsl_allocation = sick_allocations.filtered(lambda x: x.holiday_status_id.code == 'LSL')
            sick_leave_days = sum(sick_leave.mapped('number_of_days'))
            short_s_leave_days = sum(s_sick_leave.mapped('number_of_days'))
            long_s_leave_days = sum(l_sick_leave.mapped('number_of_days'))
            sick_allocations_days = sum(sl_allocation.mapped('number_of_days'))
            short_sick_allocations_days = sum(ssl_allocation.mapped('number_of_days'))
            long_sick_allocations_days = sum(lsl_allocation.mapped('number_of_days'))
            sick_balance = sick_allocations_days - sick_leave_days
            short_sick_balance = short_sick_allocations_days - short_s_leave_days
            long_sick_balance = long_sick_allocations_days - long_s_leave_days
            return sick_leave_days, short_s_leave_days, long_s_leave_days, sick_allocations_days, short_sick_allocations_days, \
                long_sick_allocations_days, sick_balance, short_sick_balance, long_sick_balance

    def action_print_leave_balance(self):
        workbook = xlwt.Workbook()
        xlwt.add_palette_colour("custom_colour", 0x21)
        workbook.set_colour_RGB(0x21, 231, 243, 253)
        date_from = self.from_date
        first_day = self.from_date.replace(day=1, month=1)
        amount_tot = 0
        hr_holiday_objs_list = []
        column_heading_style = easyxf(
            'font:height 200;font:bold True;align: vert centre, horz center;pattern: pattern solid,fore-colour custom_colour;')
        annual_report = 'ANNUAL LEAVE BALANCE REPORT'
        sick_report = 'SICK LEAVE BALANCE REPORT'
        String = "AS DATE :" + " " + str(self.from_date.strftime('%d-%m-%Y'))
        worksheet = workbook.add_sheet('Annual Leave Balance')
        worksheet.write_merge(0, 1, 1, 3, annual_report,
                              easyxf('font:height 300; align: horiz center;font:bold True;'))
        worksheet.write_merge(3, 3, 0, 1, String, easyxf('font:height 200; align: horiz center;font:bold True;'))
        col = 0
        worksheet.row(5).height = 500
        worksheet.write(5, col, _('Employee Number'), column_heading_style)
        col += 1
        worksheet.write(5, col, _('Employee Name'), column_heading_style)
        col += 1
        worksheet.write(5, col, _('Employee Type'), column_heading_style)
        col += 1
        worksheet.write(5, col, _('Employee Joining Date'), column_heading_style)
        col += 1
        worksheet.write(5, col, _('Grade'), column_heading_style)
        col += 1
        worksheet.write(5, col, _('No of Leave Days'), column_heading_style)
        col += 1
        worksheet.write(5, col, _('No of Allocation Days'), column_heading_style)
        col += 1
        worksheet.write(5, col, _('Leave Balance'), column_heading_style)
        col += 1
        worksheet.col(0).width = 5000
        worksheet.col(1).width = 10000
        worksheet.col(2).width = 5000
        worksheet.col(3).width = 5000
        worksheet.col(4).width = 5000
        worksheet.col(5).width = 5000
        worksheet.col(6).width = 5000
        worksheet.col(7).width = 5000

        worksheet2 = workbook.add_sheet('Sick Leave Balance')
        worksheet2.write_merge(0, 1, 1, 3, sick_report,
                               easyxf('font:height 300; align: horiz center;font:bold True;'))
        worksheet2.write_merge(3, 3, 0, 1, String, easyxf('font:height 200; align: horiz center;font:bold True;'))
        col1 = 0
        worksheet2.row(5).height = 500
        worksheet2.write(5, col1, _('Employee Number'), column_heading_style)
        col1 += 1
        worksheet2.write(5, col1, _('Employee Name'), column_heading_style)
        col1 += 1
        worksheet2.write(5, col1, _('Employee Type'), column_heading_style)
        col1 += 1
        worksheet2.write(5, col1, _('Employee Joining Date'), column_heading_style)
        col1 += 1
        worksheet2.write(5, col1, _('Grade'), column_heading_style)
        col1 += 1
        worksheet2.write(5, col1, _('No of Leave Days'), column_heading_style)
        col1 += 1
        worksheet2.write(5, col1, _('No of Allocation Days'), column_heading_style)
        col1 += 1
        worksheet2.write(5, col1, _('Leave Balance'), column_heading_style)
        col1 += 1
        worksheet2.col(0).width = 5000
        worksheet2.col(1).width = 10000
        worksheet2.col(2).width = 5000
        worksheet2.col(3).width = 5000
        worksheet2.col(4).width = 5000
        worksheet2.col(5).width = 5000
        worksheet2.col(6).width = 5000
        worksheet2.col(7).width = 5000

        worksheet3 = workbook.add_sheet('Short Sick Leave Balance')
        worksheet3.write_merge(0, 1, 1, 3, sick_report,
                               easyxf('font:height 300; align: horiz center;font:bold True;'))
        worksheet3.write_merge(3, 3, 0, 1, String, easyxf('font:height 200; align: horiz center;font:bold True;'))
        col2 = 0
        worksheet3.row(5).height = 500
        worksheet3.write(5, col2, _('Employee Number'), column_heading_style)
        col2 += 1
        worksheet3.write(5, col2, _('Employee Name'), column_heading_style)
        col2 += 1
        worksheet3.write(5, col2, _('Employee Type'), column_heading_style)
        col2 += 1
        worksheet3.write(5, col2, _('Employee Joining Date'), column_heading_style)
        col2 += 1
        worksheet3.write(5, col2, _('Grade'), column_heading_style)
        col2 += 1
        worksheet3.write(5, col2, _('No of Leave Days'), column_heading_style)
        col2 += 1
        worksheet3.write(5, col2, _('No of Allocation Days'), column_heading_style)
        col2 += 1
        worksheet3.write(5, col2, _('Leave Balance'), column_heading_style)
        col2 += 1
        worksheet3.col(0).width = 5000
        worksheet3.col(1).width = 10000
        worksheet3.col(2).width = 5000
        worksheet3.col(3).width = 5000
        worksheet3.col(4).width = 5000
        worksheet3.col(5).width = 5000
        worksheet3.col(6).width = 5000
        worksheet3.col(7).width = 5000

        worksheet4 = workbook.add_sheet('Long Sick Leave Balance')
        worksheet4.write_merge(0, 1, 1, 3, sick_report,
                               easyxf('font:height 300; align: horiz center;font:bold True;'))
        worksheet4.write_merge(3, 3, 0, 1, String, easyxf('font:height 200; align: horiz center;font:bold True;'))
        col3 = 0
        worksheet4.row(5).height = 500
        worksheet4.write(5, col3, _('Employee Number'), column_heading_style)
        col3 += 1
        worksheet4.write(5, col3, _('Employee Name'), column_heading_style)
        col3 += 1
        worksheet4.write(5, col3, _('Employee Type'), column_heading_style)
        col3 += 1
        worksheet4.write(5, col3, _('Employee Joining Date'), column_heading_style)
        col3 += 1
        worksheet4.write(5, col3, _('Grade'), column_heading_style)
        col3 += 1
        worksheet4.write(5, col3, _('No of Leave Days'), column_heading_style)
        col3 += 1
        worksheet4.write(5, col3, _('No of Allocation Days'), column_heading_style)
        col3 += 1
        worksheet4.write(5, col3, _('Leave Balance'), column_heading_style)
        col3 += 1
        worksheet4.col(0).width = 5000
        worksheet4.col(1).width = 10000
        worksheet4.col(2).width = 5000
        worksheet4.col(3).width = 5000
        worksheet4.col(4).width = 5000
        worksheet4.col(5).width = 5000
        worksheet4.col(6).width = 5000
        worksheet4.col(7).width = 5000

        employee_annual_leave_balances = []
        domain = []
        if self.in_house_employee:
            domain.append('perm_in_house')
        if self.staff_employee:
            domain.append('perm_staff')
        if not domain:
            domain = ['perm_in_house', 'perm_staff']
        employees = self.env['hr.employee'].search([('wassef_employee_type', 'in', domain)])
        # record = self.env['hr.leave'].browse(43430)
        # fields.Date.context_today(record.with_context(tz=record.event_id.date_tz))
        for h in employees:
            # print(h.name, 'record tz', fields.Datetime.context_timestamp(self.with_context(tz=h.tz),
            #                                         record.create_date))
            leave_days = l_greater_than_date = days_diff_year = days_within_period = same_year_date_to_greater = 0
            employee_leave_dict = {}

            leaves = self.env['hr.leave'].search(
                [('employee_id', '=', h.id), ('state', '=', 'validate'), ('holiday_status_id.is_annual', '=', True),
                 ('request_date_from', '<=', date_from), ('request_date_to', '>=', first_day)]).filtered(
                lambda x: x.date_from.year == date_from.year and fields.Datetime.context_timestamp(self.with_context(tz=h.tz),
                                                            x.date_from).date() <= date_from and fields.Datetime.context_timestamp(
                    self.with_context(tz=h.tz), x.date_to).date() >= first_day)
            days_within_period += sum(leaves.filtered(
                lambda x: all((x.date_from.year == date_from.year, x.date_to.year == date_from.year,any((x.date_to.date() <= date_from, x.date_from.date() == date_from))
                               ))).mapped(
                'number_of_days'))
            s_year_date_to_greater = leaves.filtered(
                lambda x: all(
                    (x.date_from.year == date_from.year, x.date_to.year == date_from.year,
                     x.date_to.date() > date_from, x.date_from.date() != date_from)))
            leave_days_diff_year = leaves.filtered(lambda
                                                       x: x.date_from.year != date_from.year and x.date_to.year == date_from.year and x.date_to.date() <= date_from)
            leave_greater_than_date = leaves.filtered(lambda
                                                          x: x.date_from.year != date_from.year and x.date_to.year == date_from.year and x.date_to.date() > date_from)
            if h.wassef_employee_type == 'perm_in_house':
                days_diff_year += sum([(l.date_to.date() - first_day).days + 1 for l in leave_days_diff_year]) if leave_days_diff_year else 0
                l_greater_than_date += sum([(date_from - first_day).days + 1 for l in leave_greater_than_date]) if leave_greater_than_date else 0
                same_year_date_to_greater += sum(
                    [(date_from - l.date_from.date()).days + 1 for l in s_year_date_to_greater]) if s_year_date_to_greater else 0
            elif h.wassef_employee_type == 'perm_staff':
                days_diff_year += sum(
                    [h.resource_calendar_id.get_working_days(first_day, l.date_to.date()) for l in
                     leave_days_diff_year]) if leave_days_diff_year else 0
                l_greater_than_date += sum(
                    [h.resource_calendar_id.get_working_days(first_day, date_from) for l in leave_greater_than_date]) if leave_greater_than_date else 0
                same_year_date_to_greater += sum(
                    [h.resource_calendar_id.get_working_days(date_from, l.date_to.date())for l
                     in
                     s_year_date_to_greater]) if s_year_date_to_greater else 0
            if h.registration_number == '1019':
                print('same_year_date_to_greater', days_within_period,same_year_date_to_greater )
            allocations = self.env['hr.leave.allocation'].search(
                [('employee_id', '=', h.id), ('state', '=', 'validate'), ('holiday_status_id.is_annual', '=', True),
                 ('year', '=', date_from.year), ('allocated_yearly', '!=', True)]).filtered(
                lambda x: first_day <= fields.Datetime.context_timestamp(self.with_context(tz=h.tz),
                                                                         x.create_date).date() <= date_from)

            # ('create_date', '<=', self.from_date.strftime('%Y-%m-%d %H:%M:%S'))])
            # leave_days = sum(leaves.mapped('number_of_days'))
            leave_days += days_within_period + days_diff_year + l_greater_than_date + same_year_date_to_greater
            allocations_days = sum(allocations.mapped('number_of_days'))
            balance = allocations_days - leave_days

            sick_leaves = self._get_sick_leave_details(h)
            sick_leave_days = sick_leaves[0]
            short_s_leave_day = sick_leaves[1]
            long_s_leave_days = sick_leaves[2]
            sick_allocations_days = sick_leaves[3]
            short_sick_allocations_days = sick_leaves[4]
            long_sick_allocations_days = sick_leaves[5]
            sick_balance = sick_leaves[6]
            short_sick_balance = sick_leaves[7]
            long_sick_balance = sick_leaves[8]
            employee_leave_dict["emp_name"] = h.name
            employee_leave_dict["emp_number"] = h.registration_number
            employee_leave_dict["department"] = h.department_id.name if h.department_id else ''
            employee_leave_dict["emp_type"] = "In House" if h.wassef_employee_type == 'perm_in_house' else "Staff"
            employee_leave_dict["emp_join"] = datetime.strptime(h.joining_date.strftime('%Y-%m-%d %H:%M:%S'),
                                                                '%Y-%m-%d %H:%M:%S').strftime(
                '%d-%m-%Y') if h.joining_date else ""
            employee_leave_dict[
                "emp_grad"] = h.payroll_group.name if h.wassef_employee_type == 'perm_in_house' else h.permanent_staff_employee.name
            employee_leave_dict["leave_days"] = leave_days
            employee_leave_dict["sick_leave_days"] = sick_leave_days
            employee_leave_dict["short_sick_leave_days"] = short_s_leave_day
            employee_leave_dict["long_sick_leave_days"] = long_s_leave_days
            employee_leave_dict["allocations_days"] = allocations_days
            employee_leave_dict["sick_allocations_days"] = sick_allocations_days
            employee_leave_dict["short_sick_allocations_days"] = short_sick_allocations_days
            employee_leave_dict["long_sick_allocations_days"] = long_sick_allocations_days
            employee_leave_dict["balance"] = balance
            employee_leave_dict["sick_balance"] = sick_balance
            employee_leave_dict["short_sick_balance"] = short_sick_balance
            employee_leave_dict["long_sick_balance"] = long_sick_balance
            employee_annual_leave_balances.append(employee_leave_dict)
        # print('employee_annual_leave_balances', employee_annual_leave_balances)
        annual_leave = 6
        for line in employee_annual_leave_balances:
            col = 0
            worksheet.write(annual_leave, col, line.get('emp_number'))
            col += 1
            worksheet.write(annual_leave, col, line.get('emp_name'))
            col += 1
            worksheet.write(annual_leave, col, line.get('emp_type'))
            col += 1
            worksheet.write(annual_leave, col, line.get('emp_join'))
            col += 1
            worksheet.write(annual_leave, col, line.get('emp_grad'))
            col += 1
            worksheet.write(annual_leave, col, line.get('leave_days'))
            col += 1
            worksheet.write(annual_leave, col, line.get('allocations_days'))
            col += 1
            worksheet.write(annual_leave, col, line.get('balance'))
            col += 1
            annual_leave += 1
        sick_leave = 6
        for line in employee_annual_leave_balances:
            col1 = 0
            worksheet2.write(sick_leave, col1, line.get('emp_number'))
            col1 += 1
            worksheet2.write(sick_leave, col1, line.get('emp_name'))
            col1 += 1
            worksheet2.write(sick_leave, col1, line.get('emp_type'))
            col1 += 1
            worksheet2.write(sick_leave, col1, line.get('emp_join'))
            col1 += 1
            worksheet2.write(sick_leave, col1, line.get('emp_grad'))
            col1 += 1
            worksheet2.write(sick_leave, col1, line.get('sick_leave_days'))
            col1 += 1
            worksheet2.write(sick_leave, col1, line.get('sick_allocations_days'))
            col1 += 1
            worksheet2.write(sick_leave, col1, line.get('sick_balance'))
            col1 += 1
            sick_leave += 1

        short_sick_leave = 6
        for line in employee_annual_leave_balances:
            col2 = 0
            worksheet3.write(short_sick_leave, col2, line.get('emp_number'))
            col2 += 1
            worksheet3.write(short_sick_leave, col2, line.get('emp_name'))
            col2 += 1
            worksheet3.write(short_sick_leave, col2, line.get('emp_type'))
            col2 += 1
            worksheet3.write(short_sick_leave, col2, line.get('emp_join'))
            col2 += 1
            worksheet3.write(short_sick_leave, col2, line.get('emp_grad'))
            col2 += 1
            worksheet3.write(short_sick_leave, col2, line.get('short_sick_leave_days'))
            col2 += 1
            worksheet3.write(short_sick_leave, col2, line.get('short_sick_allocations_days'))
            col2 += 1
            worksheet3.write(short_sick_leave, col2, line.get('short_sick_balance'))
            col2 += 1
            short_sick_leave += 1

        long_sick_leave = 6
        for line in employee_annual_leave_balances:
            col3 = 0
            worksheet4.write(long_sick_leave, col3, line.get('emp_number'))
            col3 += 1
            worksheet4.write(long_sick_leave, col3, line.get('emp_name'))
            col3 += 1
            worksheet4.write(long_sick_leave, col3, line.get('emp_type'))
            col3 += 1
            worksheet4.write(long_sick_leave, col3, line.get('emp_join'))
            col3 += 1
            worksheet4.write(long_sick_leave, col3, line.get('emp_grad'))
            col3 += 1
            worksheet4.write(long_sick_leave, col3, line.get('long_sick_leave_days'))
            col3 += 1
            worksheet4.write(long_sick_leave, col3, line.get('long_sick_allocations_days'))
            col3 += 1
            worksheet4.write(long_sick_leave, col3, line.get('long_sick_balance'))
            col3 += 1
            long_sick_leave += 1

        fp = io.BytesIO()
        workbook.save(fp)
        return fp.getvalue()

    def get_row_data(self, obj, number):
        registration_number = obj.registration_number
        name = obj.name
        nationality = obj.country_id.name
        sim_card = obj.sim_card
        gender = dict(obj._fields['gender'].selection).get(obj.gender)
        marital = dict(obj._fields['marital'].selection).get(obj.marital)
        work_email = obj.work_email
        qid_doc_number = obj.qid_doc_number
        joining_date = datetime.strftime(obj.joining_date, '%d/%m/%Y') if obj.joining_date else datetime.strftime(
            obj.employee_id.joining_date, '%d/%m/%Y')
        probation_date = datetime.strftime(obj.probation_date, '%d/%m/%Y') if obj.probation_date else ''
        birthday = datetime.strftime(obj.birthday, '%d/%m/%Y') if obj.birthday else ''
        age = obj.age
        profession = obj.profession_id.eng_name
        job_name = obj.job_id.name
        parent_registration_number = obj.parent_id.registration_number
        parent_name = obj.parent_id.name
        if number == 1:
            return [registration_number, name, nationality, sim_card, gender, marital, work_email, qid_doc_number,
                    joining_date, probation_date, birthday, age, profession, job_name, parent_registration_number,
                    parent_name]
        else:
            registration_number = obj.registration_number_previous if obj.registration_number_previous else registration_number
            name = obj.name_previous if obj.name_previous else name
            nationality = obj.country_id_previous.name if obj.country_id_previous else nationality
            gender = dict(obj._fields['gender'].selection).get(obj.gender_previous) if obj.gender_previous else gender
            marital = dict(obj._fields['marital'].selection).get(
                obj.marital_previous) if obj.marital_previous else marital
            job_name = obj.job_id_previous.name if obj.job_id_previous else job_name
            parent_registration_number = obj.parent_id_previous.registration_number if obj.parent_id_previous else parent_registration_number
            parent_name = obj.parent_id_previous.name if obj.parent_id_previous else parent_name
            return [registration_number, name, nationality, sim_card, gender, marital, work_email, qid_doc_number,
                    joining_date, probation_date, birthday, age, profession, job_name, parent_registration_number,
                    parent_name]

    def prepare_sheet_data(self, employees):
        # employee_list = []
        # event_list = []
        # events_size = 0
        employee = {'employee': {}, 'event': {}}
        for rec in employees:
            reg_num = rec.registration_number
            event_ids = self.env['employee.event'].sudo().search(
                [('employee_id', '=', rec.id), ('state', 'in', ['approve']), ('event_type', '=', 'update_employee')],
                order="effective_date desc")
            employee_event = event_ids.filtered(lambda x: x.event_type == 'update_employee')
            contract = self.env['hr.contract'].sudo().search(
                [('employee_id', '=', rec.id), ('state', '!=', 'draft'), ('date_start', '<=', self.from_date)], limit=1,
                order="date_start desc")
            if employee_event:
                employee.get('event').update({f'{reg_num}': {}})
                filter_events = employee_event.filtered(
                    lambda x: x.effective_date <= self.from_date)
                if filter_events:
                    # event_list.append((filter_events[0], 1))
                    employee.get('event').get(f'{reg_num}').update({'event_rec': filter_events[0]})
                    if contract:
                        employee.get('event').get(f'{reg_num}').update({'contract': contract})
                else:
                    employee.get('event').get(f'{reg_num}').update({'event_rec_p': employee_event[-1]})
                    if contract:
                        employee.get('event').get(f'{reg_num}').update({'contract': contract})
            else:
                # employee_list.append(rec.id)
                employee.get('employee').update({f'{reg_num}': {'rec': rec}})
                if contract:
                    employee.get('employee').get(f'{reg_num}').update({'contract': contract})
        print('employee_dict', employee)
        return employee

    def get_employees(self, in_house, staff, temp):
        if all((in_house, staff, temp)) or all((not in_house, not staff, not temp)):
            employee_ids = self.env['hr.employee'].sudo().search([('joining_date', '<=', self.from_date)])
            return self.prepare_sheet_data(employee_ids)
        elif in_house and staff:
            employee_ids = self.env['hr.employee'].sudo().search([('joining_date', '<=', self.from_date),
                                                                  ('wassef_employee_type', 'in',
                                                                   ['perm_in_house', 'perm_staff'])])
            return self.prepare_sheet_data(employee_ids)
        elif in_house and temp:
            employee_ids = self.env['hr.employee'].sudo().search([('joining_date', '<=', self.from_date),
                                                                  ('wassef_employee_type', 'in', ['perm_in_house', 'temp'])])
            return self.prepare_sheet_data(employee_ids)
        elif staff and temp:
            employee_ids = self.env['hr.employee'].sudo().search([('joining_date', '<=', self.from_date),
                                                                  ('wassef_employee_type', 'in', ['perm_staff', 'temp'])])
            return self.prepare_sheet_data(employee_ids)
        elif in_house:
            employee_ids = self.env['hr.employee'].sudo().search(
                [('wassef_employee_type', '=', 'perm_in_house'), ('joining_date', '<=', self.from_date)])
            return self.prepare_sheet_data(employee_ids)
        elif staff:
            employee_ids = self.env['hr.employee'].sudo().search(
                [('wassef_employee_type', '=', 'perm_staff'), ('joining_date', '<=', self.from_date)])
            return self.prepare_sheet_data(employee_ids)
        elif temp:
            employee_ids = self.env['hr.employee'].sudo().search(
                [('wassef_employee_type', '=', 'temp'), ('joining_date', '<=', self.from_date)])
            return self.prepare_sheet_data(employee_ids)

    def export_employee_info_as_date_report(self):
        employee_list = []
        event_list = []
        include_in_house = self.in_house_employee
        include_staff = self.staff_employee
        include_temporary = self.temporary_employee
        employees = self.get_employees(include_in_house, include_staff, include_temporary)
        # event_list.extend(employees[0])
        # employee_list.extend(employees[1])
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Employee Information Report', cell_overwrite_ok=True)

        style_company = easyxf(
            # 'font: name Arial;'
            'alignment: horizontal center, vertical center,wrap yes ;'
            'font:bold True,height 200;'
        )
        style_header = easyxf(
            'font: name Arial;'
            'alignment: horizontal center, vertical center,wrap yes ;'
            'font:bold True, height 200; '
            'borders:left thin, right thin, top thin, bottom thin;'
        )
        style_record = easyxf(
            'font: name Arial;'
            'alignment: horizontal center, vertical center,wrap yes ;'
            'borders:left thin, right thin, top thin, bottom thin;'
        )
        col_size = range(0, 44)
        for width in col_size:
            worksheet.col(width).width = 300 * 30

        row = 0
        worksheet.write_merge(row, row, 0, 3, 'Employee Information Report', style_company)
        row += 3

        header_str = [
            'Emp No', 'Emp Name', 'Emp Status', 'Nationality', 'Mobile', 'Gender', 'Marital Status',
            'Email Address', 'National Identifier', 'Hire Date', 'Probation Date', 'Emp Dob', 'Age',
            'Grade', 'Pos', 'Job', 'Payroll', 'Org', 'Location', 'Qualification Type',
            'Qualification Title', 'Experience', 'Supervisor No', 'Supervisor', 'Basic', 'Social', 'Housing',
            'Transportation', 'Telephone', 'Other', 'Total'
        ]
        column = 0
        for rec in header_str:
            worksheet.write(row, column, rec, style_header)
            column += 1

        row += 1

        # for event in event_list:
        for k, v in employees.items():
            if k == 'event':
                for v in v.values():
                    column = 0
                    event_id = v.get('event_rec') if v.get('event_rec') else v.get('event_rec_p')
                    number = 1 if v.get('event_rec') else 0
                    # event_id = event[0]
                    # emp_id = event_id.employee_id.id
                    registration_number, name, nationality, sim_card, gender, marital, work_email, qid_doc_number, joining_date, \
                        probation_date, birthday, age, profession, job_name, parent_registration_number, parent_name = self.get_row_data(
                        event_id, number)

                    worksheet.write(row, column, registration_number if registration_number else '', style_record)
                    column += 1
                    worksheet.write(row, column, name if name else '', style_record)
                    column += 1
                    worksheet.write(row, column, 'Active Assignment', style_record)
                    column += 1
                    worksheet.write(row, column, nationality if nationality else '', style_record)
                    column += 1
                    worksheet.write(row, column, sim_card if event_id.employee_id.sim_card else '', style_record)
                    column += 1
                    worksheet.write(row, column, gender if gender else '', style_record)
                    column += 1
                    worksheet.write(row, column, marital if marital else '', style_record)
                    column += 1
                    worksheet.write(row, column, work_email if work_email else '', style_record)
                    column += 1
                    print('column', column)
                    worksheet.write(row, column, qid_doc_number if qid_doc_number else '', style_record)
                    column += 1
                    worksheet.write(row, column, joining_date, style_record)
                    column += 1
                    worksheet.write(row, column, probation_date, style_record)
                    column += 1
                    worksheet.write(row, column, birthday, style_record)
                    column += 1
                    worksheet.write(row, column, age if age else '', style_record)
                    column += 1
                    contract = v.get('contract')
                    if contract and contract.wassef_employee_type == 'perm_in_house':
                        worksheet.write(row, column,
                                        contract.payroll_group.name if contract.payroll_group else '',
                                        style_record)
                        column += 1
                    elif contract and contract.wassef_employee_type == 'perm_staff':
                        worksheet.write(row, column,
                                        contract.permanent_staff_employee.name if contract.permanent_staff_employee else '',
                                        style_record)
                        column += 1
                    else:
                        worksheet.write(row, column, '', style_record)
                        column += 1

                    worksheet.write(row, column, profession if profession else '', style_record)
                    column += 1
                    worksheet.write(row, column, job_name if job_name else '', style_record)
                    column += 1
                    worksheet.write(row, column,
                                    contract.structure_type_id.name if contract and contract.structure_type_id else ''
                                    , style_record)
                    column += 1
                    worksheet.write(row, column, '', style_record)
                    column += 1
                    worksheet.write(row, column, 'Waseef', style_record)
                    column += 1

                    res = event_id.employee_id.certificate_ids.filtered(lambda m: m.graduation_year).sorted(
                        key=lambda r: r.graduation_year)
                    if len(res) > 0:
                        worksheet.write(row, column,
                                        dict(event_id.employee_id.certificate_ids._fields[
                                                 'qualification_type'].selection).get(
                                            res[-1].qualification_type) if res[-1] else '',
                                        style_record)
                        column += 1
                    else:
                        worksheet.write(row, column, '', style_record)
                        column += 1

                    worksheet.write(row, column,
                                    event_id.employee_id.qualification_title if event_id.employee_id else '',
                                    style_record)
                    column += 1
                    worksheet.write(row, column,
                                    event_id.employee_id.number_of_years_work if event_id.employee_id else '',
                                    style_record)
                    column += 1
                    worksheet.write(row, column, parent_registration_number if parent_registration_number else '',
                                    style_record)
                    column += 1
                    worksheet.write(row, column, parent_name if parent_name else '', style_record)
                    column += 1
                    wage = contract.wage if contract and contract.wage else 0
                    worksheet.write(row, column, wage, style_record)
                    column += 1
                    social_allowance = contract.social_allowance_for_permanent_staff if contract and contract.wassef_employee_type == 'perm_staff' else 0
                    worksheet.write(row, column, social_allowance, style_record)
                    column += 1
                    accommodation = contract.accommodation if contract and contract.accommodation else 0
                    worksheet.write(row, column, accommodation, style_record)
                    column += 1
                    transport_allowance = contract.transport_allowance if contract and contract.transport_allowance else 0
                    worksheet.write(row, column, transport_allowance, style_record)
                    column += 1
                    mobile_allowance = contract.mobile_allowance if contract and contract.mobile_allowance else 0
                    worksheet.write(row, column, mobile_allowance, style_record)
                    column += 1
                    other_allowance = contract.other_allowance if contract and contract.other_allowance else 0
                    worksheet.write(row, column, other_allowance, style_record)
                    column += 1
                    total = wage + social_allowance + transport_allowance + accommodation + mobile_allowance + other_allowance
                    worksheet.write(row, column, total, style_record)
                    column += 1
                    row += 1
            elif k == 'employee':
                for v in v.values():
                    column = 0
                    employee = v.get('rec')
                    contracts = v.get('contract')
                    worksheet.write(row, column, employee.registration_number if employee.registration_number else '',
                                    style_record)
                    column += 1
                    worksheet.write(row, column, employee.name if employee.name else '', style_record)
                    column += 1
                    worksheet.write(row, column, 'Active Assignment', style_record)
                    column += 1
                    worksheet.write(row, column, employee.country_id.name if employee.country_id else '', style_record)
                    column += 1
                    worksheet.write(row, column, employee.sim_card if employee.sim_card else '', style_record)
                    column += 1
                    worksheet.write(row, column,
                                    dict(employee._fields['gender'].selection).get(
                                        employee.gender) if employee.gender else '',
                                    style_record)
                    column += 1
                    worksheet.write(row, column, dict(employee._fields['marital'].selection).get(
                        employee.marital) if employee.marital else '', style_record)
                    column += 1
                    worksheet.write(row, column, employee.work_email if employee.work_email else '', style_record)
                    column += 1
                    worksheet.write(row, column, employee.qid_doc_number if employee.qid_doc_number else '',
                                    style_record)
                    column += 1
                    joining_date = datetime.strftime(employee.joining_date, '%d/%m/%Y') if employee.joining_date else ''
                    worksheet.write(row, column, joining_date, style_record)
                    column += 1
                    probation_date = datetime.strftime(employee.probation_date,
                                                       '%d/%m/%Y') if employee.probation_date else ''
                    worksheet.write(row, column, probation_date, style_record)
                    column += 1
                    birthday = datetime.strftime(employee.birthday, '%d/%m/%Y') if employee.birthday else ''
                    worksheet.write(row, column, birthday, style_record)
                    column += 1
                    worksheet.write(row, column, employee.age if employee.age else '', style_record)
                    column += 1
                    if contracts:
                        if contracts.wassef_employee_type == 'perm_in_house':
                            worksheet.write(row, column,
                                            contracts.payroll_group.name if contracts.payroll_group else '',
                                            style_record)
                            column += 1
                        elif contracts.wassef_employee_type == 'perm_staff':
                            worksheet.write(row, column,
                                            contracts.permanent_staff_employee.name if contracts.permanent_staff_employee else '',
                                            style_record)
                            column += 1
                        else:
                            worksheet.write(row, column, '', style_record)
                            column += 1
                    else:
                        if employee.wassef_employee_type == 'perm_in_house' and employee.payroll_group:
                            worksheet.write(row, column, employee.payroll_group.name, style_record)
                            column += 1
                        elif employee.wassef_employee_type == 'perm_staff' and employee.permanent_staff_employee:
                            worksheet.write(row, column, employee.permanent_staff_employee.name, style_record)
                            column += 1
                        else:
                            worksheet.write(row, column, '', style_record)
                            column += 1

                    worksheet.write(row, column, employee.profession_id.eng_name if employee.profession_id else '',
                                    style_record)
                    column += 1
                    worksheet.write(row, column, employee.job_id.name if employee.job_id else '', style_record)
                    column += 1
                    worksheet.write(row, column,
                                    contracts.structure_type_id.name if contracts and contracts.structure_type_id else '',
                                    style_record)
                    column += 1
                    worksheet.write(row, column, '', style_record)
                    column += 1
                    worksheet.write(row, column, 'Waseef', style_record)
                    column += 1

                    res = employee.certificate_ids.filtered(lambda m: m.graduation_year).sorted(
                        key=lambda r: r.graduation_year)
                    if len(res) > 0:
                        worksheet.write(row, column,
                                        dict(employee.certificate_ids._fields['qualification_type'].selection).get(
                                            res[-1].qualification_type) if res[-1] else '',
                                        style_record)
                        column += 1
                    else:
                        worksheet.write(row, column, '', style_record)
                        column += 1

                    worksheet.write(row, column, employee.qualification_title if employee.qualification_title else '',
                                    style_record)
                    column += 1
                    worksheet.write(row, column, employee.number_of_years_work if employee.number_of_years_work else '',
                                    style_record)
                    column += 1
                    worksheet.write(row, column, employee.parent_id.registration_number if employee.parent_id else '',
                                    style_record)
                    column += 1
                    worksheet.write(row, column, employee.parent_id.name if employee.parent_id else '', style_record)
                    column += 1

                    worksheet.write(row, column, contracts.wage if contracts and contracts.wage else '', style_record)
                    column += 1
                    worksheet.write(row, column,
                                    contracts.social_allowance_for_permanent_staff if contracts and contracts.wassef_employee_type == 'perm_staff' and contracts.social_allowance_for_permanent_staff else '',
                                    style_record)
                    column += 1
                    worksheet.write(row, column,
                                    contracts.accommodation if contracts and contracts.accommodation else '',
                                    style_record)
                    column += 1
                    worksheet.write(row, column,
                                    contracts.transport_allowance if contracts and contracts.transport_allowance else '',
                                    style_record)
                    column += 1
                    worksheet.write(row, column,
                                    contracts.mobile_allowance if contracts and contracts.mobile_allowance else '',
                                    style_record)
                    column += 1
                    worksheet.write(row, column,
                                    contracts.other_allowance if contracts and contracts.other_allowance else '',
                                    style_record)
                    column += 1
                    total = (contracts.wage + contracts.social_allowance_for_permanent_staff + \
                             contracts.transport_allowance + contracts.accommodation + contracts.mobile_allowance + contracts.other_allowance) if contracts else 0
                    worksheet.write(row, column, total, style_record)
                    column += 1

                    row += 1

                    # ------------------------------ -------- --------------------

        fp = io.BytesIO()
        workbook.save(fp)
        return fp.getvalue()

    def export_end_employee_info_report(self):
        domain = []
        if self.from_date and not self.to_date:
            domain.append(('termination_date', '>=', datetime.strftime(self.from_date, "%Y-%m-%d %H:%m:%S")))
            domain.append(('termination_date', '<=', datetime.strftime(datetime.today(), "%Y-%m-%d %H:%m:%S")))
        elif self.to_date and not self.from_date:
            domain.append(('termination_date', '<=', datetime.strftime(self.to_date, "%Y-%m-%d %H:%m:%S")))
        elif self.from_date and self.to_date:
            domain.append(('termination_date', '>=', datetime.strftime(self.from_date, "%Y-%m-%d %H:%m:%S")))
            domain.append(('termination_date', '<=', datetime.strftime(self.to_date, "%Y-%m-%d %H:%m:%S")))

        if self.in_house_employee:
            domain.append(('wassef_employee_type', '=', 'perm_in_house'))

        if self.staff_employee:
            domain.append(('wassef_employee_type', '=', 'perm_staff'))

        if self.temporary_employee:
            domain.append(('wassef_employee_type', '=', 'temp'))

        active_domain = ['|', ('active', '=', True), ('active', '=', False)]
        if self.from_date or self.to_date:
            domain = domain + active_domain
            employee_list = self.env['hr.employee'].sudo().search(domain).ids
        else:
            domain = domain + [('active', '=', False)]
            employee_list = self.env['hr.employee'].sudo().search(domain).ids

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Employee Information Report', cell_overwrite_ok=True)

        style_company = easyxf(
            # 'font: name Arial;'
            'alignment: horizontal center, vertical center,wrap yes ;'
            'font:bold True,height 200;'
        )
        style_header = easyxf(
            'font: name Arial;'
            'alignment: horizontal center, vertical center,wrap yes ;'
            'font:bold True, height 200; '
            'borders:left thin, right thin, top thin, bottom thin;'
        )
        style_record = easyxf(
            'font: name Arial;'
            'alignment: horizontal center, vertical center,wrap yes ;'
            'borders:left thin, right thin, top thin, bottom thin;'
        )
        col_size = range(0, 44)
        for width in col_size:
            worksheet.col(width).width = 300 * 30

        row = 0
        worksheet.write_merge(row, row, 0, 3, 'WASEEF END EMPLOYEE INFORMATION REPORT', style_company)
        row += 3

        header_str = [
            'Emp No', 'Emp Name', 'Nation', 'Grade', 'Position', 'Payroll', 'Start Date', 'Termination Date', 'Reason'
        ]
        column = 0
        for rec in header_str:
            worksheet.write(row, column, rec, style_header)
            column += 1

        row += 1
        for emp in employee_list:
            column = 0
            employee = self.env['hr.employee'].sudo().browse(emp)
            contracts = self.env['hr.contract'].sudo().search(
                [('state', '=', 'open'), ('employee_id', '=', employee.id)], limit=1, order="id asc")
            worksheet.write(row, column, employee.registration_number if employee.registration_number else '',
                            style_record)
            column += 1
            worksheet.write(row, column, employee.name if employee.name else '', style_record)
            column += 1
            worksheet.write(row, column, employee.country_id.name if employee.country_id else '', style_record)
            column += 1

            if employee.wassef_employee_type == 'perm_in_house' and employee.payroll_group:
                worksheet.write(row, column, employee.payroll_group.name, style_record)
                column += 1
            elif employee.wassef_employee_type == 'perm_staff' and employee.permanent_staff_employee:
                worksheet.write(row, column, employee.permanent_staff_employee.name, style_record)
                column += 1
            else:
                worksheet.write(row, column, '', style_record)
                column += 1

            worksheet.write(row, column, employee.job_id.name if employee.job_id else '', style_record)
            column += 1
            worksheet.write(row, column, contracts.structure_type_id.name if contracts.structure_type_id else ''
                            , style_record)
            column += 1
            joining_date = datetime.strftime(employee.joining_date, '%d/%m/%Y') if employee.joining_date else ''
            worksheet.write(row, column, joining_date, style_record)
            column += 1
            termination_date = datetime.strftime(employee.termination_date,
                                                 '%d/%m/%Y') if employee.termination_date else ''
            worksheet.write(row, column, termination_date, style_record)
            column += 1
            worksheet.write(row, column, employee.reason if employee.reason else '', style_record)
            column += 1
            row += 1

        fp = io.BytesIO()
        workbook.save(fp)
        return fp.getvalue()

    def export_employee_info_report(self):

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Employee Information Report', cell_overwrite_ok=True)

        style_company = easyxf(
            # 'font: name Arial;'
            'alignment: horizontal center, vertical center,wrap yes ;'
            'font:bold True,height 200;'
        )
        style_header = easyxf(
            'font: name Arial;'
            'alignment: horizontal center, vertical center,wrap yes ;'
            'font:bold True, height 200; '
            'borders:left thin, right thin, top thin, bottom thin;'
        )
        style_record = easyxf(
            'font: name Arial;'
            'alignment: horizontal center, vertical center,wrap yes ;'
            'borders:left thin, right thin, top thin, bottom thin;'
        )
        col_size = range(0, 44)
        for width in col_size:
            worksheet.col(width).width = 300 * 30

        row = 0
        worksheet.write_merge(row, row, 0, 6, 'Employee Information Report', style_company)
        row += 3

        header_str = [
            'Employee Number', 'Emp Name', 'Emp Status', 'Nationality', 'Mobile', 'Gender', 'Marital Status',
            'Email Address', 'National Identifier', 'Passport No', 'Hire Date', 'Probation Date', 'Emp Dob', 'Age',
            'Grade', 'Profession', 'Pos', 'Job', 'Payroll', 'Org', 'Location', 'Qualification Type',
            'Qualification Title', 'Experience', 'Supervisor No', 'Supervisor', 'Bank Name', 'Account Number', 'Basic',
            'Social', 'Housing', 'Transportation', 'Telephone', 'Other', 'Total'
        ]
        column = 0
        for rec in header_str:
            worksheet.write(row, column, rec, style_header)
            column += 1

        # ------------------------------ Emp details --------------------

        employee_list = []
        in_house = self.in_house_employee
        staff = self.staff_employee
        temp = self.temporary_employee
        if all((in_house, staff, temp)) or all((not in_house, not staff, not temp)):
            employee_ids = self.env['hr.employee'].sudo().search([])
            for rec in employee_ids:
                employee_list.append(rec.id)

        elif in_house and staff:
            employee_ids = self.env['hr.employee'].sudo().search([('wassef_employee_type', 'in',
                                                                   ['perm_in_house', 'perm_staff'])])
            for rec in employee_ids:
                employee_list.append(rec.id)
        elif in_house and temp:
            employee_ids = self.env['hr.employee'].sudo().search([('wassef_employee_type', 'in', ['perm_in_house', 'temp'])])
            for rec in employee_ids:
                employee_list.append(rec.id)
        elif staff and temp:
            employee_ids = self.env['hr.employee'].sudo().search([('wassef_employee_type', 'in', ['perm_staff', 'temp'])])
            for rec in employee_ids:
                employee_list.append(rec.id)
        elif in_house:
            employee_ids = self.env['hr.employee'].sudo().search([('wassef_employee_type', '=', 'perm_in_house')])
            for rec in employee_ids:
                employee_list.append(rec.id)
        elif staff:
            employee_ids = self.env['hr.employee'].sudo().search([('wassef_employee_type', '=', 'perm_staff')])
            for rec in employee_ids:
                employee_list.append(rec.id)
        elif temp:
            employee_ids = self.env['hr.employee'].sudo().search([('wassef_employee_type', '=', 'temp')])
            for rec in employee_ids:
                employee_list.append(rec.id)

        row += 1
        for emp in employee_list:
            column = 0
            employee = self.env['hr.employee'].sudo().browse(emp)
            contracts = self.env['hr.contract'].sudo().search(
                [('state', '=', 'open'), ('employee_id', '=', employee.id)], limit=1, order="id asc")
            worksheet.write(row, column, employee.registration_number if employee.registration_number else '',
                            style_record)
            column += 1
            worksheet.write(row, column, employee.name if employee.name else '', style_record)
            column += 1
            worksheet.write(row, column, 'Active Assignment', style_record)
            column += 1
            worksheet.write(row, column, employee.country_id.name if employee.country_id else '', style_record)
            column += 1
            worksheet.write(row, column, employee.sim_card if employee.sim_card else '', style_record)
            column += 1
            worksheet.write(row, column,
                            dict(employee._fields['gender'].selection).get(employee.gender) if employee.gender else '',
                            style_record)
            column += 1
            worksheet.write(row, column, dict(employee._fields['marital'].selection).get(
                employee.marital) if employee.marital else '', style_record)
            column += 1
            worksheet.write(row, column, employee.work_email if employee.work_email else '', style_record)
            column += 1
            worksheet.write(row, column, employee.qid_doc_number if employee.qid_doc_number else '', style_record)
            column += 1
            worksheet.write(row, column, employee.passport_doc_number if employee.passport_doc_number else '',
                            style_record)
            column += 1
            joining_date = datetime.strftime(employee.joining_date, '%d/%m/%Y') if employee.joining_date else ''
            worksheet.write(row, column, joining_date, style_record)
            column += 1
            probation_date = datetime.strftime(employee.probation_date, '%d/%m/%Y') if employee.probation_date else ''
            worksheet.write(row, column, probation_date, style_record)
            column += 1
            birthday = datetime.strftime(employee.birthday, '%d/%m/%Y') if employee.birthday else ''
            worksheet.write(row, column, birthday, style_record)
            column += 1
            worksheet.write(row, column, employee.age if employee.age else '', style_record)
            column += 1

            if employee.wassef_employee_type == 'perm_in_house' and employee.payroll_group:
                worksheet.write(row, column, employee.payroll_group.name, style_record)
                column += 1
            elif employee.wassef_employee_type == 'perm_staff' and employee.permanent_staff_employee:
                worksheet.write(row, column, employee.permanent_staff_employee.name, style_record)
                column += 1
            else:
                worksheet.write(row, column, '', style_record)
                column += 1

            worksheet.write(row, column, employee.profession_id.eng_name if employee.profession_id else '',
                            style_record)
            column += 1
            worksheet.write(row, column, employee.job_id.name if employee.job_id else '', style_record)
            column += 1
            worksheet.write(row, column, employee.job_id.name if employee.job_id else '', style_record)
            column += 1
            worksheet.write(row, column, contracts.structure_type_id.name if contracts.structure_type_id else '',
                            style_record)
            column += 1
            worksheet.write(row, column, '', style_record)
            column += 1
            worksheet.write(row, column, 'Waseef', style_record)
            column += 1

            res = employee.certificate_ids.filtered(lambda m: m.graduation_year).sorted(key=lambda r: r.graduation_year)
            if len(res) > 0:
                worksheet.write(row, column, dict(employee.certificate_ids._fields['qualification_type'].selection).get(
                    res[-1].qualification_type) if res[-1] else '',
                                style_record)
                column += 1
            else:
                worksheet.write(row, column, '', style_record)
                column += 1

            worksheet.write(row, column, employee.qualification_title if employee.qualification_title else '',
                            style_record)
            column += 1
            worksheet.write(row, column, employee.number_of_years_work if employee.number_of_years_work else '',
                            style_record)
            column += 1
            worksheet.write(row, column, employee.parent_id.registration_number if employee.parent_id else '',
                            style_record)
            column += 1
            worksheet.write(row, column, employee.parent_id.name if employee.parent_id else '', style_record)
            column += 1
            worksheet.write(row, column, employee.bank_name if employee.bank_name else '', style_record)
            column += 1
            worksheet.write(row, column,
                            employee.bank_account_id.acc_number if employee.bank_account_id.acc_number else '',
                            style_record)
            column += 1
            worksheet.write(row, column, contracts.wage if contracts.wage else '', style_record)
            column += 1
            worksheet.write(row, column,
                            contracts.social_allowance_for_permanent_staff if contracts.wassef_employee_type == 'perm_staff' and contracts.social_allowance_for_permanent_staff else '',
                            style_record)
            column += 1
            worksheet.write(row, column, contracts.accommodation if contracts.accommodation else '', style_record)
            column += 1
            worksheet.write(row, column, contracts.transport_allowance if contracts.transport_allowance else '',
                            style_record)
            column += 1
            worksheet.write(row, column, contracts.mobile_allowance if contracts.mobile_allowance else '', style_record)
            column += 1
            worksheet.write(row, column, contracts.other_allowance if contracts.other_allowance else '', style_record)
            column += 1
            total = contracts.wage + contracts.social_allowance_for_permanent_staff + contracts.transport_allowance + contracts.accommodation + contracts.mobile_allowance + contracts.other_allowance
            worksheet.write(row, column, total, style_record)
            column += 1

            row += 1

        # ------------------------------ -------- --------------------
        fp = io.BytesIO()
        workbook.save(fp)
        return fp.getvalue()

    def export_employee_info_arabic_report(self):
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Employee Information Report', cell_overwrite_ok=True)

        style_company = easyxf(
            # 'font: name Arial;'
            'alignment: horizontal center, vertical center,wrap yes ;'
            'font:bold True,height 200;'
        )
        style_header = easyxf(
            'font: name Arial;'
            'alignment: horizontal center, vertical center,wrap yes ;'
            'font:bold True, height 200; '
            'borders:left thin, right thin, top thin, bottom thin;'
        )
        style_record = easyxf(
            'font: name Arial;'
            'alignment: horizontal center, vertical center,wrap yes ;'
            'borders:left thin, right thin, top thin, bottom thin;'
        )
        col_size = range(0, 44)
        for width in col_size:
            worksheet.col(width).width = 300 * 30
        # col_height = range(0, 500)
        # for height in col_height:
        #     worksheet.row(height).height = 256 * 2

        row = 0
        worksheet.write_merge(row, row, 0, 6, 'Employee Information Report', style_company)
        row += 3

        header_str = [
            'Employee Number', 'Emp Name', 'Emp Status', 'Nationality', 'Mobile', 'Gender', 'Marital Status',
            'Email Address', 'National Identifier', 'Passport No', 'Hire Date', 'Probation Date', 'Emp Dob', 'Age',
            'Grade', 'Profession', 'Pos', 'Job', 'Payroll', 'Org', 'Qualification Type', 'Qualification Title',
            'Experience', 'Supervisor', 'Bank Name', 'Account Number', 'Basic', 'Social', 'Housing',
            'Transportation', 'Telephone', 'Other', 'Total'
        ]
        a = ['Location', 'Supervisor No', ]
        column = 0
        for rec in header_str:
            worksheet.write(row, column, rec, style_header)
            column += 1

        # ------------------------------ Emp details --------------------

        employee_list = []
        if self.in_house_employee:
            employee_ids = self.env['hr.employee'].sudo().search(
                [('wassef_employee_type', '=', 'perm_in_house'), ('joining_date', '<=', self.date.today())])
            for rec in employee_ids:
                employee_list.append(rec.id)

        if self.staff_employee:
            employee_ids = self.env['hr.employee'].sudo().search(
                [('wassef_employee_type', '=', 'perm_staff'), ('joining_date', '<=', self.date.today())])
            for rec in employee_ids:
                employee_list.append(rec.id)

        if self.temporary_employee:
            employee_ids = self.env['hr.employee'].sudo().search(
                [('wassef_employee_type', '=', 'temp'), ('joining_date', '<=', self.date.today())])
            for rec in employee_ids:
                employee_list.append(rec.id)

        if not self.in_house_employee and not self.staff_employee and not self.temporary_employee:
            employee_ids = self.env['hr.employee'].sudo().search([('joining_date', '<=', self.date.today())])
            for rec in employee_ids:
                employee_list.append(rec.id)
        row += 1
        for emp in employee_list:
            column = 0
            employee = self.env['hr.employee'].sudo().browse(emp)
            contracts = self.env['hr.contract'].sudo().search(
                [('state', '=', 'open'), ('employee_id', '=', employee.id)], limit=1, order="id asc")
            worksheet.write(row, column, employee.registration_number if employee.registration_number else '',
                            style_record)
            column += 1
            worksheet.write(row, column,
                            employee.employee_name_in_arabic if employee.employee_name_in_arabic else employee.name,
                            style_record)
            column += 1
            worksheet.write(row, column, 'تعيين نشط', style_record)
            column += 1
            worksheet.write(row, column, employee.country_id.name if employee.country_id else '', style_record)
            column += 1
            worksheet.write(row, column, employee.sim_card if employee.sim_card else '', style_record)
            column += 1
            worksheet.write(row, column,
                            dict(employee._fields['gender'].selection).get(employee.gender) if employee.gender else '',
                            style_record)
            column += 1
            worksheet.write(row, column, dict(employee._fields['marital'].selection).get(
                employee.marital) if employee.marital else '', style_record)
            column += 1
            worksheet.write(row, column, employee.work_email if employee.work_email else '', style_record)
            column += 1
            worksheet.write(row, column, employee.qid_doc_number if employee.qid_doc_number else '', style_record)
            column += 1
            worksheet.write(row, column, employee.passport_doc_number if employee.passport_doc_number else '',
                            style_record)
            column += 1
            joining_date = datetime.strftime(employee.joining_date, '%d/%m/%Y') if employee.joining_date else ''
            worksheet.write(row, column, joining_date, style_record)
            column += 1
            probation_date = datetime.strftime(employee.probation_date, '%d/%m/%Y') if employee.probation_date else ''
            worksheet.write(row, column, probation_date, style_record)
            column += 1
            birthday = datetime.strftime(employee.birthday, '%d/%m/%Y') if employee.birthday else ''
            worksheet.write(row, column, birthday, style_record)
            column += 1
            worksheet.write(row, column, employee.age if employee.age else '', style_record)
            column += 1

            if employee.wassef_employee_type == 'perm_in_house' and employee.payroll_group:
                worksheet.write(row, column, employee.payroll_group.name, style_record)
                column += 1
            elif employee.wassef_employee_type == 'perm_staff' and employee.permanent_staff_employee:
                worksheet.write(row, column, employee.permanent_staff_employee.name, style_record)
                column += 1
            else:
                worksheet.write(row, column, '', style_record)
                column += 1

            if employee.profession_id:
                worksheet.write(row, column,
                                employee.profession_id.arabic_name if employee.profession_id.arabic_name else employee.profession_id.eng_name,
                                style_record)
                column += 1
            else:
                worksheet.write(row, column, '', style_record)
                column += 1

            if employee.job_id:
                worksheet.write(row, column,
                                employee.job_id.job_arabic_name if employee.job_id.job_arabic_name else employee.job_id.name,
                                style_record)
                column += 1
            else:
                worksheet.write(row, column, '', style_record)
                column += 1

            if employee.job_id:
                worksheet.write(row, column,
                                employee.job_id.job_arabic_name if employee.job_id.job_arabic_name else employee.job_id.name,
                                style_record)
                column += 1
            else:
                worksheet.write(row, column, '', style_record)
                column += 1
            worksheet.write(row, column, contracts.structure_type_id.name if contracts.structure_type_id else '',
                            style_record)
            column += 1
            worksheet.write(row, column, '', style_record)
            column += 1

            res = employee.certificate_ids.filtered(lambda m: m.graduation_year).sorted(key=lambda r: r.graduation_year)
            if len(res) > 0:
                worksheet.write(row, column, dict(employee.certificate_ids._fields['qualification_type'].selection).get(
                    res[-1].qualification_type) if res[-1] else '',
                                style_record)
                column += 1
            else:
                worksheet.write(row, column, '', style_record)
                column += 1

            if len(res) > 0:
                worksheet.write(row, column, res[-1].arabic_name if res[-1] else res[-1].name,
                                style_record)
                column += 1
            else:
                worksheet.write(row, column, employee.qualification_title if employee.qualification_title else '',
                                style_record)
                column += 1
            worksheet.write(row, column, employee.number_of_years_work if employee.number_of_years_work else '',
                            style_record)
            column += 1
            worksheet.write(row, column, employee.parent_id.employee_name_in_arabic if employee.parent_id else '',
                            style_record)
            column += 1
            worksheet.write(row, column, employee.bank_name if employee.bank_name else '', style_record)
            column += 1
            worksheet.write(row, column,
                            employee.bank_account_id.acc_number if employee.bank_account_id.acc_number else '',
                            style_record)
            column += 1

            worksheet.write(row, column, contracts.wage if contracts.wage else '', style_record)
            column += 1
            worksheet.write(row, column,
                            contracts.social_allowance_for_permanent_staff if contracts.wassef_employee_type == 'perm_staff' and contracts.social_allowance_for_permanent_staff else '',
                            style_record)
            column += 1
            worksheet.write(row, column, contracts.accommodation if contracts.accommodation else '', style_record)
            column += 1
            worksheet.write(row, column, contracts.transport_allowance if contracts.transport_allowance else '',
                            style_record)
            column += 1
            worksheet.write(row, column, contracts.mobile_allowance if contracts.mobile_allowance else '', style_record)
            column += 1
            worksheet.write(row, column, contracts.other_allowance if contracts.other_allowance else '', style_record)
            column += 1
            total = contracts.wage + contracts.social_allowance_for_permanent_staff + contracts.transport_allowance + contracts.accommodation + contracts.mobile_allowance + contracts.other_allowance
            worksheet.write(row, column, total, style_record)
            column += 1

            row += 1

        # ------------------------------ -------- --------------------

        fp = io.BytesIO()
        workbook.save(fp)
        return fp.getvalue()
