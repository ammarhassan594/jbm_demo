from odoo import models, fields, api, _
import requests
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class SendSms(models.Model):
    _name = 'send.sms'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Subject")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_queue', 'In Queue'),
        ('sent', 'Sent'),
        ('cancel', 'Canceled'),
    ], default='draft', tracking=True,)

    employee_ids = fields.Many2many('hr.employee', string='Employees', required=True)
    body = fields.Text(string="Body", required=True)
    schedule_date = fields.Datetime(string="Schedule Date")
    sent_date = fields.Datetime(string="Sent Date")
    canceled_date = fields.Datetime(string="Canceled Date")

    def _get_proxies(self):
        configuration_id = self.env['dynamic.integration.configuration'].search([
            ('model', '=', 'hr.employee'),
        ], limit=1)
        proxies = {}
        if configuration_id:
            if configuration_id.http_proxy:
                proxies['http'] = configuration_id.http_proxy
            if configuration_id.https_proxy:
                proxies['https'] = configuration_id.https_proxy
        return proxies

    def _prepare_sms_numbers_fields(self):
        fields = []
        integration_configuration = self.env['dynamic.integration.configuration'].search([
            ('model', '=', 'hr.employee'),
        ], limit=1)
        if integration_configuration and integration_configuration.field_ids:
            for field in integration_configuration.field_ids:
                if field.name not in fields:
                    fields.append(field.name)
        return fields

    def _prepare_sms_numbers(self):
        fields_name = self._prepare_sms_numbers_fields()
        numbers = []
        if fields_name and self.employee_ids:
            for name in fields_name:
                phones = self.employee_ids.mapped(name)
                if phones:
                    for phone in phones:
                        if phone and phone not in numbers:
                            numbers.append(phone)
        return numbers

    def send_sms_message(self):
        url = self.env['ir.config_parameter'].sudo().get_param('ooredoo_url')
        customer_id = self.env['ir.config_parameter'].sudo().get_param('ooredoo_customerID')
        user_name = self.env['ir.config_parameter'].sudo().get_param('ooredoo_username')
        user_password = self.env['ir.config_parameter'].sudo().get_param('ooredoo_password')
        originator = self.env['ir.config_parameter'].sudo().get_param('ooredo_originator')

        message = self.body

        phonenumbers = self._prepare_sms_numbers()

        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': 'http://pmmsoapmessenger.com/HTTP_SendSms',
        }
        proxies = self._get_proxies()

        if phonenumbers:
            for phone in phonenumbers:
                xml_payload = """
                <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                               xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                  <soap:Body>
                    <HTTP_SendSms xmlns="http://pmmsoapmessenger.com/">
                    """ + """<customerID>""" + str(customer_id) + """</customerID>""" + """<userName>""" + str(
                    user_name) + """</userName>""" + """<userPassword>""" + str(
                    user_password) + """</userPassword>""" + """<originator>""" + str(
                    originator) + """</originator>""" + """<smsText>""" + str(
                    message) + """</smsText>""" + """<recipientPhone>""" + str(phone) + """</recipientPhone>""" + """
                      <messageType>ArabicWithLatinNumbers</messageType>
                      <defDate></defDate>
                      <blink>false</blink>
                      <flash>false</flash>
                      <Private>false</Private>
                    </HTTP_SendSms>
                  </soap:Body>
                </soap:Envelope>
                """
                _logger.info('TEST OOREDOOO')
                _logger.info(message)
                _logger.info(xml_payload)
                _logger.info(url)

                response = requests.post(url, data=xml_payload.encode('utf-8'), headers=headers, proxies=proxies)
                _logger.info(response.content)
                _logger.info('status of sending message:////', response.status_code)

    def action_draft(self):
        self.schedule_date = None
        self.sent_date = None
        self.canceled_date = None
        self.state = 'draft'

    def action_schedule(self):
        ctx = dict(self.env.context, default_send_sms_id=self.id)
        return {
            'name': _('Schedule Sending SMS'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'send.sms.schedule',
            'target': 'new',
            'context': ctx,
        }

    def action_send(self):
        self.send_sms_message()
        self.sent_date = fields.Datetime.now()
        self.state = 'sent'

    def action_cancel(self):
        self.canceled_date = fields.Datetime.now()
        self.state = 'cancel'

    def action_test(self):
        ctx = dict(self.env.context, default_send_sms_id=self.id)
        return {
            'name': _('Test Sending SMS'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'send.sms.test',
            'target': 'new',
            'context': ctx,
        }

    def send_sms(self):
        records = self.env['send.sms'].search([
            ('state', '=', 'in_queue'),
            ('schedule_date', '<=', fields.Datetime.now())
        ])
        if records:
            for record in records:
                record.action_send()
