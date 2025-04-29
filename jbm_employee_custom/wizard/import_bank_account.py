import csv
import pytz
from odoo import api, fields, models, _
import base64
from odoo.exceptions import ValidationError
from datetime import datetime
import xlrd
import tempfile


class BankAccountImport(models.TransientModel):
    _name = "import.bank.account"

    data_file = fields.Binary(string='')
    temp_file = fields.Binary(string='')
    type = fields.Selection(
        [('employee_bank', 'Import Employees Bank Accounts')],
        string="Operation",
        default='employee_bank', required=True)
    file_name = fields.Char('Filename')

    def _check_csv(self, data_file):
        return data_file.strip().endswith('.csv')

    def _check_excel(self, data_file):
        return data_file.strip().endswith('.xlsx')


    def import_file(self):
        if self.type == "employee_bank":
            if self.file_name:
                if not self._check_excel(self.file_name):
                    raise ValidationError(_('Unsupported file format, Import only supports XLSX'))
                return self.import_data_csv()
            else:
                raise ValidationError(_('Please Select the XLSX file'))
    def import_data_csv(self):
        if self.type == 'employee_bank':
            not_registered_employees = []
            if not self.data_file:
                raise ValidationError('Please Select the XLSX file')

            # print('111')
            file_path = tempfile.gettempdir() + '/file.xlsx'
            f = open(file_path, 'wb')
            data = self.data_file
            f.write(base64.b64decode(data))
            f.close()
            workbook = xlrd.open_workbook(file_path, on_demand=True)
            worksheet = workbook.sheet_by_index(0)
            if not worksheet.cell_value(1, 0):
                raise ValidationError('Please Select the correct Template to upload')

            for row in range(1, worksheet.nrows):
                try:
                    emp_number = int(float(worksheet.cell_value(row, 0)))
                except:
                    raise ValidationError(f'Employee number at row number: {row} is empty')

                emp_name = worksheet.cell_value(row, 1)
                acc_number = str(worksheet.cell_value(row, 2))
                acc_type = str(worksheet.cell_value(row, 3))
                acc_type_code = worksheet.cell_value(row, 4)
                bank_name = worksheet.cell_value(row, 5)
                iban_no = str(worksheet.cell_value(row, 6))
                branch = worksheet.cell_value(row, 7)
                swift_code = str(worksheet.cell_value(row, 8))
                comments = worksheet.cell_value(row, 10)
                if worksheet.cell_value(row, 9):
                    try:
                        opened_since = datetime(
                            *xlrd.xldate_as_tuple(worksheet.cell_value(row, 8), workbook.datemode)).date()
                    except ValueError:
                        pass

                employee = self.env['hr.employee'].search(
                    [('registration_number', '=', emp_number)], limit=1)

                address = self.env['res.partner'].search([('name', '=', employee.name)], limit=1)
                bank = self.env['res.bank'].search([('name', '=', bank_name)], limit=1)
                account_type = self.env['account.type'].search(['|',('name', '=', acc_type), ('code', '=', acc_type_code)], limit=1)
                if not len(address):
                    address.create({
                        'name': employee.name
                    })
                    address = self.env['res.partner'].search([('name', '=', employee.name)], limit=1)
                if not len(bank):
                    bank.create({
                        'name': bank_name
                    })
                if not len(account_type):
                    account_type = account_type.create({
                        'name': acc_type,
                        'code': acc_type_code
                    })
                res = {
                    'acc_number': acc_number,
                    'partner_id': address.id,
                    'bank_id': bank.id,
                    'employee_id': employee.id,
                    'iban_no': iban_no,
                    'branch': branch,
                    'swift_code': swift_code,
                    'account_type_id': account_type.id,
                    'comments': comments,
                }
                employee_bank_account = self.env['res.partner.bank'].create(res)
                if len(employee):

                    bank_account_data = {
                        'address_home_id': address.id,
                        'bank_account_id': employee_bank_account.id,
                    }
                    employee.write(bank_account_data)
                    self.env.cr.commit()

                else:
                    not_registered_employees.append(emp_number)
            if len(not_registered_employees):
                raise ValidationError(_('This Employee(s) ( %s ) does/do not exist') % not_registered_employees)


    @api.model
    def get_create_bank_account(self, employee_id, bank_name, account_number):
        if self.type == "employee_bank":
            if account_number and bank_name:
                bank = self.env['res.bank'].search([('name', '=', bank_name)])
                if len(bank) == 0:
                    bank = self.env['res.bank'].create({'name': bank_name})
                else:
                    bank = bank[0]
                partner = self.env['res.partner'].search([('name', '=', employee_id.name)])
                if len(partner) == 0:
                    partner = self.env['res.partner'].create({'name': employee_id.name})
                else:
                    partner = partner[0]
                if employee_id:
                    res_partner_bank = self.env['res.partner.bank'].create(
                        {
                            'acc_number': account_number,
                            'bank_id': bank.id,
                            'partner_id': partner.id
                        }
                    )

                    emp_bank_account = employee_id.write(
                        {
                            'bank_account_id': res_partner_bank.id,
                            'address_home_id': partner.id
                        }
                    )
                    return emp_bank_account

        else:
            return None

