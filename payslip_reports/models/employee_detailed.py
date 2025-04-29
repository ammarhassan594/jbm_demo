from datetime import datetime

import base64
import io
import os

from odoo import models, _
from odoo.exceptions import ValidationError


class PartnerXlsx(models.AbstractModel):
    _name = 'report.payslip_reports.employees_detailed'
    _inherit = 'report.report_xlsx.abstract'

    def _get_arabic_date(self, payslip):
        month = datetime.strftime(datetime.strptime(str(payslip.date_from), "%Y-%m-%d"), "%m")
        year = datetime.strftime(datetime.strptime(str(payslip.date_from), "%Y-%m-%d"), "%Y")
        month_name = ''
        if month == '01':
            month_name = "يناير"
        elif month == '02':
            month_name = "فبراير"
        elif month == '03':
            month_name = "مارس"
        elif month == '04':
            month_name = "أبريل"
        elif month == '05':
            month_name = "مايو"
        elif month == '06':
            month_name = "يونيو"
        elif month == '07':
            month_name = "يوليو"
        elif month == '08':
            month_name = "أغسطس"
        elif month == '09':
            month_name = "سبتمبر"
        elif month == '10':
            month_name = "أكتوبر"
        elif month == '11':
            month_name = "نوفمبر"
        elif month == '12':
            month_name = "ديسمبر"
        return {
            'month_name': month_name,
            'year': year,
        }

    def non_collaborator_employees_report(self, payslip, workbook):

        report_name = payslip.employee_id.name

        # One sheet by payslip
        sheet = workbook.add_worksheet(report_name)

        head = workbook.add_format({'align': 'center', 'bold': True, 'size': 16})
        header = workbook.add_format({'align': 'right', 'bold': True, 'size': 14, })
        cell_bold = workbook.add_format({'align': 'center', 'bold': True, 'size': 14, })
        cell = workbook.add_format({'align': 'right', 'size': 14})
        border_cell = workbook.add_format({'align': 'right', 'size': 14, 'border': 1})

        row = 3
        column = 5

        sheet.merge_range(row, column, row + 1, column + 4, 'كشف موظف تفصيلي', head)
        row += 1
        column += 5
        full_path = os.path.realpath(__file__)
        path = full_path.split('/')
        path = path[0:-2]
        path = '/'.join(path)
        c_p = path + '/static/src/img/'
        if not c_p:
            raise ValidationError('Check addon paths on configuration file')
        header_path = c_p + 'sc_header.jpg'

        with open(header_path, "rb") as image_file:
            image_data = image_file.read()
            base64_data = base64.b64encode(image_data).decode("utf-8")
        if base64_data:
            logo_image = io.BytesIO(base64.b64decode(base64_data))
            sheet.insert_image(row - 3, 13, "image.png",
                               {'image_data': logo_image, 'x_scale': 0.31, 'y_scale': 0.31})

        row = 11
        column = 14

        sheet.merge_range(row, column, row - 1, column - 2, 'المسمي  الوظيفي ', cell_bold)
        sheet.merge_range(row, column - 3, row - 1, column - 6,
                          payslip.contract_id.job_id.name if payslip.contract_id.job_id.name else '',
                          border_cell)

        sheet.merge_range(row, column - 8, row - 1, column - 10, 'الرقم  الوظيفي  ', cell_bold)
        sheet.merge_range(row, column - 11, row - 1, column - 13,
                          payslip.employee_id.registration_number,
                          border_cell)
        row += 3

        sheet.merge_range(row, column, row - 1, column - 2, 'الإ سم ', cell_bold)
        sheet.merge_range(row, column - 3, row - 1, column - 13,
                          payslip.employee_id.arabic_name if payslip.employee_id.arabic_name else payslip.employee_id.name,
                          border_cell)

        row += 3

        sheet.merge_range(row, column, row - 1, column - 2, ' الا دارة', cell_bold)
        sheet.merge_range(row, column - 3, row - 1, column - 6,
                          payslip.employee_id.department_id.name if payslip.employee_id.department_id else '',
                          border_cell)

        sheet.merge_range(row, column - 8, row - 1, column - 10, 'الدرجة', cell_bold)
        sheet.merge_range(row, column - 11, row - 1, column - 13,
                          payslip.contract_id.payscale_id.description if payslip.contract_id.payscale_id else '',
                          border_cell)
        row += 3

        sheet.merge_range(row, column, row - 1, column - 2, ' تاريخ مباشرة العمل', cell_bold)
        sheet.merge_range(row, column - 3, row - 1, column - 6,
                          payslip.employee_id.joining_date.strftime(
                              "%Y/%m/%d") if payslip.employee_id.joining_date else '',
                          border_cell)

        sheet.merge_range(row, column - 8, row - 1, column - 10, 'IBAN     رقم الحساب  البنكي', cell_bold)
        sheet.merge_range(row, column - 11, row - 1, column - 13,
                          payslip.employee_id.bank_account_id.iban_no if payslip.employee_id.bank_account_id else '',
                          border_cell)
        row += 3

        sheet.merge_range(row, column, row - 1, column - 2, ' رقم التليفون', cell_bold)
        sheet.merge_range(row, column - 3, row - 1, column - 6,
                          payslip.employee_id.phone_personal if payslip.employee_id.phone_personal else '',
                          border_cell)

        sheet.merge_range(row, column - 8, row - 1, column - 10, ' اسم البنك', cell_bold)
        sheet.merge_range(row, column - 11, row - 1, column - 13,
                          payslip.employee_id.bank_account_id.bank_id.name if payslip.employee_id.bank_account_id and payslip.employee_id.bank_account_id else '',
                          border_cell)
        row += 3

        sheet.merge_range(row, column, row - 1, column - 13,
                          str(self._get_arabic_date(payslip).get('year')) + \
                          ' ' + "راتب   شهر" + ' ' + self._get_arabic_date(payslip).get('month_name'),
                          header)
        row += 2

        sheet.merge_range(row, column, row - 1, column - 3,
                          'المرجع',
                          cell)
        row += 2

        for basic in payslip.line_ids.filtered(lambda line: line.category_id.code == 'BASIC'):
            sheet.merge_range(row, column - 4, row - 1, column - 11,
                              basic.salary_rule_id.with_context(lang='ar_001').name, cell)
            sheet.merge_range(row, column - 12, row - 1, column - 13, basic.total, cell)
            row += 2
        all_allowances = payslip.line_ids.filtered(
            lambda line: line.category_id.code not in ['BASIC', 'NET'] \
                         and line.total > 0 and not line.salary_rule_id.input_element)
        if all_allowances:
            sheet.merge_range(row, column, row - 1, column - 3, 'البدلات طبقاً للائحة الموارد البشرية', cell)
            row += 2
            for allowance in all_allowances:
                sheet.merge_range(row, column - 4, row - 1, column - 11,
                                  allowance.salary_rule_id.with_context(lang='ar_001').name,
                                  cell)
                sheet.merge_range(row, column - 12, row - 1, column - 13, allowance.total, cell)
                row += 2

        sheet.merge_range(row, column, row - 1, column - 3, 'إجمالى الراتب', cell_bold)
        total_salary = sum(
            payslip.line_ids.filtered(
                lambda line: line.category_id.code not in ['NET'] and \
                             (line.total > 0 or (line.total == 0 and line.category_id.code not in ['BASIC', 'DED'])) \
                             and not line.salary_rule_id.input_element).mapped('total'))
        sheet.merge_range(row, column - 4, row - 1, column - 11,
                          payslip.currency_id.with_context(lang='ar_001').amount_to_text(total_salary), cell)
        sheet.merge_range(row, column - 12, row - 1, column - 13, total_salary, cell)
        row += 3
        input_elements = payslip.line_ids.filtered(
            lambda line: line.category_id.code not in ['BASIC', 'NET'] and \
                         line.total > 0 and line.salary_rule_id.input_element)
        if input_elements:
            sheet.merge_range(row, column, row - 1, column - 13, ' إضافات', cell_bold)
            row += 2
            for addition in input_elements:
                sheet.merge_range(row, column - 4, row - 1, column - 11,
                                  addition.salary_rule_id.with_context(lang='ar_001').name, cell)
                sheet.merge_range(row, column - 12, row - 1, column - 13, addition.total, cell)
                row += 2

            sheet.merge_range(row, column, row - 1, column - 3, 'إجمالى الاضافات', cell_bold)
            total_additions = sum(
                payslip.line_ids.filtered(
                    lambda line: line.category_id.code not in ['BASIC', 'NET'] and \
                                 line.total > 0 and line.salary_rule_id.input_element).mapped('total'))
            sheet.merge_range(row, column - 4, row - 1, column - 11,
                              payslip.currency_id.with_context(lang='ar_001').amount_to_text(total_additions), cell)
            sheet.merge_range(row, column - 12, row - 1, column - 13, total_additions, cell)
            row += 3
        all_deductions = payslip.line_ids.filtered(lambda line: line.total < 0 and line.category_id.code != 'COMP')
        if all_deductions:
            sheet.merge_range(row, column, row - 1, column - 13, 'الخصومات والإستقطاعات والسلف', cell_bold)
            row += 2
            for deduction in all_deductions:
                sheet.merge_range(row, column - 4, row - 1, column - 11,
                                  deduction.salary_rule_id.with_context(lang='ar_001').name, cell)
                sheet.merge_range(row, column - 12, row - 1, column - 13, abs(deduction.total), cell)
                row += 2

            sheet.merge_range(row, column, row - 1, column - 3, 'إجمالى الخصومات', cell_bold)
            total_deduction = abs(sum(
                payslip.line_ids.filtered(lambda line: line.total < 0 and line.category_id.code != 'COMP').mapped(
                    'total')))
            sheet.merge_range(row, column - 4, row - 1, column - 11,
                              payslip.currency_id.with_context(lang='ar_001').amount_to_text(total_deduction), cell)
            sheet.merge_range(row, column - 12, row - 1, column - 13, total_deduction, cell)
            row += 3

        sheet.merge_range(row, column, row - 1, column - 3, 'صافى الراتب', cell_bold)
        # net_salary = total_salary + total_additions + total_deduction
        net_salary = payslip.net_wage
        sheet.merge_range(row, column - 4, row - 1, column - 11,
                          payslip.currency_id.with_context(lang='ar_001').amount_to_text(net_salary), cell_bold)
        sheet.merge_range(row, column - 12, row - 1, column - 13, net_salary, cell_bold)
        row += 5

        sheet.merge_range(row, column - 1, row - 1, column - 4, 'شؤون الموظفين', cell_bold)
        sheet.merge_range(row, column - 5, row - 1, column - 8, 'محاسب', cell_bold)
        sheet.merge_range(row, column - 9, row - 1, column - 12, 'رئيس الحسابات', cell_bold)

    def collaborator_employees_report(self, payslip, workbook):
        report_name = payslip.employee_id.name

        # One sheet by payslip
        sheet = workbook.add_worksheet(report_name)

        head = workbook.add_format({'align': 'center', 'bold': True, 'size': 16})
        header = workbook.add_format({'align': 'right', 'bold': True, 'size': 14, })
        cell_bold = workbook.add_format({'align': 'center', 'bold': True, 'size': 14, })
        cell = workbook.add_format({'align': 'center', 'size': 14, 'border': 1})

        row = 3
        column = 5

        sheet.merge_range(row, column, row + 1, column + 4, 'كشف موظف تفصيلي', head)
        row += 1
        column += 5
        full_path = os.path.realpath(__file__)
        path = full_path.split('/')
        path = path[0:-2]
        path = '/'.join(path)
        c_p = path + '/static/src/img/'
        if not c_p:
            raise ValidationError('Check addon paths on configuration file')
        header_path = c_p + 'sc_header.jpg'

        with open(header_path, "rb") as image_file:
            image_data = image_file.read()
            base64_data = base64.b64encode(image_data).decode("utf-8")
        if base64_data:
            logo_image = io.BytesIO(base64.b64decode(base64_data))
            sheet.insert_image(row - 3, 13, "image.png",
                               {'image_data': logo_image, 'x_scale': 0.32, 'y_scale': 0.32})

        row = 11
        column = 14

        sheet.merge_range(row, column, row - 1, column - 2, 'المسمي  الوظيفي ', cell_bold)
        sheet.merge_range(row, column - 3, row - 1, column - 6,
                          payslip.contract_id.job_id.name if payslip.contract_id.job_id.name else '',
                          cell)

        sheet.merge_range(row, column - 8, row - 1, column - 10, 'الرقم  الوظيفي  ', cell_bold)
        sheet.merge_range(row, column - 11, row - 1, column - 14,
                          payslip.employee_id.registration_number,
                          cell)
        row += 3

        sheet.merge_range(row, column, row - 1, column - 2, 'الإ سم ', cell_bold)
        sheet.merge_range(row, column - 3, row - 1, column - 14,
                          payslip.employee_id.arabic_name if payslip.employee_id.arabic_name else payslip.employee_id.name,
                          cell)

        row += 3

        sheet.merge_range(row, column, row - 1, column - 2, ' الا دارة', cell_bold)
        sheet.merge_range(row, column - 3, row - 1, column - 6,
                          payslip.employee_id.department_id.name if payslip.employee_id.department_id else '',
                          cell)

        sheet.merge_range(row, column - 8, row - 1, column - 10, 'الدرجة', cell_bold)
        sheet.merge_range(row, column - 11, row - 1, column - 14,
                          payslip.contract_id.payscale_id.description if payslip.contract_id.payscale_id else '',
                          cell)
        row += 3

        sheet.merge_range(row, column, row - 1, column - 2, ' تاريخ مباشرة العمل', cell_bold)
        sheet.merge_range(row, column - 3, row - 1, column - 6,
                          payslip.employee_id.joining_date.strftime(
                              "%Y/%m/%d") if payslip.employee_id.joining_date else '',
                          cell)

        sheet.merge_range(row, column - 8, row - 1, column - 10, 'IBAN     رقم الحساب  البنكي', cell_bold)
        sheet.merge_range(row, column - 11, row - 1, column - 14,
                          payslip.employee_id.bank_account_id.iban_no if payslip.employee_id.bank_account_id else '',
                          cell)
        row += 3

        sheet.merge_range(row, column, row - 1, column - 2, ' رقم التليفون', cell_bold)
        sheet.merge_range(row, column - 3, row - 1, column - 6,
                          payslip.employee_id.phone_personal if payslip.employee_id.phone_personal else '',
                          cell)

        sheet.merge_range(row, column - 8, row - 1, column - 10, ' اسم البنك', cell_bold)
        sheet.merge_range(row, column - 11, row - 1, column - 14,
                          payslip.employee_id.bank_account_id.bank_id.name if payslip.employee_id.bank_account_id and payslip.employee_id.bank_account_id else '',
                          cell)
        row += 3

        sheet.merge_range(row, column, row - 1, column - 14,
                          str(self._get_arabic_date(payslip).get('year')) + \
                          ' ' + "راتب   شهر" + ' ' + self._get_arabic_date(payslip).get('month_name'),
                          header)
        row += 2

        sheet.merge_range(row, column, row - 1, column, 'المرجع', cell)
        row += 2

        sheet.merge_range(row, column, row - 1, column - 3, ' البدلات طبقاً للائحة الموارد البشرية ', cell)

        row += 1
        not_input_allowances = payslip.line_ids.filtered(
            lambda s: s.category_id.code not in ["DED", "NET"] and s.salary_rule_id.input_element == False)
        input_allowance = payslip.line_ids.filtered(
            lambda s: s.category_id.code not in ["DED", "NET"] and s.salary_rule_id.input_element == True)
        sum_not_input_allowances = sum(not_input_allowances.mapped('amount')) if not_input_allowances else 0.0
        sum_input_allowance = sum(input_allowance.mapped('amount')) if input_allowance else 0.0

        deductions = payslip.line_ids.filtered(lambda s: s.category_id.code == "DED")
        sum_deductions = abs(sum(map(abs, deductions.mapped('amount')))) if deductions else 0.0
        net_value = (sum_not_input_allowances + sum_input_allowance) - sum_deductions
        sum_deductions = 0 - sum_deductions

        if not_input_allowances:
            for not_input_allowance in not_input_allowances:
                if not_input_allowance.amount != 0:
                    sheet.merge_range(row, column, row, column - 5,
                                      not_input_allowance.salary_rule_id.with_context(lang='ar_001').name, cell)
                    sheet.merge_range(row, column - 10, row, column - 7, not_input_allowance.amount, cell)
                    row += 1
            sheet.merge_range(row, column, row, column - 5, '', cell)
            if sum_not_input_allowances != 0:
                sheet.merge_range(row, column - 10, row, column - 7, sum_not_input_allowances, cell)
            row += 1

            if sum_input_allowance != 0:
                sheet.merge_range(row, column - 4, row + 1, column - 7, ' اﻷضافات ', cell)
                row += 2

                sheet.merge_range(row, column, row, column - 5, 'إجمالي الإضافات', cell)
                sheet.merge_range(row, column - 10, row, column - 7, sum_input_allowance, cell)
            row += 2
        if deductions:
            sheet.merge_range(row, column, row - 1, column - 3, " الخصومات والإستقطاعات والسلف", cell)
            row += 1

            for deduction in deductions:
                if deduction.amount != 0:
                    sheet.merge_range(row, column, row, column - 5,
                                      deduction.salary_rule_id.with_context(lang='ar_001').name, cell)
                    sheet.merge_range(row, column - 10, row, column - 7, deduction.amount, cell)
                    row += 1

        if sum_deductions != 0:
            sheet.merge_range(row, column, row, column - 5, 'إجمالي الخصومات', cell)
            sheet.merge_range(row, column - 10, row, column - 7, sum_deductions, cell)
        row += 2

        if net_value != 0:
            sheet.merge_range(row, column, row - 1, column - 1, "صافى المكافآة", cell)
            sheet.merge_range(row, column - 5, row - 1, column - 2,
                              payslip.currency_id.with_context(lang='ar_001').amount_to_text(net_value), cell)
            sheet.merge_range(row, column - 10, row - 1, column - 7, net_value, cell)

    def generate_xlsx_report(self, workbook, data, payslips):
        for payslip in payslips:
            if payslip.employee_id.collaborator == False:
                self.non_collaborator_employees_report(payslip, workbook)
            else:
                self.collaborator_employees_report(payslip, workbook)
