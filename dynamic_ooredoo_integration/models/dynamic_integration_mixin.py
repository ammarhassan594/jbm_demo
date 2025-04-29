import requests
import datetime
import re
from lxml import etree
import logging
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval, time
from odoo.tools import date_utils
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

ACTION_FIELD = []
ACTION_FIELD_VALUE = []


def evaluate_python_code(record=None, python_code='',
                         model_id=None, env=None, **kwargs):
    """Return the value of python expression
    if record is None must be passed model_id and env

    @param record: The object to evaluate expression form it
    @param python_code: Python expression
    @param model_id: The model of the record
    @param env: The environment variable to get the value of record

    @return: The value of python expression if found, else False and error message
    @retype: bool, str
    """
    if not python_code:
        return False
    if not record:
        if model_id and env:
            record = env[model_id.model].sudo()
        else:
            return False
    record_sudo = record.sudo()
    slip = kwargs.get('slip', record_sudo.env['hr.payslip'])
    try:
        localdict = {
            'time': time,
            'context_today': datetime.datetime.now,
            'user': record_sudo.env.user,
            'self': record_sudo,
            'env': record_sudo.env,
            'slip': slip
        }
        # result = env['ir.config_parameter'].sudo().get_param('attendance_api_token')
        safe_eval(python_code, localdict, mode="exec", nocopy=True)
        test = None
        message = ''
        if "result" in localdict:
            test = localdict.get('result', False)
        else:
            message = 'Please check expression as mentioned before must be write result'
    except Exception as e:
        _logger.warning(e)
        message = str(e)
        _logger.info('Error Expression %s' % message)
        test = None
    return test, message


class DynamicIntegrationMix(models.AbstractModel):
    _name = 'dynamic.integration.mix'

    integration_configuration_id = fields.Many2one('dynamic.integration.configuration',
                                                   string="Configuration of Integration")

    def _validate_phone_number(self, phone_numbers=[]):
        pattern = "^[0-9]\d{10}$"
        numbers = []
        if phone_numbers:
            for phone in phone_numbers:
                if re.match(pattern, phone):
                    if phone not in numbers:
                        numbers.append(phone)
        return numbers

    def _prepare_sms_numbers(self):
        configuration_id = self._get_integration_configuration()
        fields = []
        numbers = []
        validated_numbers = []
        if configuration_id and configuration_id.field_ids:
            for field in configuration_id.field_ids:
                if field.name not in fields:
                    fields.append(field.name)
        if fields:
            for record in self:
                for name in fields:
                    if record[str(name)] and record[str(name)] not in numbers:
                        numbers.append(record[str(name)])
        if numbers:
            validated_numbers = self._validate_phone_number(numbers)

        return validated_numbers

    def write(self, vals):
        self.sudo()._get_integration_configuration()
        if str(ACTION_FIELD) in vals:
            if not self._context.get('skip_sms_import'):
                if vals[str(ACTION_FIELD)] == str(ACTION_FIELD_VALUE):
                    self.sudo().send_sms_message()
        object = super(DynamicIntegrationMix, self).write(vals)
        return object

    def _get_integration_configuration(self):
        integration_configuration = self.env['dynamic.integration.configuration'].search([
            ('model', '=', self._name),
        ], limit=1)
        object = integration_configuration if integration_configuration else False
        if object and object.action_field and object.action_field_value:
            global ACTION_FIELD
            global ACTION_FIELD_VALUE
            ACTION_FIELD = object.action_field.name
            ACTION_FIELD_VALUE = object.action_field_value
        return object

    def _prepare_message(self):
        configuration_id = self._get_integration_configuration()
        message = False
        slip = self.env.context.get('slip')
        if configuration_id and configuration_id.message_template:
            test, message = evaluate_python_code(self, configuration_id.message_template, slip=slip)
            if test is None and message:
                raise ValidationError(message)
            _logger.info(f'TestMessage {test}')
            _logger.info(f'TestMessage {message}')
            return test
            # message = eval(configuration_id.message_template)
            # return message

    def _get_proxies(self):
        configuration_id = self._get_integration_configuration()
        proxies = {}
        if configuration_id:
            if configuration_id.http_proxy:
                proxies['http'] = configuration_id.http_proxy
            if configuration_id.https_proxy:
                proxies['https'] = configuration_id.https_proxy

        return proxies

    def send_sms_message(self):

        url = self.env['ir.config_parameter'].sudo().get_param('ooredoo_url')
        customer_id = self.env['ir.config_parameter'].sudo().get_param('ooredoo_customerID')
        user_name = self.env['ir.config_parameter'].sudo().get_param('ooredoo_username')
        user_password = self.env['ir.config_parameter'].sudo().get_param('ooredoo_password')
        originator = self.env['ir.config_parameter'].sudo().get_param('ooredo_originator')

        message = ''
        if self.env.context.get('message'):
            message = self.env.context.get('message')
        else:
            slip = self.env.context.get('slip')
            message = self.with_context(slip=slip)._prepare_message()
        print('message:::', message)
        # phone = '201144868697'
        phonenumbers = self._prepare_sms_numbers()

        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': 'http://pmmsoapmessenger.com/HTTP_SendSms',
        }

        proxies = self._get_proxies()

        # proxies = {
        #     'http': 'http://iproxy.diw.da:8080',
        #     'https': 'http://iproxy.diw.da:8080',
        # }

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
                _logger.info(message)
                _logger.info(xml_payload)
                _logger.info(url)

                response = requests.post(url, data=xml_payload.encode('utf-8'), headers=headers, proxies=proxies)
                _logger.info(response.content)
                _logger.info('status of sending message:////', response.status_code)

                # print(xml_payload)
                # print(response.content)
                # print('status of sending message:////',response.status_code)

    # @api.model
    # def fields_view_get(self, view_id=None, view_type="form", toolbar=False, submenu=False):
    #     self._get_integration_configuration()
    #
    #     res = super().fields_view_get(
    #         view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
    #     )
    #     if view_type == "form":
    #         doc = etree.XML(res["arch"])
    #         params = {
    #             "integration_configuration_id": self.integration_configuration_id,
    #         }
    #         for node in doc.xpath("/form/sheet"):
    #             str_element = self.env["ir.qweb"]._render(
    #                 "dynamic_ooredoo_integration.integration_configuration_id_field", params
    #             )
    #             node.append(etree.fromstring(str_element))
    #         View = self.env["ir.ui.view"]
    #
    #         # Override context for postprocessing
    #         if view_id and res.get("base_model", self._name) != self._name:
    #             View = View.with_context(base_model_name=res["base_model"])
    #         new_arch, new_fields = View.postprocess_and_fields(doc, self._name)
    #         res["arch"] = new_arch
    #         new_fields.update(res["fields"])
    #         res["fields"] = new_fields
    #
    #     return res
