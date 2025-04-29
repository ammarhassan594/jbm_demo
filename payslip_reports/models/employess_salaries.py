import base64
import io
from datetime import datetime

from odoo import models


class HrPayslipRunXlsx(models.AbstractModel):
    _name = 'report.payslip_reports.employees_salaries_xlsx_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, partners):
        for obj in partners:
            line_raw = 10

            report_name = obj.name
            # One sheet by partner
            sheet = workbook.add_worksheet(report_name[:31])
            bold = workbook.add_format({'bold': True, 'align': 'center'})
            head = workbook.add_format({'align': 'center', 'bold': True, 'size': 14, 'bg_color': '#FAEBD7'})
            cell = workbook.add_format({'align': 'center', 'bold': True, 'size': 14, 'bg_color': '#ADD8E6'})
            cell_text_format = workbook.add_format(
                {'align': 'center', 'bold': True, 'font_size': 12, 'bg_color': '#F8F8FF', 'border': 1})
            cell_sum_column = workbook.add_format(
                {'align': 'center', 'bold': True, 'font_size': 12, 'bg_color': '#8FBC8F', 'border': 1})
            row = 2
            column = 0
            sheet.merge_range(row, 6, row + 1, column + 30,
                              'كشف رواتب السادة المعينين بمؤسسة الشيخ جاسم بن محمد بن ثاني للرعاية اﻷجتماعية', head)

            # company_logo = io.BytesIO(base64.b64decode(obj.company_id.logo))
            # print('obj.company_id.logo###', obj.company_id.logo)
            # sheet.insert_image('B3', company_logo, {'image_data': company_logo})

            month = datetime.strftime(datetime.strptime(str(obj.date_start), "%Y-%m-%d"), "%m")
            year = datetime.strftime(datetime.strptime(str(obj.date_start), "%Y-%m-%d"), "%Y")
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

            head2 = str(year) + ' ' + "عن   شهر" + ' ' + month_name
            sheet.merge_range(4, 14, 4 + 1, 14 + 6, head2, head)

            hr_payslips = obj.slip_ids.filtered(lambda s: s.employee_id.collaborator == False)
            departments = {}
            deductions = []
            allowances = []
            if hr_payslips:
                salary_structure = hr_payslips.mapped("struct_id")
                if salary_structure:
                    structure_rules = salary_structure.mapped("rule_ids")
                    deductions = structure_rules.filtered(lambda s: s.category_id.code == "DED")
                    allowances = structure_rules.filtered(lambda s: s.category_id.code in ["BASIC", "ALW"])

                for department in hr_payslips.employee_id.department_id:
                    if department.type == 'BU':
                        if not departments.get(department.id):
                            departments.update({department.id: [department.id]})
                        else:
                            departments.get(department.id).append(department.id)
                    else:
                        group_department = department
                        if group_department.type != 'BU':
                            if not department.parent_id:
                                break
                            group_department = department.parent_id
                        if not departments.get(group_department.id):
                            departments.update({group_department.id: [department.id]})
                        else:
                            departments.get(group_department.id).append(department.id)

            payslip_raw = 6
            payslip_col = 0
            begin_deduction_column = 5
            sum_deduction = 0.0
            sum_allowance = 0.0
            sum_deduction_column_number = begin_deduction_column
            sum_allowance_column_number = 5 + len(deductions) + 3
            degree_column = 5 + len(deductions) + 3 + len(allowances)
            sum_salary = 0.0
            sum_net_salary = 0.0

            sum_salary_column = 5 + len(deductions)

            for department_id, department_list in departments.items():
                serial = 1
                department_obj = self.env['hr.department'].browse(department_id)
                payslips_based_department = hr_payslips.filtered(
                    lambda s: s.employee_id.department_id.id in department_list)
                if payslips_based_department:
                    sheet.merge_range(payslip_raw, payslip_col, payslip_raw + 3, payslip_col + 4, "صافي الراتب",
                                      cell_text_format)
                    net_salary_column = payslip_col
                    sheet.merge_range(payslip_raw, 5, payslip_raw + 2, 5 + int(len(deductions) - 1),
                                      "اجمالي الخصومات", cell_text_format)

                    i = payslip_raw + 3
                    y = 5

                    begin_deduction_column = y
                    for deduction in deductions:
                        sheet.set_column(i, y, 20)
                        sheet.write(i, y, deduction.with_context(lang="ar_001").name, cell_text_format)
                        y += 1

                    sheet.merge_range(payslip_raw, y, payslip_raw + 3, y + 2, "اجمالي الراتب", workbook.add_format(
                        {'align': 'center', 'bold': True, 'font_size': 12, 'bg_color': '#FAEBD7', 'border': 1}))
                    total_salary_column = y
                    y += 3
                    j = y

                    begin_allowance_column = j
                    for allowance in allowances:
                        sheet.set_column(i, j, 20)
                        sheet.write(i, j, allowance.with_context(lang="ar_001").name, cell_text_format)
                        j += 1

                    sheet.merge_range(payslip_raw, y, payslip_raw + 2, y + int(len(allowances) - 1),
                                      "البدلات و العلاوات", cell_text_format)
                    y = y + int(len(allowances))
                    sheet.merge_range(payslip_raw, y, payslip_raw + 3, y + 2, "الدرجة المالية", cell_text_format)
                    degree_column = y
                    y += 3
                    sheet.merge_range(payslip_raw, y, payslip_raw + 3, y + 2, "المسمي الوظيفي", cell_text_format)
                    job_title_column = y
                    y += 3
                    sheet.merge_range(payslip_raw, y, payslip_raw + 3, y + 4, "الاسم", cell_text_format)
                    name_column = y
                    y += 5
                    sheet.merge_range(payslip_raw, y, payslip_raw + 3, y + 2, "الرقم الوظيفي", cell_text_format)
                    registration_number_column = y
                    y += 3
                    sheet.merge_range(payslip_raw, y, payslip_raw + 3, y + 2, "م", cell_text_format)

                    sheet.merge_range(payslip_raw - 2, y, payslip_raw - 1, y + 2,
                                      department_obj.name, head)

                    payslip_raw += 4
                    sum_column_net_total_salary = 0.0
                    sum_column_total_salary_value = 0.0
                    for payslip in payslips_based_department:
                        total_salary_value = 0.0
                        net_salary_emp = 0.0
                        total_deduction_value = 0.0
                        sheet.merge_range(payslip_raw, y, payslip_raw, y + 2, serial, bold)
                        sheet.merge_range(payslip_raw, registration_number_column, payslip_raw,
                                          registration_number_column + 2, payslip.employee_id.registration_number,
                                          bold)
                        employee_name = payslip.employee_id.arabic_name if payslip.employee_id.arabic_name else payslip.employee_id.name
                        sheet.merge_range(payslip_raw, name_column, payslip_raw, name_column + 4,
                                          employee_name, bold)
                        sheet.merge_range(payslip_raw, job_title_column, payslip_raw, job_title_column + 2,
                                          payslip.employee_id.contract_id.job_id.name, bold)
                        sheet.merge_range(payslip_raw, degree_column, payslip_raw, degree_column + 2,
                                          payslip.employee_id.contract_id.payscale_id.description, bold)
                        rule_ids = payslip.mapped('line_ids')
                        if rule_ids:
                            deduction_rule_ids = rule_ids.filtered(lambda s: s.category_id.code == "DED")
                            for rule in deduction_rule_ids:
                                x = begin_deduction_column
                                for deduction_value in deductions:
                                    if rule.salary_rule_id.id == deduction_value.id:
                                        sheet.set_column(payslip_raw, x, 20)
                                        sheet.write(payslip_raw, x, rule.amount, cell_text_format)
                                        total_deduction_value += abs(rule.amount)

                                    x += 1

                            allowances_rule_ids = rule_ids.filtered(
                                lambda s: s.category_id.code in ["BASIC", "ALW"])
                            for allow_rule in allowances_rule_ids:
                                x = begin_allowance_column
                                for allowance_value in allowances:
                                    if allow_rule.salary_rule_id.id == allowance_value.id:
                                        sheet.set_column(payslip_raw, x, 20)
                                        sheet.write(payslip_raw, x, allow_rule.amount, cell_text_format)
                                        total_salary_value += allow_rule.amount
                                    x += 1
                        net_salary_rules = rule_ids.filtered(lambda s: s.category_id.code == 'NET')
                        net_salary_emp = net_salary_rules.amount if net_salary_rules else False

                        sum_column_total_salary_value += total_salary_value
                        sum_column_total_salary_value += net_salary_emp
                        sheet.merge_range(payslip_raw, total_salary_column, payslip_raw, total_salary_column + 2,
                                          total_salary_value, bold)

                        sum_salary += total_salary_value

                        net_total_salary = total_salary_value - total_deduction_value
                        # sum_column_net_total_salary += net_total_salary
                        sum_column_net_total_salary += net_salary_emp

                        # sheet.merge_range(payslip_raw, net_salary_column, payslip_raw, net_salary_column + 4,
                        #                   net_total_salary, bold)
                        #

                        sheet.merge_range(payslip_raw, net_salary_column, payslip_raw, net_salary_column + 4,
                                          net_salary_emp, bold)

                        # sum_net_salary += net_total_salary
                        sum_net_salary += net_salary_emp

                        serial += 1
                        payslip_raw += 1

                    sum_column = 0.0
                    sum_column_number = begin_deduction_column

                    for deduction in deductions:
                        for payslip_line in payslips_based_department:
                            rules_ids = payslip_line.line_ids.filtered(
                                lambda s: s.category_id.code == "DED" and s.salary_rule_id.id == deduction.id)
                            sum_column += sum(rules_ids.mapped('amount'))
                        sheet.set_column(payslip_raw, sum_column_number, 20)
                        sheet.write(payslip_raw, sum_column_number, sum_column, cell_sum_column)
                        sum_column_number += 1
                        sum_column = 0.0

                    allowance_sum_column = 0.0
                    allowance_sum_column_number = begin_allowance_column
                    for allowance in allowances:
                        for payslip_line in payslips_based_department:
                            rules_ids = payslip_line.line_ids.filtered(
                                lambda s: s.category_id.code in ["BASIC",
                                                                 "ALW"] and s.salary_rule_id.id == allowance.id)
                            allowance_sum_column += sum(rules_ids.mapped('amount'))
                        sheet.set_column(payslip_raw, allowance_sum_column_number, 20)
                        sheet.write(payslip_raw, allowance_sum_column_number, allowance_sum_column, cell_sum_column)
                        allowance_sum_column_number += 1
                        allowance_sum_column = 0.0

                    sheet.merge_range(payslip_raw, net_salary_column, payslip_raw, net_salary_column + 4,
                                      sum_column_net_total_salary, head)

                    sheet.merge_range(payslip_raw, total_salary_column, payslip_raw, total_salary_column + 2,
                                      sum_column_total_salary_value, cell_sum_column)

                    sheet.merge_range(payslip_raw, degree_column, payslip_raw, degree_column + 16,
                                      " إجمالي رواتب ومكافآت وبدلات موظفي  " + department_obj.name, head)

                    payslip_raw += 5
            # payslip_raw -= 5
            for deduc in deductions:
                for payslip_line in hr_payslips:
                    rules_ids = payslip_line.line_ids.filtered(
                        lambda s: s.category_id.code == "DED" and s.salary_rule_id.id == deduc.id)
                    sum_deduction += sum(rules_ids.mapped('amount'))
                sheet.set_column(payslip_raw, sum_deduction_column_number, 20)
                sheet.write(payslip_raw, sum_deduction_column_number, sum_deduction, head)
                sum_deduction_column_number += 1
                sum_deduction = 0.0

            for allow in allowances:
                for payslip_line in hr_payslips:
                    rules_ids = payslip_line.line_ids.filtered(
                        lambda s: s.category_id.code in ["BASIC", "ALW"] and s.salary_rule_id.id == allow.id)
                    sum_allowance += sum(rules_ids.mapped('amount'))
                sheet.set_column(payslip_raw, sum_allowance_column_number, 20)
                sheet.write(payslip_raw, sum_allowance_column_number, sum_allowance, head)
                sum_allowance_column_number += 1
                sum_allowance = 0.0

            if hr_payslips:
                sheet.merge_range(payslip_raw, degree_column, payslip_raw, degree_column + 16,
                                  " إجمالي رواتب ومكافآت وبدلات المؤسسة ", head)

                sheet.merge_range(payslip_raw, sum_salary_column, payslip_raw, sum_salary_column + 2,
                                  sum_salary, head)

                sheet.merge_range(payslip_raw, 0, payslip_raw, 0 + 4,
                                  sum_net_salary, cell)
