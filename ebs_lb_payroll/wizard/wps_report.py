from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError
import xlwt
import base64
import io
import datetime
import csv


class WPSReportWizard(models.TransientModel):
    _name = 'ebs.wps.report.wizard'
    _description = 'WPS Report Wizard'

    hide_batch_id = fields.Boolean(default=False)
    batch_id = fields.Many2one('hr.payslip.run', string="Batch")
    company_id = fields.Many2one('res.partner', 'Company', domain=[('company_partner', '=', True)])
    sponsor_id = fields.Many2one('hr.employee.sponsor', 'Sponsor', required=True)
    file = fields.Binary('Excel Report', readonly=1)
    name = fields.Char('Filename')
    employee_ids = fields.Many2many('hr.employee', string='Employees', domain=[("is_wps", "=", True)])
    config_id = fields.Many2one('ebs.hr.wps.config', string="WPS Config")

    # @api.onchange('company_id')
    # def onchange_company_id(self):
    #     domain = []
    #     #for rec in self:
    #         #domain = [('sponsored_company_id', '=', rec.company_id.id)] if rec.company_id else [('id', 'in', [])]
    #     return {'domain': {'employee_ids': domain}}


    def confirm_button(self):
        if not self.config_id:
            raise UserError("There is no WPS report configuration for this start date")

        else:
            create_datetime = self.create_date + datetime.timedelta(hours=3)
            bank_bic = self.config_id.bank_account_id.bank_id.bic
            if len(bank_bic) > 4:
                bank_bic = bank_bic[:4]
            file_name = 'SIF_' + str(self.sponsor_id.name) + '_' + str(bank_bic) + '_' + str(
                create_datetime.strftime('%Y%m%d')) + '_' + str(create_datetime.time().strftime('%H%M'))
            # file = self.generate_xlsx_report(self.employee_ids)
            csv_file = self.generate_csv_report(self.employee_ids)
            self.write({'name': file_name + '.csv', 'file': csv_file})
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            attachment_id = self.env['ir.attachment'].create({
                'name': file_name + '.csv',
                'type': 'binary',
                'datas': csv_file,
                'public': True,
            })
            download_url = '/web/content/' + str(attachment_id.id) + '?download=true'
            return {
                'type': 'ir.actions.act_url',
                'url': str(base_url) + str(download_url),
                'target': 'new',
            }

    def get_total_employee_salary(self, employees):
        employee_salary = 0
        for rec in employees:
            payslip = self.env['hr.payslip'].sudo().search([('employee_id', '=', rec.id)], order='date_from desc',
                                                           limit=1)
            employee_salary = employee_salary + sum(
                payslip.line_ids.filtered(lambda o: o.code == 'NET').mapped('total'))
        return employee_salary

    def get_employee_payslip_data(self, employee):
        payslip = self.env['hr.payslip'].sudo().search([
            ('employee_id', '=', employee.id), ('payslip_run_id', '=', self.batch_id.id)],
            limit=1)
        if employee.employee_type == 'fusion_employee' or (
                employee.employee_type == 'fos_employee' and not employee.is_labor):
            working_days = 30
        else:
            working_days = payslip.wps_working_days
        result = {
            'extra_hours': 0,
            'payment_type': 'Salary' if self.config_id.template == 'cbq' else 'Normal Payment',
            'notes': payslip.comments,
            'no_working_days': working_days,
        }
        return result, payslip

    def generate_xlsx_report(self, employees):
        """Method to generate xlsx report."""

        employee_data, payslip = self.get_employee_payslip_data(obj)
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('wps_report')
        worksheet.col(0).width = 6000
        worksheet.col(1).width = 6000
        worksheet.col(2).width = 6000
        worksheet.col(3).width = 6000
        worksheet.col(4).width = 6000
        worksheet.col(5).width = 8000
        worksheet.col(6).width = 6000
        worksheet.col(7).width = 8000
        worksheet.col(8).width = 6000
        worksheet.col(9).width = 6000
        worksheet.col(10).width = 6000
        worksheet.col(11).width = 6000
        worksheet.col(12).width = 6000
        worksheet.col(13).width = 6000
        worksheet.col(14).width = 6000
        worksheet.col(15).width = 6000
        worksheet.col(16).width = 6000
        worksheet.col(17).width = 6000
        worksheet.col(18).width = 6000
        worksheet.col(19).width = 6000
        worksheet.col(20).width = 6000
        worksheet.col(21).width = 6000

        font = xlwt.Font()
        font.bold = True
        font.name = 'Arial'
        font.height = 200
        data = xlwt.easyxf('font: name 1; font: height 200')
        format1 = xlwt.easyxf('font: bold 1; font: name 1; font: height 200;')

        row = 0

        worksheet.write(row, 0, 'Employer EID', format1)
        worksheet.write(row, 1, 'File Creation Date', format1)
        worksheet.write(row, 2, 'File Creation Time', format1)
        worksheet.write(row, 3, 'Payer EID', format1)
        worksheet.write(row, 4, 'Payer QID', format1)
        worksheet.write(row, 5, 'Payer Bank Short Name', format1)
        worksheet.write(row, 6, 'Payer IBAN', format1)
        worksheet.write(row, 7, 'Salary Year and Month', format1)
        worksheet.write(row, 8, 'Total Salaries', format1)
        worksheet.write(row, 9, 'Total Records', format1)
        if self.config_id.template == 'qnb':
            worksheet.write(row, 10, 'SIF Version', format1)

        row = row + 1
        create_datetime = self.create_date + datetime.timedelta(hours=3)
        worksheet.write(row, 0, self.sponsor_id.employer_eid, data)
        worksheet.write(row, 1, int(create_datetime.strftime('%Y%m%d')), data)
        worksheet.write(row, 2, int(create_datetime.time().strftime('%H%M')), data)
        worksheet.write(row, 3, self.sponsor_id.payer_eid, data)
        worksheet.write(row, 4, self.sponsor_id.payer_qid, data)
        worksheet.write(row, 5, self.payer_bank_short_name, data)
        worksheet.write(row, 6, self.payer_iban, data)
        worksheet.write(row, 7, int(self.batch_id.date_start.strftime('%Y%m')), data)
        worksheet.write(row, 8, self.get_total_employee_salary(employees), data)
        worksheet.write(row, 9, len(employees), data)
        if self.config_id.template == 'qnb':
            worksheet.write(row, 10, 1, data)

        row = row + 1
        worksheet.write(row, 0, 'Record Sequence', format1)
        worksheet.write(row, 1, 'Employee QID', format1)
        worksheet.write(row, 2, 'Employee Visa ID', format1)
        worksheet.write(row, 3, 'Employee Name', format1)
        worksheet.write(row, 4, 'Employee Bank Short Name', format1)
        worksheet.write(row, 5, 'Employee Account', format1)
        worksheet.write(row, 6, 'Bank Name', format1)
        worksheet.write(row, 7, 'IBAN', format1)
        worksheet.write(row, 8, 'Salary Frequency', format1)
        rule_col = 9
        for line in self.config_id.wps_report_lines:
            # if line.template == 'salary_rules':
            #     for rule in line.rule_ids:
            #         worksheet.write(row, rule_col, rule.name, format1)
            #         rule_col += 1
            # else:
            #     template_string = dict(line._fields['template'].selection).get(line.template)
            worksheet.write(row, rule_col, line.name, format1)
            rule_col += 1
        if self.config_id.template == 'qnb':
            worksheet.write(row, rule_col, 'Housing Allowance', format1)
            rule_col += 1
            worksheet.write(row, rule_col, 'Food Allowance', format1)
            rule_col += 1
            worksheet.write(row, rule_col, 'Transportation Allowance', format1)
            rule_col += 1
            worksheet.write(row, rule_col, 'Over Time Allowance', format1)
            rule_col += 1
            worksheet.write(row, rule_col, 'Deduction Reason Code', format1)
            rule_col += 1
            # worksheet.write(row, rule_col, 'Bank Name', format1)
            # rule_col += 1
            # worksheet.write(row, rule_col, 'IBAN', format1)

        line_row = row + 1
        counter = 1
        for obj in employees:
            employee_data, payslip = self.get_employee_payslip_data(obj)
            worksheet.write(line_row, 0, counter, data)
            worksheet.write(line_row, 1, obj.employee_qid_number or '', data)
            worksheet.write(line_row, 2, '', data)
            worksheet.write(line_row, 3, obj.name or '', data)
            worksheet.write(line_row, 4, obj.bank_account_id.bank_id.bic or '', data)
            worksheet.write(line_row, 5, obj.bank_account_id.iban_no or '', data)
            worksheet.write(line_row, 6, obj.bank_account_id.bank_id.name or '', data)
            worksheet.write(line_row, 7, obj.bank_account_id.iban_no or '', data)
            worksheet.write(line_row, 8, 'M', data)
            rule_col = 9
            for line in self.config_id.wps_report_lines:
                if line.template == 'salary_rules':
                    # for rule in line.rule_ids:
                    amount = sum(
                        payslip.line_ids.filtered(lambda o: o.code in line.rule_ids.mapped('code')).mapped('total'))
                    worksheet.write(line_row, rule_col, amount, data)
                    rule_col += 1
                else:
                    cell_data = employee_data.get(line.template)
                    if line.template == 'notes' and not cell_data:
                        cell_data = ''
                    worksheet.write(line_row, rule_col, cell_data, data)
                    rule_col += 1
            if self.config_id.template == 'qnb':
                worksheet.write(line_row, rule_col, 0, data)
                rule_col += 1
                worksheet.write(line_row, rule_col, 0, data)
                rule_col += 1
                worksheet.write(line_row, rule_col, 0, data)
                rule_col += 1
                worksheet.write(line_row, rule_col, 0, data)
                rule_col += 1
                worksheet.write(line_row, rule_col, 0, data)

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

    def generate_csv_report(self, employees):
        f = io.StringIO()
        writer = csv.writer(f)
        header = ['Employer EID', 'File Creation Date', 'File Creation Time', 'Payer EID', 'Payer QID',
                  'Payer Bank Short Name', 'Payer IBAN', 'Salary Year and Month', 'Total Salaries', 'Total Records']
        if self.config_id.template == 'qnb':
            header.append('SIF Version')
        writer.writerow(header)
        rows = []
        create_datetime = self.create_date + datetime.timedelta(hours=3)
        row_1 = [self.sponsor_id.employer_eid or '', int(create_datetime.strftime('%Y%m%d')),
                 int(create_datetime.time().strftime('%H%M')),
                 self.sponsor_id.payer_eid or '', self.sponsor_id.payer_qid or '',
                 self.sponsor_id.payer_bank_short_name or '', self.sponsor_id.payer_iban or '',
                 int(self
                     .batch_id.date_start.strftime('%Y%m')), self.get_total_employee_salary(employees), len(employees)]
        if self.config_id.template == 'qnb':
            row_1.append(1)
        rows.append(row_1)

        row_2 = ['Record Sequence', 'Employee QID', 'Employee Visa ID', 'Employee Name', 'Employee Bank Short Name',
                 'Employee Account', 'Salary Frequency']
        for line in self.config_id.wps_report_lines:
            row_2.append(line.name)
        rows.append(row_2)

        counter = 1
        for obj in employees:
            employee_data, payslip = self.get_employee_payslip_data(obj)
            emp_row = [counter, obj.employee_qid_number or '', '', obj.name or '', obj.bank_account_id.bank_id.bic or '',
                       obj.bank_account_id.iban_no or '', 'M']
            for line in self.config_id.wps_report_lines:
                if line.template == 'salary_rules':
                    amount = sum(
                        payslip.line_ids.filtered(lambda o: o.code in line.rule_ids.mapped('code')).mapped('total'))
                    if amount < 0:
                        amount = -amount
                    emp_row.append(amount)
                else:
                    cell_data = employee_data.get(line.template)
                    if line.template == 'notes' and not cell_data:
                        cell_data = ''
                    emp_row.append(cell_data)

            counter += 1
            rows.append(emp_row)
        writer.writerows(rows)
        f.seek(0)
        data = f.read()
        f.close()
        res = base64.b64encode(data.encode('utf-8'))
        return res
