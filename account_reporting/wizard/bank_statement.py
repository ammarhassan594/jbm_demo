import base64

import xlsxwriter
import io

from werkzeug.urls import url_encode
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class BankStatement(models.TransientModel):
    _name = 'wizard.bank.statement'
    _description = 'Wizard Bank Statement'

    def _domain_account_id(self):
        account_journals = self.env['account.journal'].search(
            [('type', '=', 'bank')]).mapped('default_account_id')
        return [('id', 'in', account_journals.ids)]

    date = fields.Date(string="Date")
    account_ids = fields.Many2many(comodel_name="account.account", string="Accounts",
                                   domain=_domain_account_id)

    report_name = fields.Char(string="Report Name", required=False, )
    report = fields.Binary(string="Report")

    def generate_xlsx_document(self):
        payment_sudo = self.env['account.payment']
        account_journal_sudo = self.env['account.journal']
        journals = account_journal_sudo.search(
            [('type', '=', 'bank'), ('default_account_id', 'in', self.account_ids.ids)])
        len_journals = len(journals)
        len_accounts = len(self.account_ids)
        journal_dic = {}
        if journals:
            for journal in journals:
                print("journal ", journal)
                # calculated journals items
                move_lines = self.env['account.move'].search([
                    ('date', '<=', self.date), ('line_ids', '!=', False)
                ]).mapped('line_ids').filtered(lambda l:
                                               l.account_id == journal.default_account_id)
                print(" Move lines ", move_lines)
                move_lines_debit = sum(move_lines.mapped('debit')) or 0.0
                move_lines_credit = sum(move_lines.mapped('credit')) or 0.0
                print("move_lines_debit ", move_lines_debit)
                print("move_lines_credit ", move_lines_credit)
                amount_entities = move_lines_debit - move_lines_credit

                # calculated draft payment
                payments_draft = payment_sudo.search([
                    ('recurring', '=', False), ('payment_type', '=', 'outbound'),
                    ('date', '<=', self.date), ('state', '=', 'draft'),
                    ('journal_id', '=', journal.id),
                    ('payment_method_line_id.payment_method', '=', 'cheque')
                ]).filtered(lambda m: not m.move_id.has_reconciled_entries)
                amount_draft = sum(payments_draft.mapped('amount'))

                # calculated posted payment
                payments_posted = payment_sudo.search([
                    ('recurring', '=', False), ('payment_type', '=', 'outbound'),
                    ('date', '<=', self.date), ('state', '=', 'posted'),
                    ('journal_id', '=', journal.id),
                    ('payment_method_line_id.payment_method', '=', 'cheque')
                ]).filtered(lambda m: not m.line_id.has_reconciled_entries)
                amount_posted = sum(payments_posted.mapped('amount'))

                # calculated remaining payment
                remain_amount = 0
                for payment in payments_posted:
                    payment_date = payment.date
                    remain_payments = 0
                    first_payment_date = False
                    current_payment_date = (
                            payment_date + relativedelta(months=payment.recurring_every))

                    while 1:
                        if current_payment_date <= payment.end_date:
                            if not first_payment_date:
                                first_payment_date = \
                                    payment_date + relativedelta(months=payment.recurring_every)
                            remain_payments += 1
                        elif payment.end_date < current_payment_date:
                            break
                        current_payment_date += relativedelta(months=payment.recurring_every)

                    remain_amount = payment.amount * remain_payments

                total_c_amount = amount_entities - (remain_amount + amount_draft +
                                                    amount_posted)
                journal_dic[journal.id] = {
                    'amount_entities': amount_entities,
                    'amount_draft': amount_draft,
                    'amount_posted': amount_posted,
                    'remain_amount': remain_amount,
                    'total_c_amount': total_c_amount
                }

            total_move_entities = sum([j.get('amount_entities', 0) for j in journal_dic.values()])
            total_amount_draft = sum([j.get('amount_draft', 0) for j in journal_dic.values()])
            total_amount_posted = sum([j.get('amount_posted', 0) for j in journal_dic.values()])
            total_remain_amount = sum([j.get('remain_amount', 0) for j in journal_dic.values()])

            total_all = total_move_entities - (total_amount_draft + total_amount_posted + total_remain_amount)

            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {
                'in_memory': True,
                'strings_to_formulas': False,
            })
            decimal_format = workbook.add_format({'num_format': '0.00', 'align': 'left'})

            sheet = workbook.add_worksheet("Bank Statement Total")
            # Change the direction for worksheet2.
            sheet.right_to_left()

            head = workbook.add_format(
                {'font_name': 'Calibri', 'align': 'right', 'bold': True, 'size': 16})
            # head.set_align('vcenter')

            title = workbook.add_format(
                {'font_name': 'Calibri', 'align': 'right', 'bold': True,
                 'border': 2, 'underline': True, 'size': 16})
            title.set_align('vcenter')

            cell = workbook.add_format({'font_name': 'Calibri', 'align': 'center',
                                        'size': 16})
            cell.set_align('vcenter')

            cell_table = workbook.add_format({'font_name': 'Calibri', 'bold': True, 'align': 'center',
                                              'size': 16, 'border': 2})
            cell_table.set_align('vcenter')

            sheet.set_column(0, 0, 10)
            sheet.set_column(1, 1, 10)
            sheet.set_column(2, 2, 30)
            sheet.set_column(3, 3, 80)
            sheet.set_column(2, (len_journals + 10), 40)

            for r_i in range(90):
                sheet.set_row(r_i, 30)
            sheet.set_row(2, 60)

            row = 2
            column = 2
            sheet.merge_range(row, column, row, column + 8,
                              'سعادة/ فيصل بن عبد العزيز الخاطر                    المحترم '
                              '        \n  المدير العام                       ', head)

            row += 1
            sheet.merge_range(row, column, row, column + 8, '', cell)
            row += 1
            report_title_1 = 'السلام عليكم ورحمة الله وبركاته'

            sheet.merge_range(row, column, row, column + 8,
                              report_title_1, head)
            row += 1
            sheet.merge_range(row, column, row, column + 8, '', cell)
            row += 1
            report_title_2 = (f'إشارة الى التسويات المرفقة نقدم لسعادتكم مخلص أرصدة حسابات المؤسسة'
                              f', لدى مصرف الريان مع ألأرصده '
                              f'المتاحة كما فى {self.date.strftime("%Y/%m/%d")}')
            sheet.merge_range(row, column, row, column + 11, report_title_2, title)
            row += 1

            sheet.write(row, column, 'م', cell_table)
            sheet.write(row, column + 1, "بيان", cell_table)
            counter_column = column + 2
            # Table Header
            for journal_id, item in journal_dic.items():
                journal = account_journal_sudo.browse(journal_id)
                journal_name = ('الحساب رقم {}'
                .format(
                    journal.bank_account_id.acc_number if journal.bank_account_id else " "))
                sheet.write(row, counter_column, journal_name, cell_table)
                counter_column += 1
            sheet.write(row, counter_column, "ألإجمالي", cell_table)
            row += 1
            # After header
            title2 = 'رصيد حسابات المصرف فى {}'.format(self.date.strftime("%Y/%m/%d"))
            sheet.merge_range(row, column, row, column + 1, title2, cell_table)
            counter_column = column + 2
            for journal_id, item in journal_dic.items():
                sheet.write(row, counter_column, item.get('amount_entities', 0), cell_table)
                counter_column += 1
            sheet.write(row, counter_column, total_move_entities, cell_table)
            row += 1

            title3 = 'أجراءات التسوية المرفقة'
            sheet.merge_range(row, column, row, column + 1, title3, cell_table)
            counter_column = column + 2
            for journal_id, item in journal_dic.items():
                sheet.write(row, counter_column, " ", cell_table)
                counter_column += 1
            sheet.write(row, counter_column, " ", cell_table)
            row += 1

            # Table Body

            # Posted Payment

            title3 = 'خصم جميع المبالغ لشيكات صادرة مؤجلة من الحساب / الجاري (مرفق التسوية)'
            sheet.write(row, column, 1, cell_table)
            sheet.write(row, column + 1, title3, cell_table)
            counter_column = column + 2
            for journal_id, item in journal_dic.items():
                sheet.write(row, counter_column, item.get('amount_posted', 0.0), cell_table)
                counter_column += 1
            sheet.write(row, counter_column, total_amount_posted or 0.0, cell_table)
            row += 1

            # Draft Payment

            title3 = 'خصم جميع المبالغ لشيكات وتحويلات لم تقدم للصرف من حساب رقم (002) (مرفق التسوية)'
            sheet.write(row, column, 2, cell_table)
            sheet.write(row, column + 1, title3, cell_table)
            counter_column = column + 2
            for journal_id, item in journal_dic.items():
                sheet.write(row, counter_column, item.get('amount_draft', 0.0), cell_table)
                counter_column += 1
            sheet.write(row, counter_column, total_amount_draft or 0.0, cell_table)
            row += 1

            # Remaining Payment

            title3 = 'خصم جميع المبالغ المحجوزة للحالات المعتمدة من حساب التوجيهات (مرفق التسوية)'
            sheet.write(row, column, 3, cell_table)
            sheet.write(row, column + 1, title3, cell_table)
            counter_column = column + 2
            for journal_id, item in journal_dic.items():
                sheet.write(row, counter_column, item.get('remain_amount', 0.0), cell_table)
                counter_column += 1
            sheet.write(row, counter_column, total_remain_amount or 0.0, cell_table)
            row += 1

            # End Table
            title3 = 'الرصيد المتاح كما فى {}'.format(self.date.strftime("%Y/%m/%d"))
            sheet.merge_range(row, column, row, column + 1, title3, cell_table)
            sheet.write(row, column + 1, title3, cell_table)
            counter_column = column + 2
            for journal_id, item in journal_dic.items():
                sheet.write(row, counter_column, item.get('total_c_amount', 0.0), cell_table)
                counter_column += 1
            sheet.write(row, counter_column, total_all or 0.0, cell_table)
            row += 1
        else:
            raise ValidationError(_('No journal found '))

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()
        return generated_file

    def action_print_bank_statement(self):
        pass
        self.ensure_one()
        file = self.generate_xlsx_document()
        self.report_name = 'Bank Statement Total'
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
