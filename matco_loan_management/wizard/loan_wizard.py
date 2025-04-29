from odoo import fields, api, models, _


class LoanRequestExcelReport(models.AbstractModel):
    _name = 'report.matco_loan_management.request_loan_xlsx_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, partners):
        sheet = workbook.add_worksheet('Loan Request Report')
        data_format = workbook.add_format({'align': 'center'})
        header_row_style = workbook.add_format({'bold': True, 'align': 'center', 'border': True})
        date_format = workbook.add_format({'num_format': 'd-m-yyyy', 'align': 'center'})

        loans = self.env['hr.loan'].browse(data.get('loans'))

        row = 0
        col = 0
        if loans:
            sheet.set_column(0, 5, 18)
            sheet.write(row, col, 'Employee Number', header_row_style)
            sheet.write(row, col + 1, 'Employee Name', header_row_style)
            sheet.write(row, col + 2, 'Type', header_row_style)
            sheet.write(row, col + 3, 'Date', header_row_style)
            sheet.write(row, col + 4, 'Purpose Code', header_row_style)
            sheet.write(row, col + 5, 'Bank Code', header_row_style)
            sheet.set_column(col + 6, col + 6, 35)
            sheet.write(row, col + 6, 'IBAN No', header_row_style)
            sheet.write(row, col + 7, 'Amount', header_row_style)
            row += 1
            for loan in loans:
                bank_code = None
                total_amount = loan.total_amount
                if loan.parent_loan_settle_id:
                    total_amount = loan.total_amount - loan.parent_loan_settle_id.settle_amount
                if loan.employee_id.bank_account_id.bank_id.bic:
                    bank_code = loan.employee_id.bank_account_id.bank_id.bic
                sheet.write(row, col, loan.employee_id.registration_number, data_format)
                sheet.write(row, col + 1, loan.employee_id.name if loan.employee_id.name else "", data_format)
                sheet.write(row, col + 2, loan.loan_type.name if loan.loan_type.name else "", data_format)
                sheet.write(row, col + 3, loan.date if loan.date else "", date_format)
                sheet.write(row, col + 4, loan.loan_type.purpose_code if loan.loan_type.purpose_code else "", data_format)
                sheet.write(row, col + 5, bank_code if bank_code else "", data_format)
                sheet.write(row, col + 6, loan.employee_id.bank_account_id.acc_number if loan.employee_id.bank_account_id.acc_number else "", data_format)
                sheet.write(row, col + 7, total_amount, data_format)
                row += 1
