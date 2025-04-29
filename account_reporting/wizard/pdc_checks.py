# -*- coding: utf-8 -*-
import base64

import xlsxwriter
import io
from dateutil.relativedelta import relativedelta

from werkzeug.urls import url_encode

from odoo import models, fields, api, _

from odoo.exceptions import ValidationError


class PdcChecksWizard(models.TransientModel):
    _name = 'pdc.checks'
    _description = 'PDC CHECKS'

    def _domain_account_id(self):
        account_journals = self.env['account.journal'].search(
            [('type', '=', 'bank')]).mapped('default_account_id')
        return [('id', 'in', account_journals.ids)]

    date = fields.Date(string="Date")
    account_id = fields.Many2one(comodel_name="account.account", string="Account",
                                 domain=_domain_account_id)

    report_name = fields.Char(string="Report Name", required=False, )
    report = fields.Binary(string="Report")

    def generate_xlsx_document(self):

        journals = self.env['account.journal'].search(
            [('type', '=', 'bank'), ('default_account_id', '=', self.account_id.id)])
        if journals:
            payments1 = self.env['account.payment'].search(
                [
                    ('recurring', '=', True), ('recurring_every', '!=', False), ('end_date', '!=', False),
                 ('end_date', '>=', self.date), ('type', '=', 'scheduled'), ('journal_id', '=', journals[0].id),

                 ])
            # payments2 = self.env['account.payment'].search(
            #     [
            #         ('recurring', '!=', True), ('date', '>=', self.date),
            #         ('journal_id', '=', journals[0].id),
            #
            #     ]).filtered(lambda p: p.payment_method_line_id.payment_method_id.code == 'check_printing')
            payments = payments1

            if payments:
                output = io.BytesIO()
                workbook = xlsxwriter.Workbook(output, {
                    'in_memory': True,
                    'strings_to_formulas': False,
                })
                decimal_format = workbook.add_format({'num_format': '0.00', 'align': 'left'})

                sheet = workbook.add_worksheet("PDC Report")

                head = workbook.add_format(
                    {'font_name': 'Calibri', 'align': 'center', 'bold': True, 'size': 16, 'border': 2,
                     'underline': True})
                head.set_align('vcenter')

                title = workbook.add_format(
                    {'font_name': 'Calibri', 'align': 'center', 'bold': True, 'border': 2, 'size': 16})
                title.set_align('vcenter')

                table_footer = workbook.add_format(
                    {'font_name': 'Calibri', 'align': 'center', 'bold': True, 'border': 2, 'size': 16})
                table_footer.set_align('vcenter')

                cell = workbook.add_format({'font_name': 'Calibri', 'align': 'center', 'size': 14})
                cell.set_align('vcenter')

                right_edge_cell = workbook.add_format(
                    {'font_name': 'Calibri', 'align': 'center', 'size': 14, 'right': 2})
                right_edge_cell.set_align('vcenter')

                left_edge_cell = workbook.add_format({'font_name': 'Calibri', 'align': 'center', 'size': 14, 'left': 2})
                left_edge_cell.set_align('vcenter')

                sheet.set_column('A:A', 2)
                sheet.set_column('B:B', 2)
                sheet.set_column('C:C', 15)
                sheet.set_column('D:D', 20)
                sheet.set_column('E:E', 20)
                sheet.set_column('F:F', 15)
                sheet.set_column('G:G', 15)
                sheet.set_column('H:H', 20)
                sheet.set_column('I:I', 35)
                sheet.set_column('J:J', 45)
                sheet.set_row(0, 35)
                sheet.set_row(1, 35)
                sheet.set_row(2, 35)
                sheet.set_row(3, 35)
                sheet.set_row(4, 40)
                sheet.set_row(5, 35)
                sheet.set_row(6, 50)
                sheet.set_row(7, 35)
                sheet.set_row(8, 35)
                sheet.set_row(9, 35)
                sheet.set_row(10, 35)
                sheet.set_row(11, 35)
                sheet.set_row(12, 35)
                sheet.set_row(13, 35)
                sheet.set_row(14, 35)
                sheet.set_row(15, 35)
                sheet.set_row(16, 35)
                sheet.set_row(17, 35)
                sheet.set_row(18, 35)
                sheet.set_row(19, 35)
                sheet.set_row(20, 35)

                row = 2
                column = 2
                sheet.merge_range(row, column, row, column + 7,
                                  'مؤسسة الشيخ جاسم بن محمد بن ثاني للرعاية الاجتماعية', head)

                row += 1
                sheet.merge_range(row, column, row, column + 7, '', cell)
                row += 1
                report_title = 'بيان بالشيكات الصاردة بتواريخ لاحقة للمؤسسة من الحساب الجاري رقم(' \
                               + (journals[0].bank_account_id.acc_number if journals[0].bank_account_id else '') \
                               + ') حتى تاريخ ' + str(self.date)

                sheet.merge_range(row, column, row, column + 7,
                                  report_title, head)
                row += 1
                sheet.merge_range(row, column, row, column + 7, '', cell)
                row += 1
                sheet.write(row, column, ' إجمالى المبلغ ', title)
                sheet.write(row, column + 1, " تاريخ إستحقاق آخر \n شيك من أوراق الدفع", title)
                sheet.write(row, column + 2, "تاريخ استحقاق اول\n شيك من أوراق الدفع", title)
                sheet.write(row, column + 3, '  نوع الحساب', title)
                sheet.write(row, column + 4, ' قيمة الشيك  ', title)
                sheet.write(row, column + 5, ' عدد الشيكات / عدد \nالتحويلات المتبقية ', title)
                sheet.write(row, column + 6, ' رقم البطاقة الشخصية', title)
                sheet.write(row, column + 7, ' أسم الحالة', title)
                row += 1
                total_pdc_amount = 0
                for payment in payments:
                    if payment.journal_id.bank_account_id and payment.journal_id.bank_account_id.account_type_id:
                        account_type = payment.journal_id.bank_account_id.account_type_id.name
                    else:
                        account_type = ''
                    payment_date = payment.date
                    remain_payments = 0
                    first_payment_date = False
                    current_payment_date = payment_date + relativedelta(months=payment.recurring_every)

                    while 1:
                        if payment.end_date and current_payment_date <= payment.end_date:
                            if not first_payment_date:
                                first_payment_date = payment_date + relativedelta(months=payment.recurring_every)
                            remain_payments += 1
                        elif payment.end_date and payment.end_date < current_payment_date:
                            break
                        current_payment_date += relativedelta(months=payment.recurring_every)
                    if remain_payments:
                        last_payment_date = current_payment_date + relativedelta(months=-1 * payment.recurring_every)
                        total_remain_amount = payment.amount * remain_payments
                        total_pdc_amount += total_remain_amount
                        sheet.write(row, column, total_remain_amount, left_edge_cell)
                        sheet.write(row, column + 1, str(last_payment_date), cell)
                        sheet.write(row, column + 2, str(first_payment_date), cell)
                        sheet.write(row, column + 3, account_type, cell)
                        sheet.write(row, column + 4, payment.amount, cell)
                        sheet.write(row, column + 5, remain_payments, cell)
                        sheet.write(row, column + 6, payment.qid_number if payment.qid_number else '', cell)
                        sheet.write(row, column + 7, payment.partner_id.name if payment.partner_id else '',
                                    right_edge_cell)
                        row += 1
                sheet.write(row, column, total_pdc_amount, table_footer)
                sheet.merge_range(row, column + 1, row, column + 7,
                                  'الإجمالي الشيكات الصاردة بتواريخ لاحقة من الحساب الجاري', table_footer)

                workbook.close()
                output.seek(0)
                generated_file = output.read()
                output.close()
                return generated_file
            else:
                raise ValidationError(_('No payments found '))
        else:
            raise ValidationError(_('No journal found '))

    def action_print_pdc_report(self):
        self.ensure_one()
        file = self.generate_xlsx_document()
        self.report_name = 'PDC Report'
        if file:
            file = self.generate_xlsx_document()
            self.report = base64.encodestring(file)

            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/?' + url_encode({
                    'model': self._name,
                    'id': self.id,
                    'filename_field': 'report_name',
                    'field': 'report',
                    'download': 'true'
                }),
                'target': 'self'
            }
