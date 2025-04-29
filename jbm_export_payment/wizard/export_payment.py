# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import xlsxwriter
import base64
import io


class ExportPayment(models.TransientModel):
    _name = 'export.payment'

    bank_account_id = fields.Many2one('res.partner.bank', string="Account Number")
    date = fields.Date(string="Date")
    binary_data = fields.Binary("File")

    def generate_payment(self):
        filename = 'Payments.xlsx'
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Payments')
        info_format = workbook.add_format({'align': 'left', 'valign': 'vcenter', 'bold': True, 'font_size': 12})
        journal_ids = self.env['account.journal'].sudo().search([('bank_account_id', '=', self.bank_account_id.id)])
        payments = self.env['account.payment']
        for journal_id in journal_ids:
            payments += self.env['account.payment'].sudo().search([
                ('journal_id', '=', journal_id.id), ('date', '=', self.date),
                 ('payment_method_line_id.payment_method', '!=', 'check')
            ])
        row = 0
        worksheet.set_column(0, 0, 30)
        worksheet.set_column(1, 1, 50)
        worksheet.set_column(2, 12, 15)
        worksheet.write(row, 0, 'Transaction Code', info_format)
        worksheet.write(row, 1, 'LBT')
        row += 1
        worksheet.write(row, 0, 'Account No', info_format)
        worksheet.write(row, 1, self.bank_account_id.acc_number)
        row += 1
        worksheet.write(row, 0, 'Value Date', info_format)
        worksheet.write(row, 1, self.date.strftime('%d-%m-%y'))
        row += 1
        worksheet.write(row, 0, 'File Reference Number', info_format)
        worksheet.write(row, 1, 'MIXED 125')
        row += 1
        worksheet.write(row, 0, 'Num Transactions', info_format)
        worksheet.write(row, 1, str(len(payments)))
        row += 1
        worksheet.write(row, 0, 'Row Number', info_format)
        worksheet.write(row, 1, 'Account Number / IBAN', info_format)
        worksheet.write(row, 2, 'Amount', info_format)
        worksheet.write(row, 3, 'Bank Code', info_format)
        worksheet.write(row, 4, 'Bank Name', info_format)
        worksheet.write(row, 5, 'Branch Name', info_format)
        worksheet.write(row, 6, 'Bank Address', info_format)
        worksheet.write(row, 7, 'Beneficiary Name', info_format)
        worksheet.write(row, 8, 'Description', info_format)
        worksheet.write(row, 9, 'Phone number', info_format)
        worksheet.write(row, 10, 'Bank Charges', info_format)
        worksheet.write(row, 11, 'Include-Exclude Charger', info_format)
        worksheet.write(row, 12, 'Purpose Of Transfer', info_format)
        count = 0
        for payment in payments.filtered(lambda pay: pay.journal_id.type == 'bank'):
            count += 1
            row += 1
            bank_address = ''
            if payment.partner_bank_id.bank_id and payment.partner_bank_id.bank_id.street:
                bank_address += payment.partner_bank_id.bank_id.street + ','
            if payment.partner_bank_id.bank_id and payment.partner_bank_id.bank_id.street2:
                bank_address += payment.partner_bank_id.bank_id.street2 + ','
            if payment.partner_bank_id.bank_id and payment.partner_bank_id.bank_id.city:
                bank_address += payment.partner_bank_id.bank_id.city + ','
            if payment.partner_bank_id.bank_id and payment.partner_bank_id.bank_id.state:
                bank_address += payment.partner_bank_id.bank_id.state.name + ','
            if payment.partner_bank_id.bank_id and payment.partner_bank_id.bank_id.country:
                bank_address += payment.partner_bank_id.bank_id.country.name + ','
            if payment.partner_bank_id.bank_id and payment.partner_bank_id.bank_id.zip:
                bank_address += payment.partner_bank_id.bank_id.zip
            iban = payment.partner_id.bank_ids[0].acc_number if payment.partner_id.bank_ids else payment.partner_bank_id.iban_no
            worksheet.write(row, 0, count)
            worksheet.write(row, 1, iban or '')
            worksheet.write(row, 2, payment.amount or 0)
            worksheet.write(row, 3, payment.partner_bank_id.bank_id.bic or '')
            worksheet.write(row, 4, payment.partner_bank_id.bank_id.name or '')
            worksheet.write(row, 5, payment.partner_bank_id.branch or '')
            worksheet.write(row, 6, bank_address)
            worksheet.write(row, 7, payment.partner_id.name or '')
            worksheet.write(row, 8, payment.ref or '')
            worksheet.write(row, 9, payment.partner_bank_id.bank_id.phone or '')
            worksheet.write(row, 10, 'our')
            worksheet.write(row, 11, 'exclude')
            worksheet.write(row, 12, payment.purpose_of_transfer or '')
        print('--------------------------')
        workbook.close()
        output.seek(0)
        output = base64.encodebytes(output.read())
        self.write({'binary_data': output})
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=export.payment&field=binary_data&download=true&id=%s&filename=%s' % (
                self.id, filename),
            'target': 'new',
        }
