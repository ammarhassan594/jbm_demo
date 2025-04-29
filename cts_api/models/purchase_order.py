# -*- coding: utf-8 -*-

import requests
import logging
import base64
import json

from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval, time
from odoo.exceptions import UserError
from requests.exceptions import RequestException, Timeout, ConnectionError

_logger = logging.getLogger(__name__)


class InheritResConfigSettings(models.Model):
    _inherit = 'purchase.order'

    cts_api_status = fields.Selection([
        ('not_counted', 'Not Counted'), ('draft', 'Draft'), ('sent', 'Sent'), ('fail', 'Fail')],
        string='CTS API Status')
    cts_api_response = fields.Text(string="Api Response")
    cts_api_response_auth = fields.Text(string="Api Response Auth")

    @api.model
    def create(self, vals_list):
        orders = super().create(vals_list)
        for order in orders:
            if order.accommodation_api:
                order.cts_api_status = 'draft'
            else:
                order.cts_api_status = 'not_counted'
        return orders

    def _generate_cts_attachment(self):

        report = self.env.ref('taqat_purchase_extended.purchase_order_approval_template')
        attachment = self.env['ir.attachment'].sudo()
        vals = {}
        if report.report_type in ['qweb-pdf', 'qweb-html', 'qweb-text']:
            extension = 'pdf'
            if report.print_report_name:
                report_name = safe_eval(report.print_report_name, {'object': self, 'time': time})
                attachment_name = "%s.%s" % (report_name, extension)
            else:
                report_name = f'{report.name}' if report.name else f'{self._name}'
                attachment_name = "%s.%s" % (report_name, extension)
            pdf_bin, unused_filetype = report._render_qweb_pdf(self.id)
            vals.update({
                'datas': base64.b64encode(pdf_bin),
                'name': attachment_name,
                'mimetype': 'application/pdf',
                'res_model': self._name,
                'res_id': self.id,
                'type': 'binary',
            })
        elif report.report_type == 'xlsx':
            extension = 'xlsx'
            if report.print_report_name:
                report_name = safe_eval(report.print_report_name, {'object': self, 'time': time})
                attachment_name = "%s.%s" % (report_name, extension)
            else:
                report_name = f'{report.name}' if report.name else f'{self._name}'
                attachment_name = "%s.%s" % (report_name, extension)
            data = {"context": self._context or self.env.context}
            xlsx_bin, unused_filetype = report._render_xlsx(self.id, data=data)
            vals.update({
                'datas': base64.b64encode(xlsx_bin),
                'name': attachment_name,
                'res_model': self._name,
                'res_id': self.id,
                'type': 'binary',
            })
        if vals:
            return attachment.create(vals)
        return False

    def _get_authentication_key(self):
        url = self.env['ir.config_parameter'].sudo().get_param('cts_auth_url')
        username = self.env['ir.config_parameter'].sudo().get_param('cts_username')
        password = self.env['ir.config_parameter'].sudo().get_param('cts_password')
        cert_url = self.env['ir.config_parameter'].sudo().get_param('ssl_certificate_url')

        payload = json.dumps({
            "UserName": username,
            "Password": password
        })
        headers = {
            'Content-Type': 'application/json',
        }
        try:
            response = requests.request("POST", url, headers=headers, data=payload, verify=False)
            # response = requests.request("POST", url, headers=headers, data=payload)
            _logger.info(f'{str(response.text)}')
            response_text = response.text
            response = json.loads(response_text)
            self.cts_api_response_auth = response
            if response and response.get('Result') and response.get('Result').get('AuthAccessToken'):
                return response.get('Result').get('AuthAccessToken')
            else:
                return False
        except (Timeout, ConnectionError, RequestException, ValueError) as e:
            _logger.warning(f'{str(e)}')
            self.cts_api_response_auth = f'{str(e)}'
            return f"{str(e)}"

    def _send_report_cts(self, auth_key, report):
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + auth_key,
            }
            url = self.env['ir.config_parameter'].sudo().get_param('cts_url')
            cert_url = self.env['ir.config_parameter'].sudo().get_param('ssl_certificate_url')

            payload = json.dumps({
                "DocumentReference": self.case_ref_no or '',
                "AttachmentType": 1,
                "Attachments": [
                    {
                        "Name": report.name,
                        "FileSize": report.file_size,
                        "Extension": report.mimetype.split('/')[-1] if report.mimetype else '',
                        "ContentType": report.mimetype,
                        "MD5Checksum": "",
                        "Data": report.datas.decode('ascii')}
                ]

            })
            # response = requests.request("POST", url, headers=headers, data=payload, verify=False)
            response = requests.post(url, data=payload, headers=headers, verify=False)
            response_text = response.text
            response = json.loads(response_text)
            self.cts_api_response = response_text
            if response.get('Status') and int(response.get('Status')) == 200:
                self.cts_api_status = 'sent'
            else:
                self.cts_api_status = 'fail'

            return response

        except (Timeout, ConnectionError, RequestException, ValueError) as e:
            _logger.warning(f'{str(e)}')
            self.cts_api_response = response_text
            self.cts_api_status = 'fail'
            return f"{str(e)}"

    def send_attachment_cts(self):
        report = self._generate_cts_attachment()
        authentication_key = self._get_authentication_key()
        response = self._send_report_cts(authentication_key, report)
        if isinstance(response, dict):
            response_text = json.dumps(response)
            self.cts_api_response = response_text
            if response.get('Status') and int(response.get('Status')) == 200:
                self.cts_api_status = 'sent'
            else:
                self.cts_api_status = 'fail'
        elif isinstance(response, str):
            self.cts_api_response = response
            self.cts_api_status = 'fail'

    def write(self, vals):
        if vals.get('state') and vals.get('state') == 'purchase' and self.case_ref_no:
            self.send_attachment_cts()
        return super(InheritResConfigSettings, self).write(vals)

    def send_fail_attachment(self):
        matched_orders = self.env['purchase.order'].search([('cts_api_status', '=', 'fail')])
        for order in matched_orders:
            order.send_attachment_cts()
