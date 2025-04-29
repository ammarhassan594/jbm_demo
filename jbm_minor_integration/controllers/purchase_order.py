# -*- coding: utf-8 -*-
import ast

from odoo import http
from odoo.http import request
from datetime import datetime
import base64
import json


class PurchaseOrderAccommodation(http.Controller):
    @http.route('/CreatePurchaseOrder', auth="public", type="json", methods=["POST"])
    def create_purchase_order(self, **kwargs):
        params = request.httprequest.data
        params = json.loads(params.decode('utf-8'))
        # params = request.httprequest.data.decode('utf-8')
        # params = ast.literal_eval(params)

        if params.get("case_ref_no"):

            if params.get("accommodation_type"):
                accommodation_product = request.env['product.product'].sudo().search(
                    [('accommodation_type', '=', params.get("accommodation_type"))], limit=1)
                if accommodation_product:
                    order_line = [(0, 0, {
                        'product_id': accommodation_product.id,
                        'name': accommodation_product.name,
                        'product_uom': accommodation_product.uom_po_id.id,
                        'product_qty': 1,
                        'price_unit': params.get("max_rent_price") if params.get("max_rent_price") else 0.0
                    })]

            po_vals = {
                'order_line': order_line,
                'accommodation_api': True,
                'case_ref_no': params.get("case_ref_no"),
                'case_name': params.get("case_name") or False,
                'case_qid': params.get("case_qid") or False,
                'priority': params.get("priority") or False,
                'person_no': int(params.get("person_no")) if params.get('person_no') else False,
                'region': params.get("region") or False,
                'rooms_no': int(params.get("rooms_no")) if params.get('rooms_no') else False,
            }

            date_format = '%Y-%m-%d'
            if params.get("start_date"):
                date_str = params.get("start_date")
                start_date_obj = datetime.strptime(date_str, date_format)
                po_vals.update({'start_date': start_date_obj})
            if params.get("end_date"):
                date_str = params.get("end_date")
                end_date_obj = datetime.strptime(date_str, date_format)
                po_vals.update({'end_date': end_date_obj})

            accommodation_po = request.env['purchase.order'].sudo().create(po_vals)

            if params.get("attachment"):
                for attach in params.get("attachment"):
                    attachment_vals = {
                    'datas': (attach.get("Data")).encode(),
                    'name': attach.get("Name"),
                    'res_model': accommodation_po._name,
                    'res_id': accommodation_po.id,
                    'type': 'binary',
                    }
                    attachment = request.env['ir.attachment'].sudo().create(attachment_vals)
                    accommodation_po.case_attachment_id = attachment.id
            
            data = {
                'status': 'Success',
                'status_code': 200,
                'purchase_id': accommodation_po.id
            }
            return data

        else:
            return "You Must Insert  Case Reference Number!"
