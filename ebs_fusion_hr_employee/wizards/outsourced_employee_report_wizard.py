from odoo import fields, models, api
import base64
import io
import xlsxwriter
from datetime import date, datetime
from dateutil.relativedelta import relativedelta


class OutsourcedEmployeeReportWizard(models.TransientModel):
    _name = 'outsourced.employee.report.wizard'
    _description = 'Outsourced Employee Report Wizard'

    report_template = fields.Selection([
        ('outsourced_qid_report', 'Outsourced RP Expiry Date Report'),
        ('outsourced_national_address_report', 'Outsourced National Address Report'),
    ], string='Report Template')
    binary_data = fields.Binary(string='File')

    def button_confirm(self):
        if self.report_template == 'outsourced_qid_report':
            return self.get_outsourced_qid_report()
        if self.report_template == 'outsourced_national_address_report':
            return self.get_outsourced_national_address_report()

    def get_outsourced_qid_report(self):
        filename = 'Outsourced RP Expiry Date Report.xlsx'
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        header_format = workbook.add_format({'bold': True})
        date_format = workbook.add_format({'num_format': 'dd/mm/yyy'})
        worksheet = workbook.add_worksheet('Outsourced RP Expiry Date Report')
        for rec in range(9):
            worksheet.set_column(rec, 1, 20)
        row = 0
        worksheet.write(row, 0, 'Client/Company', header_format)
        worksheet.write(row, 1, 'Account Manager', header_format)
        worksheet.write(row, 2, 'Qid No.', header_format)
        worksheet.write(row, 3, 'Name', header_format)
        worksheet.write(row, 4, 'Nationality', header_format)
        worksheet.write(row, 5, 'Gender', header_format)
        worksheet.write(row, 6, 'RP Expiry Date', header_format)
        worksheet.write(row, 7, 'Status', header_format)
        worksheet.write(row, 8, 'National Address Registered?', header_format)
        row += 1

        expiry_date = date.today() + relativedelta(months=3)
        fos_employee_ids = self.env['hr.employee'].search(
            [('employee_type', '=', 'fos_employee')]).filtered(
            lambda o: o.qid_expiry_date and o.qid_expiry_date <= expiry_date).sorted('qid_expiry_date')
        if fos_employee_ids:
            for employee in fos_employee_ids:
                worksheet.write(row, 0, employee.partner_parent_id.name or '')
                worksheet.write(row, 1, employee.partner_parent_id.client_account_manager_id.name or '')
                worksheet.write(row, 2, employee.qid_no or '')
                worksheet.write(row, 3, employee.name or '')
                worksheet.write(row, 4, employee.nationality_id.name or '')
                worksheet.write(row, 5, dict(employee._fields['gender'].selection).get(employee.gender))
                worksheet.write_datetime(row, 6, employee.qid_expiry_date if employee.qid_expiry_date else '',
                                         date_format)
                worksheet.write(row, 7,
                                dict(employee._fields['outsourced_status'].selection).get(employee.outsourced_status))
                worksheet.write(row, 8, 'Yes' if employee.have_national_address else 'No')
                row += 1

        workbook.close()
        output.seek(0)
        output = base64.encodestring(output.read())
        if self._context.get('mail_attachment'):
            return self.get_report_attachment(filename, output)
        self.write({'binary_data': output})
        return self.download_file(filename)

    def get_outsourced_national_address_report(self):
        filename = 'Outsourced National Address Report.xlsx'
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        header_format = workbook.add_format({'bold': True})
        worksheet = workbook.add_worksheet('Outsourced National Address Report')
        for rec in range(9):
            worksheet.set_column(rec, 1, 20)
        row = 0
        worksheet.write(row, 0, 'Client/Company', header_format)
        worksheet.write(row, 1, 'Account Manager', header_format)
        worksheet.write(row, 2, 'Qid No.', header_format)
        worksheet.write(row, 3, 'Name', header_format)
        worksheet.write(row, 4, 'Nationality', header_format)
        worksheet.write(row, 5, 'Gender', header_format)
        worksheet.write(row, 6, 'RP Expiry Date', header_format)
        worksheet.write(row, 7, 'Status', header_format)
        worksheet.write(row, 8, 'National Address Registered?', header_format)
        row += 1

        fos_employee_ids = self.env['hr.employee'].search(
            [('employee_type', '=', 'fos_employee'), ('have_national_address', '=', False), (
            'outsourced_status', 'not in',
            ['visa_ready_to_use', 'onboarding', 'potential_candidate', 'work_multi_entry', 'work_permit',
             'inside_country_mev'])])
        if fos_employee_ids:
            for employee in fos_employee_ids:
                worksheet.write(row, 0, employee.partner_parent_id.name or '')
                worksheet.write(row, 1, employee.partner_parent_id.client_account_manager_id.name or '')
                worksheet.write(row, 2, employee.qid_no or '')
                worksheet.write(row, 3, employee.name or '')
                worksheet.write(row, 4, employee.nationality_id.name or '')
                worksheet.write(row, 5, dict(employee._fields['gender'].selection).get(employee.gender))
                worksheet.write(row, 6, datetime.strftime(employee.qid_expiry_date,
                                                          '%d/%m/%Y') if employee.qid_expiry_date else '')
                worksheet.write(row, 7,
                                dict(employee._fields['outsourced_status'].selection).get(employee.outsourced_status))
                worksheet.write(row, 8, 'Yes' if employee.have_national_address else 'No')
                row += 1

        workbook.close()
        output.seek(0)
        output = base64.encodestring(output.read())
        if self._context.get('mail_attachment'):
            return self.get_report_attachment(filename, output)
        self.write({'binary_data': output})
        return self.download_file(filename)

    def get_report_attachment(self, filename, output):
        if self._context.get('mail_attachment'):
            attachment_id = self.env['ir.attachment'].create({
                'name': filename,
                'type': 'binary',
                'datas': output,
                'public': True,
            })
            return attachment_id

    def download_file(self, filename):
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=outsourced.employee.report.wizard&field=binary_data&download=true&id=%s&filename=%s' % (
                self.id, filename),
            'target': 'new',
        }
