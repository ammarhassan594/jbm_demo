import requests
import base64
import json
import logging
import datetime

from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval, time
from odoo.tools import date_utils

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


def evaluate_python_code(record=None, python_code='',
                         model_id=None, env=None):
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
    try:
        localdict = {
            'time': time,
            'context_today': datetime.datetime.now,
            'user': record_sudo.env.user,
            'record': record_sudo,
            'env': record_sudo.env
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
        test = None
    return test, message


class DmsIntegrationMix(models.AbstractModel):
    _name = 'dms.integration.mix'

    dms_configuration_id = fields.Many2one('dms.integration',
                                           string="DMS Configuration")

    def _generate_attachment(self, report):
        """Generates attachment based on report type and return attachment object

        @param report: is a report object
        """
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

    # def _evaluate_python_code(self, python_code):
    #     """Return the value of python expression"""
    #     self_sudo = self
    #     try:
    #         localdict = {
    #             'time': time,
    #             'context_today': datetime.datetime.now,
    #             'user': self_sudo.env.user,
    #             'record': self_sudo,
    #         }
    #         safe_eval(python_code, localdict, mode="exec", nocopy=True)
    #         test = localdict.get('result')
    #     except Exception as e:
    #         _logger.warning(e)
    #         test = False
    #     return test

    def _get_body(self, dms_configuration):
        """Returns fields linked with dms_configuration object.
            Self must be referenced to the implementation model

        @param dms_configuration is the dms configuration object
        @rtype: dict
        """
        self.ensure_one()
        _logger.info("Getting body of api")
        result = {"fieldsValues": []}
        for line in dms_configuration.dms_field_ids.filtered(lambda l: l.send_type == 'body'):
            if line.python_code:
                value, _ = evaluate_python_code(self, line.python_code)
                result["fieldsValues"].append(
                    {
                        "Key": f"{line.api_field}",
                        "Value": value
                    })
            # Stop fetch from field_id
            # if hasattr(self, line.field_id.name):
            #     result["fieldsValues"].append(
            #         {
            #             "Key": f"{line.api_field}",
            #             "Value": getattr(self, line.field_id.name, False)
            #         })
        return result

    def _get_params(self, dms_configuration):
        """Returns params if there are fields sent by the header on DMS configuration.
                   Self must be referenced to the implementation model

        @param dms_configuration is the dms configuration object

        @rtype: dict
        """
        self.ensure_one()
        params = {}
        for line in dms_configuration.dms_field_ids.filtered(lambda l: l.send_type == 'headers'):
            if line.python_code:
                value, _ = evaluate_python_code(self, line.python_code)
                params[f"{line.api_field}"] = value
            # Stop fetch from field_id
            # if hasattr(self, line.field_id.name):
            #     params[f"{line.api_field}"] = getattr(self, line.field_id.name, False)

        return params

    def _get_attachments_on_field(self, dms_configuration):
        """Returns the attachments on the field if the field has an attachment value"""
        self.ensure_one()
        _logger.info("Getting attachment on fields ")
        result = []
        for line in dms_configuration.dms_field_ids. \
                filtered(lambda l: l.send_type == 'attachment'):
            if line.python_code and line.file_name_expression:
                attachment_datas, _ = evaluate_python_code(self, line.python_code)
                attachment_name, _ = evaluate_python_code(self, line.file_name_expression)
                attachment_name = str(attachment_name) or "Default Name"
                result.append({
                    attachment_name: attachment_datas
                })
            # Stop fetch from field_id
            # if hasattr(self, line.field_id.name):
            #     result["fieldsValues"].append(
            #         {
            #             "Key": f"{line.api_field}",
            #             "Value": getattr(self, line.field_id.name, False)
            #         })
        return result

    def _retrieve_attachment_report(self, report_id):
        """Retrieve an attachment for a specific report.

        :param report_id: Report assigned to model of record
        :return: A recordset of length <=1 or None
        """
        _logger.info("Retrieving attachment for report {}".format(report_id))
        extension = 'pdf'
        if report_id.report_type == 'qweb-pdf':
            extension = 'pdf'
        elif report_id.report_type == 'xlsx':
            extension = 'xlsx'
        if report_id.print_report_name:
            report_name = safe_eval(report_id.print_report_name, {'object': self, 'time': time})
            attachment_name = "%s.%s" % (report_name, extension)
        else:
            report_name = f'{report_id.name}' if report_id.name else f'{self._name}'
            attachment_name = "%s.%s" % (report_name, extension)
        return self.env['ir.attachment'].search([
            ('name', '=', attachment_name),
            ('res_model', '=', self._name),
            ('res_id', '=', self.id)
        ], limit=1)

    def _retrieve_attachment_record(self):
        """Retrieve an attachment for a specific report.

        :return: A recordset of length >=1 or None
        """
        return self.env['ir.attachment'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id)
        ])

    def _get_dms_integration(self):
        dms_configuration = self.env['dms.integration'].search([
            ('model_id', '=', self._name),
        ])
        if not dms_configuration:
            return False, False, False
        matched_dms = self.env['dms.integration']
        for config in dms_configuration:
            if config.is_matched_dms(res=self):
                matched_dms = config
                break
        if not matched_dms:
            return False, False, False
        state_field_id, state_value_id = (False, False)
        if matched_dms:
            state_field_id = matched_dms.field_state_id or False
            state_value_id = matched_dms.state_value_id or False
            return matched_dms, state_field_id, state_value_id
        return matched_dms, state_field_id, state_value_id

    def _attach_report(self, dms_configuration):
        """Attach report as attachment on chatter of record
            if found with same name deleted and attached a new report to chatter of record"""
        self.ensure_one()
        report_id = dms_configuration.report_id
        _logger.info('Attaching report as attachment')
        attachment = self._retrieve_attachment_report(report_id)
        if attachment:
            _logger.info("Delete exists attachment and linked other")
            attachment.unlink()
        new_attachment = self._generate_attachment(report_id)
        if new_attachment:
            _logger.info("Add a new attachment to chatter of record")
            self.message_post(attachment_ids=[new_attachment.id])

    def _check_send_file_name(self):
        """Check if self is instance of a document object
        get the name of file from a document object

        """
        self.ensure_one()
        if self._name == 'documents.document':
            return self.description
        else:
            return ""

    def _send_request(self, dms_config, attachment=None, **kw):
        """Send API request

        @param dms_config: Dms configuration object
        @param attachment: Attachment related with record for send to api
        """
        attachment_field = kw.get('attachment_field')
        self.ensure_one()
        _logger.info("Send API request")
        if not attachment_field:
            if not dms_config.send_attachments and dms_config.report_id:
                attachment = self._retrieve_attachment_report(dms_config.report_id)
        # Stop used fields
        # Flush fields before fetching from DB
        # self.flush([line.field_id.name for line in dms_config.dms_field_ids])
        dms_config = dms_config.sudo()
        url = dms_config.url
        if not url or not dms_config.api_method:
            return
        today = fields.Datetime.context_timestamp(
            self, datetime.datetime.now()
        )
        if "UploadSingleFile" in url and dms_config.api_method == 'post':
            payload = self._get_body(dms_config)
            params = self._get_params(dms_config)
            headers = {
                'Content-Type': 'application/json; charset=utf-8',
            }
            temporary_data = {
                'dms_api_id': dms_config.id,
                'res_id': self.id,
                'processing_date': fields.Datetime.now(),
                'user_id': self._uid or self.env.user.id,
                'model_id': dms_config.model_id.id,
                'res_model': dms_config.model_id.model,
                'report_id': dms_config.report_id.id,
                'api_method': dms_config.api_method,
            }
            temporary_sudo = self.env['dms.temporary'].sudo()
            # check if attachment
            # file_name = self._check_send_file_name()
            if not attachment_field:
                if dms_config.use_odoo_name and attachment is not None:
                    payload['fileName'] = str(attachment.name)
                elif dms_config.file_name and not dms_config.use_odoo_name:
                    if dms_config.send_datetime:
                        payload['fileName'] = str(dms_config.file_name) + \
                                              today.strftime("%d%m%Y%H%M%S") + ".pdf"
                    else:
                        payload['fileName'] = str(dms_config.file_name)
                else:
                    payload['fileName'] = ''
            else:
                payload['fileName'] = list(attachment_field.keys())[0]

            if dms_config.content_type_id:
                payload['contentTypeName'] = dms_config.content_type_id.name
                temporary_data['content_type_id'] = dms_config.content_type_id.id
            else:
                payload['contentTypeName'] = dms_config.content_type_id.name
            temporary_data['file_name'] = payload['fileName']
            if attachment is not None:
                _logger.info("Send attachment to api")
                payload['fileBytes'] = attachment["datas"]
                temporary_data['attachment'] = attachment.datas
            elif attachment_field is not None and isinstance(attachment_field, dict):
                _logger.info("Send attachment field to api")
                payload['fileBytes'] = list(attachment_field.values())[0]
                temporary_data['attachment'] = payload['fileBytes']
            try:
                payload = json.dumps(payload, ensure_ascii=False, default=date_utils.json_default)
                #  _logger.info("Payload {}".format(payload))
                r = requests.post(url, data=payload.encode('utf-8'), headers=headers, params=params)
                #  _logger.info("Requests URL {}".format(r.url))
                #  _logger.info("Requests Body {}".format(json.loads(r.request.body)))
                #  _logger.info("Requests Header {}".format(dict(r.request.headers)))
                response = json.loads(r.text)
                if not (response.get('UploadSingleFileResult') and
                        response.get('UploadSingleFileResult').get('Code') != 'OK'):
                    temporary_data['response'] = r.text
                    temporary_data['request'] = payload
                    temporary_data['processed'] = True
                    temporary_sudo.create(temporary_data)
            except Exception as e:
                _logger.info("Error while calling dms API {}".format(str(e)))
                temporary_data['response'] = str(e)
                temporary_data['request'] = payload
                temporary_data['processed'] = False
                temporary_sudo.create(temporary_data)
                # raise UserError(f'Error {str(e)}')

    def write(self, vals):
        _logger.info('Getting dms configuration')
        self_sudo = self.sudo()
        # if self._name == 'stock.picking':
        #     print("stock.picking")
        # if not vals.get('dms_configuration_id'):
        res = super(DmsIntegrationMix, self).write(vals)
        for record in self_sudo:
            values = record._get_dms_integration()
            dms_config = values[0]
            if dms_config:
                state_field_id = values[1]
                state_value_id = values[2]
                state_field_name = state_field_id.name
                _logger.info("Dms Config {}".format(dms_config))
                if record._name == 'stock.picking':
                    _logger.info("Run dms on stock picking")
                    # _logger.info("Vals {}".format(vals))
                    if vals.get("date_done"):
                        # if not record.dms_configuration_id:
                        vals['dms_configuration_id'] = dms_config.id
                        # res = super(DmsIntegrationMix, record).write(vals)
                        _logger.info("Checking if dms configuration has report {} for attachment"
                                     .format(dms_config.report_id))
                        if dms_config.report_id:
                            record._attach_report(dms_config)
                        record.send_data(dms_config)
                else:
                    if state_field_id.name in vals and vals.get(f'{state_field_name}',
                                                                "") == state_value_id.state_value_db:
                        # if not record.dms_configuration_id:
                        vals['dms_configuration_id'] = dms_config.id
                        # res = super(DmsIntegrationMix, record).write(vals)
                        # _logger.info("Checking if dms configuration has report {} for attachment"
                        #              .format(dms_config.report_id))
                        # _logger.info("Vals {}".format(vals))
                        if record._name == 'account.move':
                            _logger.info("DMS on account move")
                        if dms_config.report_id:
                            record._attach_report(dms_config)
                        record.send_data(dms_config)
                    # else:
                    #     res = super(DmsIntegrationMix, self).write(vals)
                # else:
                #     res = super(DmsIntegrationMix, record).write(vals)
        # else:
        #     res = super(DmsIntegrationMix, self).write(vals)
        # res = super(DmsIntegrationMix, self).write(vals)
        return res

    def send_data(self, dms_config=None):
        """Send data to dms based on configuration linked with a current model.

        @param dms_config: Dms configuration object can be passed
                or fetch linked configuration
        """
        _logger.info("Sending data to dms api")
        self.ensure_one()
        dms_config = dms_config or self.dms_configuration_id or self.env['dms.integration']
        if not dms_config:
            _logger.info("Not found dms configuration on this model {}".format(self._name))
            return
        send_attachments_on_field = False
        attachments_on_field = self._get_attachments_on_field(dms_config)
        if attachments_on_field:
            send_attachments_on_field = True
            _logger.info("There are attachments")
            for attachment in attachments_on_field:
                if isinstance(attachment, dict):
                    self._send_request(dms_config, attachment_field=attachment)
        if dms_config.send_attachments:
            _logger.info('Send Attachments on records')
            attachments = self._retrieve_attachment_record()
            if attachments:
                for attachment in attachments:
                    self._send_request(dms_config, attachment)
            elif not send_attachments_on_field:
                _logger.info('No attachments found on this record')
                self._send_request(dms_config)
        else:
            if dms_config.report_id:
                _logger.info("No send attachment but found report")
                self._send_request(dms_config)
            elif not send_attachments_on_field:
                _logger.info("No send attachment and not attachment found on field")
                self._send_request(dms_config)
