from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError
import xlwt
import base64
import io


# datetime.date(2021, 11, calendar.monthrange(2021, 11)[-1])
class SalaryReportWizard(models.TransientModel):
    _name = 'ebs.salary.report.wizard'
    _description = 'Salary Report Wizard'

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    company_id = fields.Many2one('res.company', 'Company')
    employee_ids = fields.Many2many('hr.employee', string='Employees')
    file = fields.Binary('Excel Report', readonly=1)
    name = fields.Char('Filename')

    @api.onchange('company_id')
    def onchange_company_id(self):
        for rec in self:
            if rec.company_id:
                employees = self.env['hr.employee'].search([('company_id', '=', rec.company_id.id)])
                return {
                    'domain': {
                        'employee_ids': [('id', 'in', employees.ids)]
                    }
                }
            else:
                return {
                    'domain': {
                        'employee_ids': [],
                    }
                }

    def confirm_button(self):
        if not self.employee_ids:
            if self.company_id:
                employees = self.env['hr.employee'].search(
                    [('company_id', '=', self.company_id.id), ('employee_type', '=', 'fusion_employee')])
            else:
                employees = self.env['hr.employee'].search([('employee_type', '=', 'fusion_employee')])
        else:
            employees = self.employee_ids
        report_config_id = self.env['ebs.hr.salary.report'].search(
            [
                ('start_date', '<=', self.start_date),
                ('end_date', '>=', self.start_date)
            ]
            , limit=1)
        if not report_config_id:
            raise UserError("There is no salary report configuration for this start date")

        else:
            employee_payslips = self.env['hr.payslip'].search([('employee_id', 'in', employees.ids),
                                                           ('date_from', '>=', self.start_date),
                                                           ('date_from', '<=', self.end_date),
                                                           ('date_to', '<=', self.end_date),
                                                           ('date_to', '>=', self.start_date)])
            file = self.generate_xlsx_report(employees, report_config_id, employee_payslips)
            self.write({'name': 'Payroll Report '+self.start_date.strftime('%d/%m/%Y')+'.xls', 'file': file})
            base_url = self.env['ir.config_parameter'].get_param('web.base.url')
            attachment_id = self.env['ir.attachment'].create({
                'name': 'Payroll Report '+self.start_date.strftime('%d/%m/%Y')+'.xls',
                'type': 'binary',
                'datas': file,
                'public': True,
            })
            download_url = '/web/content/' + str(attachment_id.id) + '?download=true'
            return {
                'type': 'ir.actions.act_url',
                'url': str(base_url) + str(download_url),
                'target': 'new',
            }

    def generate_xlsx_report(self, employees, report_config_id, payslips):
        """Method to generate xlsx report."""
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('salary_report')
        worksheet.col(0).width = 7000
        worksheet.col(2).width = 8000
        worksheet.col(3).width = 7000
        worksheet.col(4).width = 7000
        worksheet.col(5).width = 5000
        worksheet.col(6).width = 5000
        worksheet.col(7).width = 5000
        worksheet.col(8).width = 5000
        worksheet.col(9).width = 5000

        font = xlwt.Font()
        font.bold = True
        font.name = 'Arial'
        font.height = 200
        # pattern = xlwt.Pattern()
        tot = xlwt.easyxf('font: bold 1; font: name 1; font: height 300')
        border = xlwt.easyxf('font: bold 1; font: name 1; font: height 200')
        format1 = xlwt.easyxf('font: bold 1; font: name 1; font: height 200')

        row = 0

        worksheet.write(row, 0, 'Company', format1)
        worksheet.write(row, 1, 'QID No.', format1)
        worksheet.write(row, 2, 'Name', format1)
        worksheet.write(row, 3, 'Bank', format1)
        worksheet.write(row, 4, 'IBAN No.', format1)
        worksheet.write(row, 5, 'For recording', format1)
        col_count = 6
        for line in report_config_id.salary_report_lines:
            worksheet.write(row, col_count, line.name, format1)
            col_count += 1
        worksheet.write(row, col_count, 'Salary Status', format1)
        col_count += 1
        worksheet.write(row, col_count, 'Salary Date', format1)
        col_count += 1
        worksheet.write(row, col_count, 'MP or FOS', format1)
        col_count += 1

        line_row = row + 1
        line_col = 0
        counter = 1
        for obj in employees:
            # worksheet.write(line_row, line_col, counter, border)
            # line_col += 1
            worksheet.write(line_row, line_col, obj.company_id.name or '', border)
            line_col += 1
            worksheet.write(line_row, line_col, '', border)
            line_col += 1
            worksheet.write(line_row, line_col, obj.name or '', border)
            line_col += 1
            worksheet.write(line_row, line_col, obj.bank_account_id.acc_number or '', border)
            line_col += 1
            worksheet.write(line_row, line_col, obj.bank_account_id.iban_no or '', border)
            line_col += 1
            worksheet.write(line_row, line_col, '', border)
            line_col += 1
            for line in report_config_id.salary_report_lines:
                rule_ids = line.rule_ids
                total = 0
                for payslip in payslips:
                    payslip_lines = payslip.line_ids.search([('salary_rule_id', 'in', rule_ids.ids),
                                                             ('slip_id', '=', payslip.id),
                                                             ('employee_id', '=', obj.id)])
                    for line in payslip_lines:
                        total += line.total
                worksheet.write(line_row, line_col, total, border)
                line_col += 1
            worksheet.write(line_row, line_col, '', border)
            line_col += 1
            worksheet.write(line_row, line_col, self.start_date.strftime("%d/%m/%Y"), border)
            line_col += 1
            worksheet.write(line_row, line_col, '', border)
            line_col += 1
            line_col = 0
            line_row += 1
            counter += 1

        row += 5
        fp = io.BytesIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        res = base64.encodestring(data)
        return res
