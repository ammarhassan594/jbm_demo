# -*- coding: utf-8 -*-
from datetime import datetime, date
from logging import getLogger

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    state = fields.Selection(selection_add=[("recurring_approved", "Recurring Approved"), ('posted',)],
                             ondelete={'recurring_approved': 'set default'})


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    recurring = fields.Boolean('Recurring')
    recurring_every = fields.Integer('Recurring Every')
    bank_name = fields.Char()
    iban_number = fields.Char(strting='IBAN Number')
    end_date = fields.Date(string="End Date")
    recurring_payment_id = fields.Many2one('account.payment', string='Origin Payment')
    recurring_payment_ids = fields.One2many('account.payment', 'recurring_payment_id', string='Payments')
    initial_payment = fields.Boolean(string="Initial Payment")
    payee = fields.Many2one('res.partner')
    payee_qid = fields.Char()
    commercial_registration_number  = fields.Char()
    beneficiary_qid = fields.Char()
    # beneficiary_commercial_number = fields.Char()

    def approve_recurring_payment(self):
        create_list = []
        recurring_payments = self.filtered(lambda payment: payment.state == 'draft' and payment.recurring)

        for payment in recurring_payments:
            create_list.append({
                'is_internal_transfer': payment.is_internal_transfer,
                'payment_type': payment.payment_type,
                'partner_id': payment.partner_id.id if payment.partner_id else None,
                'amount': payment.amount,
                'journal_id': payment.journal_id.id,
                'payment_method_line_id': payment.payment_method_line_id.id if payment.payment_method_line_id else None,
                'date': payment.date,
                'ref': payment.ref,
                'is_post_dated_check': payment.is_post_dated_check,
                'recurring_payment_id': payment.id,
                'case_number': payment.case_number,
                'purpose_of_transfer': payment.purpose_of_transfer,
                'iban_number': payment.iban_number,
                'qid_number': payment.qid_number,
                'case_name': payment.case_name,
                'partner_bank_id': payment.partner_bank_id.id if payment.partner_bank_id else None,
            })
        if create_list:
            self.create(create_list)
        recurring_payments.write({'state': 'recurring_approved'})

    @api.onchange('recurring')
    def _onchange_recurring(self):
        if self.recurring:
            self.type = 'scheduled'
            self.payment_type = 'outbound'
        else:
            self.recurring_every = False

    @api.model
    def create_payment_api(self, **kwargs):
        _logger.info("In Payment API {}".format(kwargs))

        customer_qid = kwargs.get('beneficiaryQID') and str(kwargs.get('beneficiaryQID'))
        customer_name = kwargs.get('beneficiaryName') and str(kwargs.get('beneficiaryName'))
        iban_number = kwargs.get('ibanNumber') and str(kwargs.get('ibanNumber'))
        payment_method = kwargs.get('paymentMethod') and str(kwargs.get('paymentMethod'))
        amount = kwargs.get('amount') and float(kwargs.get('amount'))
        recurring = kwargs.get('recurring') and bool(kwargs.get('recurring'))
        recurring_every = kwargs.get('recurringEvery') and int(kwargs.get('recurringEvery'))
        date_created = kwargs.get('date') and str(kwargs.get('date'))
        case_number = kwargs.get('caseNumber') and str(kwargs.get('caseNumber'))
        case_owner_qid = kwargs.get('caseOwnerQID') and str(kwargs.get('caseOwnerQID'))
        case_name = kwargs.get('caseOwnerName') and str(kwargs.get('caseOwnerName'))
        cr_number = kwargs.get('beneficiaryCR') and str(kwargs.get('beneficiaryCR'))
        end_date = kwargs.get('expiryRecurringDate') and str(kwargs.get('expiryRecurringDate'))

        # Parameters must be passed to api
        # if not ((customer_qid or cr_number) and payment_method):
        #     return {
        #         "Message": "Missing required parameters ['BeneficiaryQID or beneficiaryCR', 'paymentMethod']",
        #         "http_status": 400,
        #         "code": 400
        #     }
        if payment_method not in ['bank_transfer', 'check']:
            return {
                "Message": "Payment Method has two values must be passed ['bank_transfer', 'check']",
                "http_status": 400,
                "code": 400
            }

        values = {
            "payment_type": 'outbound',
            "partner_type": 'supplier'
        }
        customer_sudo = self.env['res.partner'].sudo()
        employee_sudo = self.env['hr.employee'].sudo()
        if customer_qid:
            employee = employee_sudo.search([
                ('employee_qid_number', '=', customer_qid)
            ], limit=1)
            if employee and employee.user_id:
                values.update({
                    "partner_id": employee.user_id.partner_id.id
                })
            else:
                customer = customer_sudo.search([
                    ('qid_no', '=', customer_qid)], limit=1)
                if customer:
                    values.update({
                        "partner_id": customer.id
                    })
                else:
                    customer = customer_sudo.create({
                        'name': customer_name or f'Customer {customer_qid}',
                        'qid_no': customer_qid
                    })
                    values.update({
                        "partner_id": customer.id
                    })
        else:
            if cr_number:
                company = customer_sudo.search([
                    ('cr_number', '=', cr_number)
                ], limit=1)
                if company:
                    values.update({
                        "partner_id": company.id
                    })
                else:
                    company = customer_sudo.create({
                        'name': customer_name or f' Company {cr_number}',
                        'company_type': 'company',
                        'cr_number': cr_number
                    })
                    values.update({
                        "partner_id": company.id
                    })

        if payment_method:
            payment_method_sudo = self.env['account.payment.method.line'].sudo()
            payment_method_id = payment_method_sudo.search([
                ('case_integration_api_type', '=', payment_method)], limit=1)
            if payment_method_id:
                values.update({
                    "payment_method_line_id": payment_method_id.id
                })
        if amount:
            values.update({"amount": amount})
        if iban_number:
            values.update({"iban_number": iban_number})
        if case_name:
            values.update({"case_name": case_name})
        if case_number:
            values.update({"case_number": case_number})
        if customer_qid:
            values.update({"qid_number": customer_qid})
        if case_number:
            values.update({"case_number": case_number})
        if recurring:
            values.update({"recurring": recurring})
        if recurring_every:
            values.update({"recurring_every": recurring_every})
        if date_created:
            date_created = datetime.strptime(date_created, "%Y-%m-%d").date()
            values.update({"date": date_created})
        if case_owner_qid:
            values.update({'qid_number': case_owner_qid})
        if end_date:
            values.update({'end_date': end_date})
        _logger.info("Values {}".format(values))
        try:
            self.create(values)
            return {
                "Message": "Successfully created payment",
                "http_status": 201,
                "code": 201
            }
        except Exception as e:
            err = str(e)
            _logger.info("there is error on create payment {}".format(err))
            return {
                "Message": f"Error on creation payment {err}",
                "http_status": 500,
                "code": 500
            }

    @api.model
    def cancel_payment_api(self, **kwargs):
        _logger.info("In Cancel Payment API {}".format(kwargs))
        case_number = kwargs.get('caseNumber') and str(kwargs.get('caseNumber'))
        # Parameters must be passed to api
        if not case_number:
            return {
                "Message": "Missing required parameters ['case_number']",
                "http_status": 400,
                "code": 400
            }
        payment = self.search([
            ('case_number', '=', case_number), ('state', '=', 'draft')
        ], limit=1)
        if payment:
            payment.action_cancel()
            return {
                "Message": "Successfully cancelled payment",
                "http_status": 200,
                "code": 200
            }
        else:
            return {
                "Message": "Failed cancelled payment",
                "http_status": 400,
                "code": 400
            }

    # @api.model_create_multi
    # def create(self, val_list):
    #     for val in val_list:
    #         case_number = val.get('case_number')
    #         recurring = val.get('recurring')
    #         if case_number and recurring:
    #             exists_payment = self.search([
    #                 ('case_number', '=', case_number), ('recurring', '=', True)
    #             ])
    #             if exists_payment:
    #                 raise ValidationError(_(f'This case number {exists_payment.case_number} '
    #                                         f'already exists on another payment'))
    #     return super().create(val_list)

    @api.constrains('case_number', 'recurring')
    def _check_case_number(self):
        for record in self:
            if record.case_number and record.recurring:
                exists_payment = self.search([
                    ('case_number', '=', record.case_number),
                    ('id', '!=', record.id),
                    ('recurring', '=', True)
                ])
                if exists_payment:
                    if exists_payment:
                        if record.env.context.get('lang') == 'ar_001':
                            raise ValidationError(_(f"  لا يمكن إصافة نفس رقم الحالة {record.case_number} "
                                                    f" لأنه موجود على دفع متكرر أخر "))
                        else:
                            raise ValidationError(_(f'This case number'
                                                    f' {record.case_number} '
                                                    f'already exists on another recurring payment'))

    @api.constrains('state', 'recurring')
    def _check_recurring_posted(self):
        for record in self:
            if record.recurring and record.state == 'posted':
                if record.env.context.get('lang') == 'ar_001':
                    raise ValidationError(_(f" لا يمكن طلب موافقة على هذا الدفع لأنه متكرر "))
                else:
                    raise ValidationError(_('You cannot request approval for '
                                            'recurring payment'))


class AccountPaymentMethod(models.Model):
    _inherit = 'account.payment.method.line'

    payment_method = fields.Selection([
        ('check', 'Check'),
        ('bank_transfer', 'Bank Transfer'),
    ], string='Method Of Payment')

    case_integration_api_type = fields.Selection([
        ('check', 'Check'),
        ('bank_transfer', 'Bank Transfer'),
    ], string='Case Integration API Type')
