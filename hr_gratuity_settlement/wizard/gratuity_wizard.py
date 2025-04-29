from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
from odoo.tools.date_utils import end_of


class GratuityExcelReport(models.AbstractModel):
    _name = 'report.hr_gratuity_settlement.request_allowance_xlsx_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, partners):
        print(data)
        sheet = workbook.add_worksheet('Gratuity Report')
        data_format = workbook.add_format({'align': 'center'})
        header_row_style = workbook.add_format({'bold': True, 'align': 'center', 'border': True})
        date_format = workbook.add_format({'num_format': 'd-m-yyyy', 'align': 'center'})

        data = self.env['hr.gratuity'].browse(data.get('records'))

        row = 0
        col = 0
        if data:
            sheet.set_column(0, 5, 18)
            sheet.write(row, col, 'Employee Number', header_row_style)
            sheet.write(row, col + 1, 'Employee Name', header_row_style)
            sheet.write(row, col + 2, 'Total Years Worked', header_row_style)
            sheet.write(row, col + 3, 'Total Amount Pay', header_row_style)
            sheet.write(row, col + 4, 'Total Amount Deduction', header_row_style)
            sheet.write(row, col + 5, 'Amount Final Settlement', header_row_style)
            row += 1
            for rec in data:
                sheet.write(row, col, rec.employee_id.registration_number, data_format)
                sheet.write(row, col + 1, rec.employee_id.name, data_format)
                sheet.write(row, col + 2, rec.total_working_years, data_format)
                sheet.write(row, col + 3, rec.total_amount_pay, data_format)
                sheet.write(row, col + 4, rec.total_amount_deduction, data_format)
                sheet.write(row, col + 5, rec.total_amount_final_settlement, data_format)
                row += 1

