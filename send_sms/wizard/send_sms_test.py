from odoo import models, fields, api, _
import requests
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class SendSMSTest(models.TransientModel):
    _name = 'send.sms.test'

    numbers = fields.Text(string='Number(s)', required=True, help='Carriage-return-separated list of phone numbers')
    send_sms_id = fields.Many2one('send.sms', string='Send SMS', required=True, ondelete='cascade')

    def action_send_sms(self):
        if self.send_sms_id:
            message = self.send_sms_id.body

            url = self.env['ir.config_parameter'].sudo().get_param('ooredoo_url')
            customer_id = self.env['ir.config_parameter'].sudo().get_param('ooredoo_customerID')
            user_name = self.env['ir.config_parameter'].sudo().get_param('ooredoo_username')
            user_password = self.env['ir.config_parameter'].sudo().get_param('ooredoo_password')
            originator = self.env['ir.config_parameter'].sudo().get_param('ooredo_originator')


            phonenumbers = [number.strip() for number in self.numbers.splitlines()]

            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': 'http://pmmsoapmessenger.com/HTTP_SendSms',
            }
            proxies = self.send_sms_id._get_proxies()

            if phonenumbers:
                for phone in phonenumbers:
                    xml_payload = """
                            <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                                           xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                                           xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                              <soap:Body>
                                <HTTP_SendSms xmlns="http://pmmsoapmessenger.com/">
                                """ + """<customerID>""" + str(
                        customer_id) + """</customerID>""" + """<userName>""" + str(
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
                    response = requests.post(url, data=xml_payload.encode('utf-8'), headers=headers, proxies=proxies)
                    _logger.info('status of sending message:////', response.status_code)
