from odoo import api, fields, models
import base64
import io
import xlsxwriter
from dateutil.relativedelta import relativedelta
from datetime import date, datetime


class PayCard(models.TransientModel):
    _name = 'pay.card'
    _description = 'Pay Card Report'

    binary_data = fields.Binary("File")

    def button_confirm(self):
        model = self._context.get('active_model')
        employee_ids = self.env[model].browse(self.env.context.get('active_ids'))
        filename = 'PayCard.xlsx'
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('PayCard')

        row = 0
        for rec in range(32):
            worksheet.set_column(0, rec, 30)

        table_header = workbook.add_format({'bold': True, 'border': 1, 'align': 'center', 'bg_color': '#69d1cf'})
        table_header_red = workbook.add_format({'bold': True, 'border': 1, 'align': 'center', 'bg_color': '#ff0000'})

        worksheet.merge_range('A1:A3', 'SL.NO.', table_header)
        worksheet.merge_range('B1:B3', 'CARD NUMBER (For Bank Use Only) ', table_header_red)
        worksheet.merge_range('C1:C3', 'TITLE (5)', table_header)
        worksheet.merge_range('D1:D3', 'LAST NAME   (50)   Characters', table_header)
        worksheet.merge_range('E1:E3', 'FIRST NAME   (50)    Characters', table_header)
        worksheet.merge_range('F1:F3', 'NATIONALITY   (30)  Characters', table_header)
        worksheet.merge_range('G1:G3', 'Resident (Y or N )', table_header)
        worksheet.merge_range('H1:H3', 'QID No.', table_header)
        worksheet.merge_range('I1:I3', 'QID Expiry Date', table_header)
        worksheet.merge_range('J1:J3', 'Passport No', table_header)
        worksheet.merge_range('K1:K3', 'Pass Expiry Date', table_header)
        worksheet.merge_range('L1:L3', 'Passport Issued Country', table_header)
        worksheet.merge_range('M1:M3', ' Visa Number', table_header)
        worksheet.merge_range('N1:N3',
                              "EMBOSSING NAME (25) No. of characters shouldn't be more than 25 including spaces ",
                              table_header)
        worksheet.merge_range('O1:O3', 'DOB  DD/MM/YYYY   ', table_header)
        worksheet.merge_range('P1:P3', 'Country of Birth', table_header)
        worksheet.merge_range('Q1:Q3', 'SEX M / F', table_header)
        worksheet.merge_range('R1:R3', 'EMPLOYER   (50)  Characters', table_header)
        worksheet.merge_range('S1:S3', 'P.O.BOX', table_header)
        worksheet.merge_range('T1:T3', 'DEPARTMENT (30) Characters', table_header)
        worksheet.merge_range('U1:U3', 'POSITION (30) Characters', table_header)
        worksheet.merge_range('V1:V3', 'STAFF NO (15)', table_header)
        worksheet.merge_range('W1:W3', 'OFFICE TEL (20)', table_header)
        worksheet.merge_range('X1:X3', 'HOME TEL  (20)', table_header)
        worksheet.merge_range('Y1:Y3', 'MOBILE  (20)', table_header)
        worksheet.merge_range('Z1:Z3', 'Salar Amount', table_header)
        worksheet.merge_range('AA1:AA3', 'IS EMPLOYMENT TENURE GREATER THAN 1 YEAR?', table_header)
        worksheet.merge_range('AB1:AB3',
                              'DEALING WITH SANCTION COUNTRY. Enter Iran or Syria or North Korea or Not applicable',
                              table_header)
        worksheet.merge_range('AC1:AC3', 'RELATIONSHIP WITH SANCTION COUNTRY. Enter Resident or Citizen or Others',
                              table_header)
        worksheet.merge_range('AD1:AD3', 'IF RELATIONSHIP IS OTHERS. SPECIFY DETAILS', table_header)
        worksheet.merge_range('AE1:AE3', 'CO. CODE(For Bank Use Only)', table_header_red)
        worksheet.merge_range('AF1:AF3', 'Particulars (For Bank Use Only)', table_header_red)
        i = 3
        count = 1
        for employee in employee_ids:
            lastname = str(employee.name.split(' ')[-1]) if employee.name and len(
                employee.name.split(' ')) >= 0 else str(employee.name.split(' ')[-2])
            firstname = " ".join(employee.name.split(' ')[0:-1]) if employee.name else ""
            worksheet.write(i, 0, count)
            count += 1
            worksheet.write(i, 1, "")
            worksheet.write(i, 2,
                            str(employee.title.name) if employee.title else "")  # Title: title from employee profile
            worksheet.write(i, 3, lastname)  # Last Name: split name by space and take the last element in array
            worksheet.write(i, 4, firstname) or ''  # name: split name by space and take every element beside the last
            worksheet.write(i, 5,
                            str(employee.nationality_id.name) if employee.nationality_id else "")  # nationality: from employee profile
            worksheet.write(i, 6, 'Y' if (
                        employee.qid_no or employee.visa_type.name == 'Work - Yearly Resident') else "N")  # resident: Y if qid available else N
            worksheet.write(i, 7, str(employee.qid_no) if employee.qid_no else "")  # QID no
            worksheet.write(i, 8, employee.qid_expiry_date.strftime(
                "%d/%m/%Y") if employee.qid_expiry_date else "")  # qid expiry date
            worksheet.write(i, 9, str(employee.passport_no) if employee.passport_no else "")  # passport no
            worksheet.write(i, 10,
                            employee.passport_expiry_date.strftime(
                                "%d/%m/%Y") if employee.passport_expiry_date else "")  # pass expi date
            worksheet.write(i, 11,
                            str(employee.passport_country.name) if employee.passport_country else "")  # passport issued country from passport
            worksheet.write(i, 12,
                            str(employee.visa_no) if employee.visa_no else "")  # visa number if QID available leave blank
            worksheet.write(i, 13, str(employee.name) if employee.name else "")  # Name: all the name
            worksheet.write(i, 14, employee.birthday.strftime(
                '%d/%m/%Y') if employee.birthday else "")  # DOB with format DD/MM/YYYY
            worksheet.write(i, 15,
                            str(employee.country_of_birth.name) if employee.country_of_birth else "")  # country of birth: nationality
            worksheet.write(i, 16, "M" if employee.gender == 'male' else "F")  # gender: M or F
            worksheet.write(i, 17,
                            str(employee.sponsored_company_id.name) if employee.sponsored_company_id else "")  # employer: FUSION OUTSOURCING AND SERVICES
            worksheet.write(i, 18, '14383')  # PO BOX: 14383
            worksheet.write(i, 19, "OPERATIONS")  # DEPARTMENT: OPERATIONS
            worksheet.write(i, 20,
                            str(employee.qid_job_position_id.name) if employee.qid_job_position_id else employee.job_id.name or "")  # Position: from employee profile
            worksheet.write(i, 21,
                            (employee.qa_staff_no or '') if employee.partner_parent_id.abbreviation == 'QA' else str(
                                employee.sequence))  # Staff NO from employee profile
            worksheet.write(i, 22, "40120300")  # office tel::40120300
            worksheet.write(i, 23, "40120300")  # home tel: 40120300
            worksheet.write(i, 24,
                            str(employee.phone_personal) if employee.phone_personal else '')  # mobile: from employee profile
            worksheet.write(i, 25,
                            str(employee.emp_package) if employee.emp_package else 0.0)  # salary amount is the package
            worksheet.write(i, 26, 'Y' if employee.time_hired_in_no >= 1 else 'N')  # employment tenure : Y
            worksheet.write(i, 27, 'Applicable'
            if employee.nationality_id.name == 'Syria' or employee.nationality_id.name == 'North Korea' or employee.nationality_id.name == 'Iran' else 'Not Applicable')  # dealing with sanction countries if nationality is Syria or north korea or iran: Applicable else not applicable
            worksheet.write(i, 28, 'Citizen'
            if employee.nationality_id.name == 'Syria' or employee.nationality_id.name == 'North Korea' or employee.nationality_id.name == 'Iran' else '')  # rlationship with sanctioned countries: if previous applicable put citizen
            worksheet.write(i, 29, '')  # relation ship is other: leave blank
            worksheet.write(i, 30, '')  # CO code: leave blank
            worksheet.write(i, 31, '')  # Particulars: leave blank

            i += 1

        workbook.close()
        output.seek(0)
        output = base64.encodestring(output.read())
        self.write({'binary_data': output})
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=pay.card&field=binary_data&download=true&id=%s&filename=%s' % (
                self.id, filename),
            'target': 'new',
        }
