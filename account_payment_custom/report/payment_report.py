# -*- coding: utf-8 -*-
from decimal import Decimal
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import math



class ReportPaymentTransfer(models.AbstractModel):
    _name = 'report.account_payment_custom.cash_receipt_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        payments = self.env['account.payment'].browse(docids)
        if payments and payments.filtered(lambda s: s.payment_type != 'inbound'):
            raise ValidationError(_('Cannot generate cash receipt report for payment type: send'))
        docs = {
            'docs': payments,
            'payment': payments,
        }
        return docs


class ReportPaymentTransfer(models.AbstractModel):
    _name = 'report.account_payment_custom.payment_transfer_report_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        payment = self.env['account.payment'].browse(docids)
        if payment and payment.filtered(lambda s: s.payment_type != 'outbound'):
            raise ValidationError(_('Cannot generate payment transfer report for payment type: Receive'))
        journal = getattr(payment, 'journal_id', False)
        bank_id = getattr(journal, 'bank_id', False)
        more_than_payment = False
        if len(payment) > 1:
            more_than_payment = True
            amount = 0
            for pay in payment:
                amount += pay.amount
            docs = {
                'docs': docids,
                'payment': payment,
                'more_than_payment': more_than_payment,
                'total_amount': amount
            }
            return docs

        docs = {
            'docs': docids,
            'payment': payment,
            'more_than_payment': more_than_payment
        }
        return docs


class ReportPaymentCheck(models.AbstractModel):
    _name = 'report.account_payment_custom.payment_method_report_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        env = self.env
        payment = env['account.payment'].browse(docids).ensure_one()
        if not (payment.payment_type == 'outbound' and payment.payment_method_line_id.name.lower() == 'checks'):
            raise ValidationError(_('Cannot generate payment check report for payment type: Receive and Payment '
                                    'method not by Check'))

        account_id = payment.journal_id and payment.journal_id.default_account_id
        budgetary_position = False
        if account_id:
            budgetary_position = self.env['account.budget.post'].search([('account_ids', 'in', account_id.ids)],
                                                                        limit=1)
        journal = getattr(payment, 'journal_id', False)
        bank_id = getattr(journal, 'bank_id', False)
        acc_number = getattr(journal.bank_account_id, 'acc_number', False)
        approve_req_ids = payment.dynamic_approve_request_ids.sorted("sequence") or False
        shared_service_manager = accounting_manager = auditor = False
        # if approve_req_ids:
        #     auditor = env['res.users'].search(
        #         [('id', 'in', approve_req_ids[0].user_ids.ids), ('role_ids.name', 'ilike', 'Auditor')],
        #         limit=1)  # Auditor approves first
        #     shared_service_manager = env['res.users'].search(
        #         [('id', 'in', approve_req_ids[1].user_ids.ids), ('role_ids.name', 'ilike', 'Shared Services Manager')],
        #         limit=1)  # Then shared services manager approves it
        #     accounting_manager = env['res.users'].search(
        #         [('id', 'in', approve_req_ids[2].user_ids.ids), ('role_ids.name', 'ilike', 'Accounting Manager')],
        #         limit=1)  # Accounting Manager approves at last
        shared_service_manager_phone = False
        if shared_service_manager and shared_service_manager.partner_id and any(
                (shared_service_manager.partner_id.phone, shared_service_manager.partner_id.mobile)):
            shared_service_manager_phone = shared_service_manager.partner_id.phone or shared_service_manager.partner_id.mobile
        elif shared_service_manager and shared_service_manager.employee_id:
            shared_service_manager_phone = shared_service_manager.employee_id.phone or shared_service_manager.employee_id.mobile_phone

        created_by = getattr(payment, 'create_uid', False)  # Accountant creates the payment
        partner = getattr(created_by, 'partner_id', False)
        qid_ids = self.env['documents.document'].search([
            ('document_type_name', '=', 'QID'),
            ('partner_id', '=', partner.id)
        ])
        qid_number = qid_ids[
            0].document_number if qid_ids else False  # qid number of the accountant (who created the payment)
        # amount_decimal = payment.amount - math.floor(payment.amount)
        # amount_decimal =  frac, whole = math.modf(payment.amount)
        # amount_decimal = frac * 100
        amount_decimal = str(payment.amount).split('.')[1]
        if len(amount_decimal) == 1 and amount_decimal != '0':
            amount_decimal += '0'

        docs = {
            'docs': docids,
            'payments': payment,
            'budgetary_position': budgetary_position,
            'bank_id': bank_id,
            'acc_number': acc_number,
            'date': payment.date.strftime('%d/%m/%Y'),
            'amt_fraction': amount_decimal,
            # 'amt_fraction': int(((payment.amount) % 1) * 100),
            'amt': int(payment.amount),
            'created_by': created_by.name,
            'auditor_names': getattr(auditor, 'name', False),
            'shared_service_manager': shared_service_manager,
            'shared_service_manager_names': getattr(shared_service_manager, 'name', False),
            'shared_service_manager_phone': shared_service_manager_phone,
            'accounting_manager_names': getattr(accounting_manager, 'name', False),
            'accountant': created_by.name,
            'qid_number': qid_number,
            'check_number': payment.manual_check_no,
            'check_date': payment.date,
        }
        return docs


class PersonalCheck(models.AbstractModel):
    _name = 'report.account_payment_custom.payment_personal_check_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        env = self.env
        payment = env['account.payment'].browse(docids).ensure_one()
        if not (payment.payment_type == 'outbound' and payment.payment_method_line_id.name.lower() == 'checks'):
            raise ValidationError(_('Cannot generate payment check report for payment type: Receive and Payment '
                                    'method not by Check'))
        docs = {
            'docs': payment,
            'payment': payment,
        }
        return docs


class CompanyCheck(models.AbstractModel):
    _name = 'report.account_payment_custom.payment_company_check_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        env = self.env
        payment = env['account.payment'].browse(docids).ensure_one()
        if not (payment.payment_type == 'outbound' and payment.payment_method_line_id.name.lower() == 'checks'):
            raise ValidationError(_('Cannot generate payment check report for payment type: Receive and Payment '
                                    'method not by Check'))
        docs = {
            'docs': payment,
            'payment': payment,
        }
        return docs


class NewReportPaymentCheck(models.AbstractModel):
    _name = 'report.account_payment_custom.payment_method_report_template2'

    @api.model
    def _get_report_values(self, docids, data=None):
        env = self.env
        payment = env['account.payment'].browse(docids).ensure_one()
        # if not (payment.payment_type == 'outbound' and payment.payment_method_line_id.name.lower() == 'checks'):
        #     raise ValidationError(_('Cannot generate payment check report for payment type: Receive and Payment '
        #                             'method not by Check'))

        account_id = payment.journal_id and payment.journal_id.default_account_id
        budgetary_position = False
        if account_id:
            budgetary_position = self.env['account.budget.post'].search([('account_ids', 'in', account_id.ids)],
                                                                        limit=1)
        journal = getattr(payment, 'journal_id', False)
        bank_id = getattr(journal, 'bank_id', False)
        acc_number = getattr(journal.bank_account_id, 'acc_number', False)
        approve_req_ids = payment.dynamic_approve_request_ids.sorted("sequence") or False
        approve_list = []
        approve_name = []
        if approve_req_ids:
            for req in approve_req_ids:
                approve_list.append(req.approved_by)
            for approve in approve_list:
                arabic_name = self.env['hr.employee'].search([('user_id', '=', approve.id)]).arabic_name
                approve_name.append(arabic_name)
        accounting_name = ''
        auditor_name = ''
        accounting_manager_name = ''
        shared_service_manager_name = ''
        if len(approve_name) >= 1:
            accounting_name = approve_name[0]
        if len(approve_name) >= 2:
            auditor_name = approve_name[1]
        if len(approve_name) >= 3:
            accounting_manager_name = approve_name[2]
        if len(approve_name) >= 4:
            shared_service_manager_name = approve_name[3]

        accounting_signature = ''
        auditor_signature = ''
        accounting_manager_signature = ''
        shared_service_manager_signature = ''
        if len(approve_name) >= 1:
            accounting_signature = approve_list[0]
        if len(approve_name) >= 2:
            auditor_signature = approve_list[1]
        if len(approve_name) >= 3:
            accounting_manager_signature = approve_list[2]
        if len(approve_name) >= 4:
            shared_service_manager_signature = approve_list[3]




        # shared_service_manager = accounting_manager = auditor = False
        # if approve_req_ids:
        #     auditor = env['res.users'].search(
        #         [('id', 'in', approve_req_ids[0].user_ids.ids), ('role_ids.name', 'ilike', 'Auditor')],
        #         limit=1)  # Auditor approves first
        #     shared_service_manager = env['res.users'].search(
        #         [('id', 'in', approve_req_ids[1].user_ids.ids), ('role_ids.name', 'ilike', 'Shared Services Manager')],
        #         limit=1)  # Then shared services manager approves it
        #     accounting_manager = env['res.users'].search(
        #         [('id', 'in', approve_req_ids[2].user_ids.ids), ('role_ids.name', 'ilike', 'Accounting Manager')],
        #         limit=1)  # Accounting Manager approves at last
        # shared_service_manager_phone = False
        # if shared_service_manager and shared_service_manager.partner_id and any(
        #         (shared_service_manager.partner_id.phone, shared_service_manager.partner_id.mobile)):
        #     shared_service_manager_phone = shared_service_manager.partner_id.phone or shared_service_manager.partner_id.mobile
        # elif shared_service_manager and shared_service_manager.employee_id:
        #     shared_service_manager_phone = shared_service_manager.employee_id.phone or shared_service_manager.employee_id.mobile_phone

        created_by = getattr(payment, 'create_uid', False)  # Accountant creates the payment
        partner = getattr(created_by, 'partner_id', False)
        partner_id = getattr(payment, 'partner_id', False)
        partner_name = ''
        if partner_id:
            partner_name = getattr(partner_id, 'name', False)
        # qid_ids = self.env['documents.document'].search([
        #     ('document_type_name', '=', 'QID'),
        #     ('partner_id', '=', partner.id)
        # ])
        # qid_number = qid_ids[
        #     0].document_number if qid_ids else False  # qid number of the accountant (who created the payment)
        # qid_number = getattr(partner_id, 'qid_no', False)
        qid_number = ''
        if payment.beneficiary_qid:
            qid_number = payment.beneficiary_qid
        # elif payment.beneficiary_commercial_number:
        #     qid_number = payment.beneficiary_commercial_number
        # amount_decimal = payment.amount - math.floor(payment.amount)
        # amount_decimal =  frac, whole = math.modf(payment.amount)
        # amount_decimal = frac * 100
        # amount_decimal = str(payment.amount).split('.')[1]
        # if len(amount_decimal) == 1 and amount_decimal != '0':
        #     amount_decimal += '0'
        amount = payment.amount

        docs = {
            'docs': docids,
            'payments': payment,
            'budgetary_position': budgetary_position,
            'bank_id': bank_id,
            'acc_number': acc_number,
            'date': payment.date.strftime('%d/%m/%Y'),
            'amount': amount,
            # 'amt_fraction': int(((payment.amount) % 1) * 100),
            'amt': int(payment.amount),
            'created_by': created_by.name,
            'partner': partner_name,
            # 'auditor_names': getattr(auditor, 'name', False),
            # 'shared_service_manager': shared_service_manager,
            # 'shared_service_manager_names': getattr(shared_service_manager, 'name', False),
            # 'shared_service_manager_phone': shared_service_manager_phone,
            # 'accounting_manager_names': getattr(accounting_manager, 'name', False),
            'accountant': created_by.name,
            'qid_number': qid_number,
            'check_number': payment.manual_check_no,
            'check_date': payment.date,
            'accounting_name': accounting_name,
            'accounting_signature': accounting_signature,
            'auditor_name': auditor_name,
            'auditor_signature': auditor_signature,
            'accounting_manager_name': accounting_manager_name,
            'accounting_manager_signature': accounting_manager_signature,
            'shared_service_manager_name': shared_service_manager_name,
            'shared_service_manager_signature': shared_service_manager_signature,
        }
        return docs
