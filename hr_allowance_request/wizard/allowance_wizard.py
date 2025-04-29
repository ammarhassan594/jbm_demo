from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
from odoo.tools.date_utils import end_of


class AllowanceRequestWizard(models.TransientModel):
    _name = 'allowance.request.wizard'

    allowance_type_ids = fields.Many2many('allowance.type', required=True)

    start_date = fields.Date(default=fields.Date.today(), string="Start Date", required=True)
    end_date = fields.Date(default=end_of(fields.Date.today(), 'month'), string="End Date", required=True)
    include_loan = fields.Boolean(string="Include Loans")
    pay = fields.Boolean(string="Pay")

    def action_generate_report_excel(self):
        if self.allowance_type_ids and self.start_date and self.end_date:
            allowances = self.env['allowance.request'].search([
                ('allowance_type', 'in', self.allowance_type_ids.ids),
                ('state', '=', 'approved'),
                ('date', '>=', self.start_date),
                ('date', '<=', self.end_date),
            ])
            data = {
                'allowances': allowances.ids,
                'start_date': self.start_date,
                'end_date': self.end_date,
            }

            loans = None
            if self.include_loan:
                loans = self.env['hr.loan'].search([
                    ('state', '=', 'approve'),
                    ('date', '>=', self.start_date),
                    ('date', '<=', self.end_date),
                ])
                data["loans"] = loans.ids

            if self.pay:
                for allowance in allowances:
                    if allowance.allowance_type.paid_seperator:
                        allowance.sudo().write({'state': 'paid'})
                if self.include_loan:
                    for loan in loans:
                        loan.sudo().action_paid()
            return self.env.ref('hr_allowance_request.action_allowance_request_xlsx_report').report_action(self,
                                                                                                               data=data)

    @api.constrains('start_date', 'end_date')
    def _check_date(self):
        if self.end_date and self.start_date and self.start_date > self.end_date:
            raise ValidationError(_('Invalid start date'))


class AllowanceRequestExcelReport(models.AbstractModel):
    _name = 'report.hr_allowance_request.request_allowance_xlsx_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, partners):
        sheet = workbook.add_worksheet('Allowance Request Report')
        data_format = workbook.add_format({'align': 'center'})
        header_row_style = workbook.add_format({'bold': True, 'align': 'center', 'border': True})
        date_format = workbook.add_format({'num_format': 'd-m-yyyy', 'align': 'center'})

        allowances = self.env['allowance.request'].sudo().search([('id', 'in', data.get('allowances'))], order='id desc')
        loans = self.env['hr.loan'].browse(data.get('loans'))

        row = 0
        col = 0
        if allowances:
            sheet.set_column(1, 2, 25)
            sheet.set_column(3, 4, 15)
            sheet.set_column(6, 6, 35)
            sheet.write(row, col, 'Employee Number', header_row_style)
            sheet.write(row, col + 1, 'Employee Name', header_row_style)
            sheet.write(row, col + 2, 'Type', header_row_style)
            sheet.write(row, col + 3, 'Date', header_row_style)
            sheet.write(row, col + 4, 'Purpose Code', header_row_style)
            sheet.write(row, col + 5, 'Bank Code', header_row_style)
            sheet.write(row, col + 6, 'IBAN No', header_row_style)
            sheet.write(row, col + 7, 'Amount', header_row_style)
            row += 1
            allowance_dict = {}
            for allowance in allowances:
                if allowance_dict.get((allowance.employee_id.id, allowance.allowance_type)):
                    allowance_dict.get((allowance.employee_id.id, allowance.allowance_type)).append(allowance)
                else:
                    allowance_dict.update({(allowance.employee_id.id, allowance.allowance_type): [allowance]})

            for allowance in allowance_dict.values():
                bank_code = None
                u_code = None
                if allowance[0].mapped('employee_id').bank_account_id.bank_id.bic:
                    bank_code = allowance[0].mapped('employee_id').bank_account_id.bank_id.bic
                if allowance[0].mapped('allowance_type').u_code:
                    u_code = allowance[0].mapped('allowance_type').u_code
                sheet.write(row, col, allowance[0].mapped('employee_id').registration_number if allowance[0].mapped('employee_id').registration_number else "",
                            data_format)
                sheet.write(row, col + 1, allowance[0].mapped('employee_id').name if allowance[0].mapped('employee_id').name else "", data_format)
                sheet.write(row, col + 2, allowance[0].mapped('allowance_type').name if allowance[0].mapped('allowance_type').name else "",
                            data_format)
                sheet.write(row, col + 3, allowance[0].mapped('date')[0] if allowance[0].mapped('date')[0] else "", date_format)
                sheet.write(row, col + 4, u_code if u_code else "", data_format)
                sheet.write(row, col + 5, bank_code if bank_code else "", data_format)
                sheet.write(row, col + 6, allowance[0].mapped('employee_id').bank_account_id.acc_number if allowance[0].mapped('employee_id').bank_account_id.acc_number else "",
                            data_format)
                amount_sum = []
                for rec in allowance:
                    if allowance[0].mapped('allowance_type').code == 'education':
                        amount_sum.append(rec.total_requested_amount)
                    else:
                        amount_sum.append(rec.eligible_amount)
                sheet.write(row, col + 7, sum(amount_sum), data_format)
                row += 1
        row += 2
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
