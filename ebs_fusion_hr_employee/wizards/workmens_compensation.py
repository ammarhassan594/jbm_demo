from odoo import api, fields, models
import base64
import io
import xlsxwriter
from dateutil.relativedelta import relativedelta
from datetime import date, datetime


class WorkmensCompensation(models.TransientModel):
    _name = 'insurance.workmens.compensation'
    _description = 'Insurance Workmens Compensation Report'

    binary_data = fields.Binary("File")

    def button_confirm(self):
        model = self._context.get('active_model')
        employee_ids = self.env[model].browse(self.env.context.get('active_ids'))
        if 'addition' in self._context:
            header = 'ADDITION'
            filename = 'Insurance: Workmens Compensation Addition.xlsx'
        else:
            header = 'DELETION'
            filename = 'Insurance: Workmens Compensation Deletion.xlsx'
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet(header)

        row = 0
        for rec in range(32):
            worksheet.set_column(0, rec, 15)

        table_header = workbook.add_format({'bold': True, 'border': 1, 'align': 'center', })

        worksheet.merge_range('A1:K1', "FUSION OUTSOURCING SERVICES", table_header)
        worksheet.merge_range('A2:K2', "%s as on %s" % (header, date.today().strftime('%d/%m/%Y')), table_header)
        worksheet.write(2, 0, 'S.NO.', table_header)
        worksheet.write(2, 1, 'NAME', table_header)
        worksheet.write(2, 2, 'DESIGNATION', table_header)
        worksheet.write(2, 3, 'BASIC SALARY', table_header)
        worksheet.write(2, 4, 'RELATION', table_header)
        worksheet.write(2, 5, 'DOB', table_header)
        worksheet.write(2, 6, 'GENDER', table_header)
        worksheet.write(2, 7, 'NATIONALITY', table_header)
        worksheet.write(2, 8, 'MARITAL STATUS', table_header)
        worksheet.write(2, 9, 'QID/VISA NO.', table_header)
        worksheet.write(2, 10, 'MOBILE.NO', table_header)

        i = 3
        count = 1
        for employee in employee_ids:

            worksheet.write(i, 0, count)
            count += 1
            if employee.qid_no:
                emp_no = employee.qid_no
            elif employee.visa_no:
                emp_no = employee.visa_no
            else:
                emp_no = ''
            worksheet.write(i, 1, employee.name)
            worksheet.write(i, 2, str(employee.job_id.name) if employee.job_id else '')
            worksheet.write(i, 3, str(employee.emp_wage) if employee.emp_wage else '')
            worksheet.write(i, 4, 'Principal')
            worksheet.write(i, 5, employee.birthday.strftime('%d/%m/%Y') if employee.birthday else "")
            worksheet.write(i, 6, "M" if employee.gender == 'male' else "F")
            worksheet.write(i, 7, str(employee.nationality_id.name) if employee.nationality_id else '')
            worksheet.write(i, 8, str(employee.marital).capitalize() if employee.marital else '')
            worksheet.write(i, 9, str(emp_no))
            worksheet.write(i, 10, str(employee.phone_personal) if employee.phone_personal else '')

            i += 1
        #
        workbook.close()
        output.seek(0)
        output = base64.encodestring(output.read())
        self.write({'binary_data': output})
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=insurance.workmens.compensation&field=binary_data&download=true&id=%s&filename=%s' % (
                self.id, filename),
            'target': 'new',
        }
