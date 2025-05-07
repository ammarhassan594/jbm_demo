# -*- coding: utf-8 -*-
import base64

import xlsxwriter
import io

from werkzeug.urls import url_encode

from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


class BankReceonWizard(models.TransientModel):
    _name = 'bank.receon'
    _description = 'Bank Receon'

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
        journals = journals and journals[0]
        if journals:
            move_lines = self.env['account.move'].search([
                ('date', '<=', self.date), ('line_ids', '!=', False)
            ]).mapped('line_ids').filtered(lambda l: l.account_id == self.account_id)
            print(" Move lines ", move_lines)
            move_lines_debit = sum(move_lines.mapped('debit')) or 0.0
            move_lines_credit = sum(move_lines.mapped('credit')) or 0.0
            print("move_lines_debit ", move_lines_debit)
            print("move_lines_credit ", move_lines_credit)
            amount_entities = move_lines_debit - move_lines_credit
            payments = self.env['account.payment'].search([
                ('recurring', '=', False), ('payment_type', '=', 'outbound'),
                ('date', '<=', self.date), ('state', '=', 'posted'),
                ('journal_id', '=', journals.id),
                ('payment_method_line_id.payment_method', '=', 'cheque')
            ]).filtered(lambda m: not m.move_id.has_reconciled_entries)
            payment_len = len(payments)
            #     if payments:
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {
                'in_memory': True,
                'strings_to_formulas': False,
            })
            decimal_format = workbook.add_format({'num_format': '0.00', 'align': 'left'})
            # Add the cell formats.
            format_left_to_right = workbook.add_format({"reading_order": 1})
            format_right_to_left = workbook.add_format({"reading_order": 2})
            sheet = workbook.add_worksheet("Bank Receon")
            # Change the direction for worksheet2.
            sheet.right_to_left()
            head = workbook.add_format(
                {'font_name': 'Calibri', 'align': 'center', 'bold': True, 'size': 18, 'border': 2,
                 'underline': True, })
            head.set_align('vcenter')

            title = workbook.add_format(
                {'font_name': 'Calibri', 'align': 'center', 'bold': True, 'border': 2, 'size': 16})
            title.set_align('vcenter')

            cell = workbook.add_format({'font_name': 'Calibri', 'align': 'right', 'bold': True,
                                        'border': 2, 'size': 12})
            cell.set_align('vcenter')

            cell_border = workbook.add_format({'font_name': 'Calibri',
                                               'align': 'center', 'bold': True,
                                               'border': 1, 'size': 12, 'underline': True})
            cell_border.set_align('vcenter')

            cell_red = workbook.add_format({'font_name': 'Calibri', 'align': 'right',
                                            'bold': True, 'border': 2, 'size': 12})
            cell_red.set_align('vcenter')
            cell_red.set_font_color('red')

            sheet.set_column('B:B', 60)
            sheet.set_column('C:C', 60)
            sheet.set_column('D:D', 60)
            sheet.set_column('E:E', 60)
            sheet.set_column('F:F', 60)
            sheet.set_column('G:G', 60)
            sheet.set_column('H:H', 60)
            sheet.set_column('I:I', 60)
            sheet.set_column('J:J', 60)
            for i in range((payment_len + 30)):
                sheet.set_row(i, 50)

            sheet.set_row(3, 70)
            row = 3
            column = 1
            sheet.merge_range(row, column, row, column + 4,
                              'مؤسسة الشيخ / جاسم بن محمد بن ثاني للرعاية الاجتماعية', head)

            row += 1
            sheet.merge_range(row, column, row, column + 4, '', cell)
            row += 1
            sheet.set_row(row, 70)
            bank_name = journals.bank_id.name if journals.bank_id else " "
            bank_number = journals.bank_account_id.acc_number if journals.bank_account_id else " "
            report_title = (' تسوية الحساب الخاص بالمؤسسة لدى  {}'
                            ' والخاص بالتوجيهات الواردة الى المؤسسة حساب رقم {}'.format(bank_name, bank_number))
            sheet.merge_range(row, column, row, column + 4,
                              report_title, head)
            row += 1
            sheet.set_row(row, 70)
            sheet.merge_range(row, column, row, column + 4, ' كما فى {}'.format(self.date.strftime('%Y/%m/%d')), title)
            row += 1
            sheet.merge_range(row, column, row, column + 4, '', cell)
            row += 1
            sheet.set_row(row, 70)
            sheet.merge_range(row, column, row, column + 4, ' المبالغ الموضحة أدناه بالريال القطري', title)
            row += 2
            sheet.set_column('B:B', 70)
            sheet.set_row(row, 50)
            sheet.write(row, column, ' البيان ', title)
            sheet.write(row, column + 1, "رقم الشيك/التحويل", title)
            sheet.write(row, column + 2, "تاريخ الشيك/التحويل", title)
            sheet.write(row, column + 3, '  المبلغ', title)
            sheet.write(row, column + 4, ' إجمالي ', title)
            row += 1

            report_title3 = ' رصيد حساب {} بموجب كشف البنك فى {}'.format(bank_name, self.date.strftime('%Y/%m/%d'))
            sheet.merge_range(row, column, row, column + 3,
                              report_title3, cell)
            sheet.write(row, column + 4, f"{amount_entities}", title)
            row += 1

            report_title3 = ('  يخصم منه : أرصده دائنه ظاهره في سجلات المؤسسة ولم تظهر في حساب'
                             ' {} حتى تاريخه ( شيكات لم تقدم للصرف ) ').format(bank_name)
            sheet.merge_range(row, column, row, column + 3,
                              report_title3, cell_red)
            sheet.write(row, column + 4, " ", cell)

            counter_payment = 1
            total_payment_amount = sum(payments.mapped('amount'))
            amount_entities -= total_payment_amount
            print("Len payment ", payment_len)
            for payment in payments:
                row += 1
                sheet.write(row, column, payment.case_name or " ", cell)
                sheet.write(row, column + 1, payment.manual_check_no or " ", cell)
                sheet.write(row, column + 2, payment.date or " ", cell)
                sheet.write(row, column + 3, payment.amount or " ", cell)
                if payment_len == counter_payment:
                    sheet.write(row, column + 4, total_payment_amount, cell_red)
                else:
                    sheet.write(row, column + 4, " ", cell)
                counter_payment += 1
            row += 1
            report_title4 = ('الرصيد بعد التسوية والمطابق لكشف حساب مصرف {} '
                             'بدفاتر المؤسسة حتى  {}').format(bank_name, self.date.strftime('%Y/%m/%d'))
            sheet.merge_range(row, column, row, column + 3,
                              report_title4, title)
            sheet.write(row, column + 4, f"{amount_entities}", title)
            row += 2

            report_title4 = ('الرصيد مطابق كما هو فى كشف حساب مصرف {} '
                             'بدفاتر المؤسسة فى {} ').format(bank_name, self.date.strftime('%Y/%m/%d'))
            sheet.merge_range(row, column, row, column + 2,
                              report_title4, title)
            row += 2

            sheet.write(row, column, 'محاسب', cell_border)
            sheet.write(row, column + 1, " ", cell)
            sheet.write(row, column + 2, "رئيس الحسابات", cell)
            row += 2
            account_manager = self.env.ref('jbm_group_access_right_extended.custom_accounting_manager').users
            account_manager = account_manager and account_manager[0]
            sheet.write(row, column, self.env.user.name, title)
            sheet.write(row, column + 1, " ", title)
            sheet.write(row, column + 2, account_manager.name, title)
        else:
            raise ValidationError(_('No journal found '))

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()
        return generated_file

    def action_print_receon_report(self):
        self.ensure_one()
        file = self.generate_xlsx_document()
        self.report_name = 'Receon Report'
        if file:
            file = self.generate_xlsx_document()
            self.report = base64.encodebytes(file)

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
