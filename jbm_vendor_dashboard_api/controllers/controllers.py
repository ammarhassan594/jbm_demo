# -*- coding: utf-8 -*-
import datetime

from odoo import http, fields, models
from odoo.http import request
from datetime import timedelta, datetime


def set_contract_purchase_info(con_or_pur, total, total_paid, amount_residual, total_unpaid, is_contract):
    data = {
        'id': con_or_pur.id,
        'description': con_or_pur.contract_description or '' if is_contract else con_or_pur.subject or '',
        'contract_number': con_or_pur.name,
        'total': total,
        'total_paid': total_paid,
        'amount_residual': amount_residual + total_unpaid,
        'is_contract': int(is_contract)
    }
    return data


def set_bill_info(bill_number, amount_total, total_paid, amount_residual):
    data = {
                        'bill_number':  bill_number,
                        'total_amount': amount_total,
                        'total_paid': total_paid,
                        'amount_residual': amount_residual
                    }
    return data


def get_total(con_or_pur, is_contract, is_purchase):
    sub_total = 0
    if is_contract:
        for line in con_or_pur.line_ids:
            sub_total = sub_total + (line.product_qty * line.price_unit)
        return sub_total
    elif is_purchase:
        for line in con_or_pur.order_line:
            sub_total = sub_total + (line.product_qty * line.price_unit)
        return sub_total


def get_amount_residual_contract(contract):
    purchase_amount_residual = 0
    purchase_amount_total = 0
    for purchase in contract.purchase_ids.filtered(lambda pur: pur.state in ['purchase', 'done']):
        amount_residual = 0
        amount_total = 0
        for bill in purchase.invoice_ids:
            amount_residual = amount_residual + bill.amount_residual
            amount_total = amount_total + bill.amount_total
        purchase_amount_residual = purchase_amount_residual + amount_residual
        purchase_amount_total = purchase_amount_total + amount_total
    return purchase_amount_residual, purchase_amount_total


def get_amount_residual_purchase(purchase):
    purchase_amount_residual = 0
    purchase_amount_total = 0

    amount_residual = 0
    amount_total = 0
    for bill in purchase.invoice_ids:
        amount_residual = amount_residual + bill.amount_residual
        amount_total = amount_total + bill.amount_total
    purchase_amount_residual = purchase_amount_residual + amount_residual
    purchase_amount_total = purchase_amount_total + amount_total
    return purchase_amount_residual, purchase_amount_total


def bill_info(bill):
    return bill.name, bill.amount_total, bill.amount_residual


class VendorDashboard(http.Controller):

    def get_data_filtered(self, vendors):
        data_filtered = {}
        creation_dates = vendors.mapped('create_date')
        creation_dates.sort()
        for create_date in creation_dates:
            if data_filtered.get(create_date.year):
                if data_filtered.get(create_date.year).get(create_date.month):
                    data_filtered[create_date.year][create_date.month] = \
                        data_filtered.get(create_date.year).get(create_date.month) + 1
                else:
                    data_filtered.get(create_date.year).update({create_date.month: 1})
            else:
                data_filtered.update({create_date.year: {create_date.month: 1}})

        return data_filtered

    @http.route("/GetVendorsBillsData/", auth="public", type="json", methods=["POST"])
    def get_vendors_data(self, **kwargs):
        data = []
        params = request.httprequest.args.to_dict()

        vendors = request.env['res.partner'].sudo().search([('is_vendor', '=', True)])
        vendors_count = len(vendors)
        data_filtered = self.get_data_filtered(vendors) or {}
        all_vendor_bills = request.env['account.move'].sudo().search(
            [('partner_id', 'in', vendors.ids), ('move_type', '=', 'in_invoice'), ('state', '=', 'posted')])

        vendor_bills_number = len(all_vendor_bills)
        paid_vendor_bills = len(all_vendor_bills.filtered(lambda bill: bill.payment_state == 'paid'))
        not_paid_vendor_bills = vendor_bills_number - paid_vendor_bills

        bills_total_amount = sum(all_vendor_bills.mapped('amount_total'))
        bills_residual_amount = sum(all_vendor_bills.mapped('amount_residual'))
        bills_paid_amount = bills_total_amount - bills_residual_amount

        partner_bills_amounts = {}
        for partner in all_vendor_bills.mapped('partner_id'):
            partner_bills = all_vendor_bills.filtered(lambda bill: bill.partner_id.id == partner.id)
            partner_total_amounts = sum(partner_bills.mapped('amount_total'))
            partner_residual_amounts = sum(partner_bills.mapped('amount_residual'))
            partner_bills_amounts.update({
                partner.id: {
                    'partner_name': partner.name,
                    'partner_total_amounts': partner_total_amounts,
                    'partner_paid_amounts': partner_total_amounts - partner_residual_amounts,
                    'partner_residual_amounts': partner_residual_amounts

                }
            })
        data.append({
            'vendors_count': vendors_count,
            'vendors_data_filtered': data_filtered,
            'vendor_bills_number': vendor_bills_number,
            'paid_vendor_bills': paid_vendor_bills,
            'not_paid_vendor_bills': not_paid_vendor_bills,
            'bills_total_amount': bills_total_amount,
            'bills_paid_amount': bills_paid_amount,
            'bills_residual_amount': bills_residual_amount,
            'partner_bills_amounts': partner_bills_amounts,
        })

        return data

    @http.route('/GetVendorContractInfo', auth="public", type="json", methods=["POST"])
    def vendor_purchase_agreements_info(self, **kwargs):
        print("hello")
        params = request.httprequest.args.to_dict()
        vendor_id = int(params.get("vendor_id"))
        if not vendor_id:
            return "Please, pass the supplier ID as a parameter"
        data = []
        contracts = request.env['purchase.requisition'].sudo().search([('vendor_id.id', '=', vendor_id), ('state', 'not in', ['draft', 'cancel'])])
        purchases = request.env['purchase.order'].sudo().search([('partner_id.id', '=', vendor_id),
                                                                       ('state', 'in', ['purchase', 'done']), ('requisition_id', '=', False)])
        for contract in contracts:
            total = get_total(contract, True, False)
            amount_residual, amount_total = get_amount_residual_contract(contract)
            total_unpaid = total - amount_total
            total_paid = amount_total - amount_residual
            # total_paid = total - amount_residual
            data.append(
             set_contract_purchase_info(contract, total, total_paid, amount_residual, total_unpaid, True)
            )
        for purchase in purchases:
            total = get_total(purchase, False, True)
            amount_residual, amount_total = get_amount_residual_purchase(purchase)
            total_unpaid = total - amount_total
            total_paid = amount_total - amount_residual
            # total_paid = total - amount_residual
            data.append(
             set_contract_purchase_info(purchase, total, total_paid, amount_residual, total_unpaid, False)
            )
        return data

    @http.route('/ContractBillInfo', auth="public", type="json", methods=["POST"])
    def purchase_agreement_info(self, **kwargs):
        data = []
        params = request.httprequest.args.to_dict()
        contract_id = int(params.get("contract_id"))
        is_contract = int(params.get("is_contract"))
        if is_contract:
            contract = request.env['purchase.requisition'].sudo().search([('id', '=', contract_id)])
            for purchase in contract.purchase_ids:
                for bill in purchase.invoice_ids:
                    bill_number, amount_total, amount_residual = bill_info(bill)
                    total_paid = amount_total - amount_residual
                    data.append(
                      set_bill_info(bill_number, amount_total, total_paid, amount_residual)
                    )
            return data

        else:
            purchase = request.env['purchase.order'].sudo().search([('id', '=', contract_id)])
            for bill in purchase.invoice_ids:
                bill_number, amount_total, amount_residual = bill_info(bill)
                total_paid = amount_total - amount_residual
                data.append(
                    set_bill_info(bill_number, amount_total, total_paid, amount_residual)
                )
            return data

