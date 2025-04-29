import base64
import io
from datetime import datetime

from odoo import models


class HrPayslipRunXlsx(models.AbstractModel):
    _name = 'report.payslip_reports.collaborator_employees_salaries'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, partners):
        for obj in partners:
            report_name = obj.name
            sheet = workbook.add_worksheet(report_name[:31])
            bold = workbook.add_format({'align': 'center'})
            head = workbook.add_format({'align': 'center', 'bold': True, 'size': 14})
            cell = workbook.add_format({'align': 'center', 'bold': True, 'size': 14, 'border': 1})
            cell_text_format = workbook.add_format(
                {'align': 'center', 'bold': True, 'font_size': 12, 'bg_color': '#F8F8FF', 'border': 1})
            cell_sum_column = workbook.add_format(
                {'align': 'center', 'bold': True, 'font_size': 12, 'bg_color': '#8FBC8F', 'border': 1})

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

            head2 = 'كشف مكافأت المتعاونين' + ' ' + "عن شهر" + ' ' + month_name + ' ' + str(year)
            sheet.merge_range(3, 4, 3 + 1, 4 + 4, head2, head)

            hr_payslips = obj.slip_ids.filtered(lambda s: s.employee_id.collaborator == True)
            departments = {}
            if hr_payslips:

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
            if departments:
                all_sum_net_salary = 0.0
                all_sum_total_salary = 0.0
                all_sum_total_other_allowance_rules = 0.0
                all_sum_total_allowance_rules = 0.0

                all_sum_total_other_deduction_rules = 0.0
                all_sum_total_deduction_rules = 0.0
                all_sum_total_deduction = 0.0

                for department_id, department_list in departments.items():
                    sum_net_salary = 0.0
                    sum_total_salary = 0.0
                    sum_total_other_allowance_rules = 0.0
                    sum_total_allowance_rules = 0.0

                    sum_total_other_deduction_rules = 0.0
                    sum_total_deduction_rules = 0.0
                    sum_total_deduction = 0.0

                    serial = 1
                    department_obj = self.env['hr.department'].browse(department_id)
                    payslips_based_department = hr_payslips.filtered(
                        lambda s: s.employee_id.department_id.id in department_list)
                    if payslips_based_department:
                        sheet.merge_range(payslip_raw, payslip_col, payslip_raw + 3, payslip_col, "صافي الراتب",
                                          cell_text_format)
                        payslip_col += 1
                        sheet.set_column(payslip_raw, payslip_col, 15)
                        sheet.merge_range(payslip_raw, payslip_col, payslip_raw + 3, payslip_col,
                                          "اجمالي الخصومات", cell_text_format)
                        payslip_col += 1

                        sheet.merge_range(payslip_raw, payslip_col, payslip_raw + 3, payslip_col,
                                          "خصومات أخرى", cell_text_format)
                        payslip_col += 1

                        sheet.set_column(payslip_raw, payslip_col, 15)
                        sheet.merge_range(payslip_raw, payslip_col, payslip_raw + 1, payslip_col,
                                          "الخصومات والسلف ", cell_text_format)
                        sheet.set_column(payslip_raw + 2, payslip_col, 15)
                        sheet.merge_range(payslip_raw + 2, payslip_col, payslip_raw + 3, payslip_col,
                                          "خصومات الشهر الجاري", cell_text_format)
                        payslip_col += 1
                        sheet.merge_range(payslip_raw, payslip_col, payslip_raw + 3, payslip_col,
                                          "اجمالي الراتب", cell_text_format)

                        payslip_col += 1
                        sheet.merge_range(payslip_raw, payslip_col, payslip_raw + 3, payslip_col,
                                          "مكافآت / بدلات أخرى", cell_text_format)

                        payslip_col += 1

                        sheet.merge_range(payslip_raw, payslip_col, payslip_raw + 1, payslip_col + 1,
                                          "البدلات و العلاوات ", cell_text_format)

                        sheet.merge_range(payslip_raw + 2, payslip_col, payslip_raw + 3, payslip_col + 1,
                                          "البدل/المكافأة عن الشهر الجاري", cell_text_format)

                        payslip_col += 2
                        sheet.merge_range(payslip_raw, payslip_col, payslip_raw + 3, payslip_col,
                                          "الدرجة المالية", cell_text_format)

                        payslip_col += 1
                        sheet.merge_range(payslip_raw, payslip_col, payslip_raw + 3, payslip_col,
                                          "المسمي الوظيفي", cell_text_format)

                        payslip_col += 1
                        sheet.merge_range(payslip_raw, payslip_col, payslip_raw + 3, payslip_col + 2,
                                          "الاســم", cell_text_format)
                        payslip_col += 3
                        sheet.merge_range(payslip_raw, payslip_col, payslip_raw + 3, payslip_col,
                                          "الرقم الوظيفي", cell_text_format)

                        payslip_col += 1
                        sheet.merge_range(payslip_raw, payslip_col, payslip_raw + 3, payslip_col,
                                          "م", cell_text_format)
                        payslip_col += 1

                        sheet.merge_range(payslip_raw - 1, payslip_col - 5, payslip_raw - 1, payslip_col - 1,
                                          department_obj.name, cell_text_format)

                        payslip_raw += 4
                        payslip_col = 0

                        for payslip in payslips_based_department:
                            deduction_rules = payslip.line_ids.filtered(
                                lambda s: s.category_id.code == "DED" and s.salary_rule_id.input_element == False)
                            other_deduction_rules = payslip.line_ids.filtered(
                                lambda s: s.category_id.code == "DED" and s.salary_rule_id.input_element == True)

                            total_deduction_rules = sum(
                                map(abs, deduction_rules.mapped('amount'))) if deduction_rules else 0.0
                            total_other_deduction_rules = sum(
                                map(abs, other_deduction_rules.mapped('amount'))) if other_deduction_rules else 0.0
                            total_deduction = 0 - (total_deduction_rules + total_other_deduction_rules)
                            total_deduction_rules = 0 - total_deduction_rules if total_deduction_rules else 0.0
                            total_other_deduction_rules = 0 - total_other_deduction_rules if total_other_deduction_rules else 0.0

                            allowance_rules = payslip.line_ids.filtered(lambda s: s.category_id.code in ["BASIC",
                                                                                                         "ALW"] and s.salary_rule_id.input_element == False)
                            other_allowance_rules = payslip.line_ids.filtered(lambda s: s.category_id.code in ["BASIC",
                                                                                                               "ALW"] and s.salary_rule_id.input_element == True)
                            total_allowance_rules = sum(
                                map(abs, allowance_rules.mapped('amount'))) if allowance_rules else 0.0
                            total_other_allowance_rules = sum(
                                map(abs, other_allowance_rules.mapped('amount'))) if other_allowance_rules else 0.0
                            total_salary = total_allowance_rules + total_other_allowance_rules

                            # net_salary = total_salary - abs(total_deduction)
                            net_salary_rule = payslip.line_ids.filtered(
                                lambda s: s.category_id.code == "NET" and s.salary_rule_id.input_element == False)
                            net_salary = net_salary_rule.amount if net_salary_rule else False

                            sum_total_other_deduction_rules += total_other_deduction_rules
                            sum_total_deduction_rules += total_deduction_rules
                            sum_total_deduction += total_deduction

                            sum_net_salary += net_salary
                            sum_total_salary += total_salary
                            sum_total_other_allowance_rules += total_other_allowance_rules
                            sum_total_allowance_rules += total_allowance_rules

                            sheet.write(payslip_raw, payslip_col, net_salary, bold)
                            payslip_col += 1

                            sheet.write(payslip_raw, payslip_col, total_deduction, bold)
                            payslip_col += 1

                            sheet.write(payslip_raw, payslip_col, abs(total_other_deduction_rules), bold)
                            payslip_col += 1

                            sheet.write(payslip_raw, payslip_col, abs(total_deduction_rules), bold)
                            payslip_col += 1

                            sheet.write(payslip_raw, payslip_col, total_salary, bold)
                            payslip_col += 1

                            sheet.write(payslip_raw, payslip_col, total_other_allowance_rules, bold)
                            payslip_col += 1

                            sheet.merge_range(payslip_raw, payslip_col, payslip_raw, payslip_col + 1,
                                              total_allowance_rules, bold)
                            payslip_col += 2

                            sheet.write(payslip_raw, payslip_col,
                                        payslip.employee_id.contract_id.payscale_id.description, bold)
                            payslip_col += 1

                            sheet.write(payslip_raw, payslip_col, payslip.employee_id.contract_id.job_id.name, bold)
                            payslip_col += 1

                            employee_name = payslip.employee_id.arabic_name if payslip.employee_id.arabic_name else payslip.employee_id.name
                            sheet.merge_range(payslip_raw, payslip_col, payslip_raw, payslip_col + 2, employee_name,
                                              bold)
                            payslip_col += 3

                            sheet.write(payslip_raw, payslip_col, payslip.employee_id.registration_number, bold)
                            payslip_col += 1

                            sheet.write(payslip_raw, payslip_col, serial, bold)
                            payslip_col += 1

                            payslip_raw += 1
                            payslip_col = 0
                            serial += 1

                        payslip_col = 0

                        sheet.merge_range(payslip_raw, payslip_col, payslip_raw + 2, payslip_col, sum_net_salary, cell)
                        payslip_col += 1

                        sheet.merge_range(payslip_raw, payslip_col, payslip_raw + 2, payslip_col, sum_total_deduction,
                                          cell)
                        payslip_col += 1

                        sheet.merge_range(payslip_raw, payslip_col, payslip_raw + 2, payslip_col,
                                          abs(sum_total_other_deduction_rules), cell)
                        payslip_col += 1

                        sheet.merge_range(payslip_raw, payslip_col, payslip_raw + 2, payslip_col,
                                          abs(sum_total_deduction_rules), cell)
                        payslip_col += 1

                        sheet.merge_range(payslip_raw, payslip_col, payslip_raw + 2, payslip_col, sum_total_salary,
                                          cell)
                        payslip_col += 1

                        sheet.merge_range(payslip_raw, payslip_col, payslip_raw + 2, payslip_col,
                                          sum_total_other_allowance_rules, cell)
                        payslip_col += 1

                        sheet.merge_range(payslip_raw, payslip_col, payslip_raw + 2, payslip_col + 1,
                                          sum_total_allowance_rules, cell)
                        payslip_col += 2

                        sheet.merge_range(payslip_raw, payslip_col, payslip_raw + 2, payslip_col + 6,
                                          "أجمالي رواتب ومكافأت وبدلات متعاوني  " + department_obj.name, cell)

                        all_sum_total_other_deduction_rules += sum_total_other_deduction_rules
                        all_sum_total_deduction_rules += sum_total_deduction_rules
                        all_sum_total_deduction += sum_total_deduction
                        all_sum_net_salary += sum_net_salary
                        all_sum_total_salary += sum_total_salary
                        all_sum_total_other_allowance_rules += sum_total_other_allowance_rules
                        all_sum_total_allowance_rules += sum_total_allowance_rules

                        payslip_raw += 7
                        payslip_col = 0

                sheet.merge_range(payslip_raw, payslip_col, payslip_raw + 2, payslip_col, all_sum_net_salary, cell)
                payslip_col += 1

                sheet.merge_range(payslip_raw, payslip_col, payslip_raw + 2, payslip_col, all_sum_total_deduction, cell)
                payslip_col += 1

                sheet.merge_range(payslip_raw, payslip_col, payslip_raw + 2, payslip_col,
                                  abs(all_sum_total_other_deduction_rules), cell)
                payslip_col += 1

                sheet.merge_range(payslip_raw, payslip_col, payslip_raw + 2, payslip_col, all_sum_total_deduction_rules,
                                  cell)
                payslip_col += 1

                sheet.merge_range(payslip_raw, payslip_col, payslip_raw + 2, payslip_col, all_sum_total_salary, cell)
                payslip_col += 1

                sheet.merge_range(payslip_raw, payslip_col, payslip_raw + 2, payslip_col,
                                  all_sum_total_other_allowance_rules, cell)
                payslip_col += 1

                sheet.merge_range(payslip_raw, payslip_col, payslip_raw + 2, payslip_col + 1,
                                  all_sum_total_allowance_rules,
                                  cell)
                payslip_col += 2

                sheet.merge_range(payslip_raw, payslip_col, payslip_raw + 2, payslip_col + 6,
                                  " إجمالي رواتب ومكافآت وبدلات متعاوني المؤسسة ", cell)

                payslip_raw += 7
                payslip_col = 0

                sheet.merge_range(payslip_raw, payslip_col, payslip_raw, payslip_col + 1,
                                  " رئيس الحسابات ", cell)

                payslip_col += 3

                sheet.merge_range(payslip_raw, payslip_col, payslip_raw, payslip_col + 1,
                                  "محاسب", cell)

                payslip_col += 3

                sheet.merge_range(payslip_raw, payslip_col, payslip_raw, payslip_col + 1,
                                  "شؤون الموظفين", cell)
