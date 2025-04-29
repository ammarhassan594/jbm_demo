# -*- coding: utf-8 -*-

from odoo import api, exceptions, fields, models, _
import requests
import logging

_logger = logging.getLogger(__name__)


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    from_view = fields.Boolean(string="From View", default=False, copy=True)

    def write(self, vals):
        print('hello')
        return super(self, MailActivity).write(vals)

    def action_feedback_schedule_next(self, feedback=False):
        action = super(MailActivity, self).action_feedback_schedule_next(feedback)
        action['context'].update({
            'default_from_view': True
        })
        return action

    def send_sms_justification(self, receiver_phone, message):
        url = self.env['ir.config_parameter'].sudo().get_param('ooredoo_url')
        customer_id = self.env['ir.config_parameter'].sudo().get_param('ooredoo_customerID')
        user_name = self.env['ir.config_parameter'].sudo().get_param('ooredoo_username')
        user_password = self.env['ir.config_parameter'].sudo().get_param('ooredoo_password')

        phone = receiver_phone

        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': 'http://pmmsoapmessenger.com/HTTP_SendSms',
        }
        if phone:
            xml_payload = """
        <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                       xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                       xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
          <soap:Body>
            <HTTP_SendSms xmlns="http://pmmsoapmessenger.com/">
            """ + """<customerID>""" + str(customer_id) + """</customerID>""" + """<userName>""" + str(
                user_name) + """</userName>""" + """<userPassword>""" + str(
                user_password) + """</userPassword>""" + """<originator>JASIM</originator>""" + """<smsText>""" + str(
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
            try:
                requests.post(url, data=xml_payload.encode('utf-8'), headers=headers)
            except Exception as e:
                _logger.info(f"Error: {str(e)}")

    def action_close_dialog(self):
        for activity in self:
            create_employee = activity.create_uid.employee_id
            assigned_employee = activity.user_id.employee_id
            if activity.from_view and create_employee and create_employee.work_email and assigned_employee \
                    and assigned_employee.work_email:
                template_id = self.env.ref('mail_custom.manual_activity_email').id
                template = self.env['mail.template'].browse(template_id)
                model = activity.sudo().res_model_id
                if model.model == 'approval.request':
                    res_id = activity.env['{}'.format(model.model)].search([('id', '=', activity.res_id)])
                    template.subject = '{}'.format(activity.activity_type_id.with_context(lang='ar_001').name)
                    template.email_from = create_employee.work_email
                    template.email_to = assigned_employee.work_email
                    initial_div = f'<div style="text-align:right; direction:rtl;">'
                    email_body = "تم جدولة النشاط للطلب رقم ({} - {}) من قبل الموظف: {}، يرجى مراجعة الطلب في نظام موارد".format(
                        res_id.name, res_id.category_id.with_context(lang="ar_001").name, create_employee.arabic_name)
                    message = email_body
                    end_div = '</div>'
                    email_body += '\n'
                    if activity.summary:
                        email_body += "{}".format(activity.summary)
                    email_body += '\n'
                    if activity.note:
                        email_body += "{}".format(activity.note)
                    email_body = initial_div + email_body + end_div
                    template.body_html = email_body
                    template.send_mail(activity.id, force_send=True)
                    assigned_employee.sudo().with_context(message=message).send_sms_message()
                elif model.send_activity_mail:
                    res_id = activity.env['{}'.format(model.model)].search([('id', '=', activity.res_id)])
                    name = model.field_name.with_context(lang='ar_001').name
                    type = model.field_type.with_context(lang='ar_001').name
                    if model.field_name.ttype == 'many2one':
                        name = res_id['{}'.format(name)].with_context(lang='ar_001').name
                    else:
                        name = res_id.with_context(lang='ar_001')['{}'.format(name)]
                    if model.field_type.ttype == 'many2one':
                        type = res_id['{}'.format(type)].with_context(lang='ar_001').name
                    else:
                        type = res_id.with_context(lang='ar_001')['{}'.format(type)]
                    template.subject = '{}'.format(activity.activity_type_id.with_context(lang='ar_001').name)
                    template.email_from = create_employee.work_email
                    template.email_to = assigned_employee.work_email
                    initial_div = f'<div style="text-align:right; direction:rtl;">'
                    email_body = "إشعار طلب استكمال/اعتماد إجراء بشأن: ({} / {} / {})".format(name, type,
                                                                                              model.with_context(
                                                                                                  lang='ar_001').name)
                    message = email_body
                    end_div = '</div>'
                    email_body += '\n'
                    if activity.summary:
                        email_body += "{}".format(activity.summary)
                    email_body += '\n'
                    if activity.note:
                        email_body += "{}".format(activity.note)
                    email_body = initial_div + email_body + end_div
                    template.body_html = email_body
                    template.send_mail(activity.id, force_send=True)
                    assigned_employee.sudo().with_context(message=message).send_sms_message()
        return super(MailActivity, self).action_close_dialog()

    def action_done(self, feedback=False, attachment_ids=None):
        for activity in self:
            create_employee = activity.create_uid.employee_id
            assigned_employee = activity.user_id.employee_id
            if create_employee and create_employee.work_phone and activity.from_view:
                template_id = self.env.ref('mail_custom.manual_activity_email').id
                template = self.env['mail.template'].browse(template_id)
                model = activity.sudo().res_model_id
                if model.name == 'Approval Request':
                    res_id = activity.env['{}'.format(model.model)].search([('id', '=', activity.res_id)])
                    template.subject = '{}'.format(activity.activity_type_id.with_context(lang='ar_001').name)
                    template.email_from = assigned_employee.work_email
                    template.email_to = create_employee.work_email
                    initial_div = f'<div style="text-align:right; direction:rtl;">'
                    email_body = "تم الانتهاء من النشاط المجدول للطلب رقم ({} - {}) من قبل الموظف: {}، يرجى مراجعة الطلب في نظام موارد".format(
                        res_id.name, res_id.category_id.with_context(lang="ar_001").name, assigned_employee.arabic_name)
                    message = email_body
                    end_div = '</div>'
                    email_body += '\n'
                    if activity.summary:
                        email_body += "{}".format(activity.summary)
                    email_body += '\n'
                    if activity.note:
                        email_body += "{}".format(activity.note)
                    email_body = initial_div + email_body + end_div
                    template.body_html = email_body
                    template.send_mail(activity.id, force_send=True)
                    create_employee.sudo().with_context(message=message).send_sms_message()
                elif model.send_activity_mail:
                    res_id = activity.env['{}'.format(model.model)].search([('id', '=', activity.res_id)])
                    name = model.field_name.with_context(lang='ar_001').name
                    type = model.field_type.with_context(lang='ar_001').name
                    if model.field_name.ttype == 'many2one':
                        name = res_id['{}'.format(name)].with_context(lang='ar_001').name
                    else:
                        name = res_id.with_context(lang='ar_001')['{}'.format(name)]
                    if model.field_type.ttype == 'many2one':
                        type = res_id['{}'.format(type)].with_context(lang='ar_001').name
                    else:
                        type = res_id.with_context(lang='ar_001')['{}'.format(type)]
                    template.subject = '{}'.format(activity.activity_type_id.with_context(lang='ar_001').name)
                    template.email_from = create_employee.work_email
                    template.email_to = assigned_employee.work_email
                    initial_div = f'<div style="text-align:right; direction:rtl;">'
                    email_body = "إشعار طلب استكمال/اعتماد إجراء بشأن: ({} / {} / {})".format(name, type,
                                                                                              model.with_context(
                                                                                                 lang='ar_001').name)
                    message = email_body
                    end_div = '</div>'
                    email_body += '\n'
                    if activity.summary:
                        email_body += "{}".format(activity.summary)
                    email_body += '\n'
                    if activity.note:
                        email_body += "{}".format(activity.note)
                    email_body = initial_div + email_body + end_div
                    template.body_html = email_body
                    template.send_mail(activity.id, force_send=True)
                    create_employee.sudo().with_context(message=message).send_sms_message()
        return super(MailActivity, self).action_done()

    # Override To prevent send message when create activity
    def action_notify(self):
        if not self:
            return
        original_context = self.env.context
        body_template = self.env.ref('mail.message_activity_assigned')
        for activity in self:
            if activity.user_id.lang:
                # Send the notification in the assigned user's language
                self = self.with_context(lang=activity.user_id.lang)
                body_template = body_template.with_context(lang=activity.user_id.lang)
                activity = activity.with_context(lang=activity.user_id.lang)
            model_description = self.env['ir.model']._get(activity.res_model).display_name
            body = body_template._render(
                dict(
                    activity=activity,
                    model_description=model_description,
                    access_link=self.env['mail.thread']._notify_get_action_link('view', model=activity.res_model,
                                                                                res_id=activity.res_id),
                ),
                engine='ir.qweb',
                minimal_qcontext=True
            )
            body_template = body_template.with_context(original_context)
            self = self.with_context(original_context)

    def _action_done(self, feedback=False, attachment_ids=None):
        for activity in self:
            create_employee = activity.create_uid.employee_id
            assigned_employee = activity.user_id.employee_id
            if create_employee and create_employee.work_phone and activity.from_view and assigned_employee:
                template_id = self.env.ref('mail_custom.manual_activity_email').id
                template = self.env['mail.template'].browse(template_id)
                model = activity.sudo().res_model_id
                if model.model == 'approval.request':
                    res_id = activity.env['{}'.format(model.model)].search([('id', '=', activity.res_id)])
                    template.subject = '{}'.format(activity.activity_type_id.with_context(lang='ar_001').name)
                    template.email_from = assigned_employee.work_email
                    template.email_to = create_employee.work_email
                    initial_div = f'<div style="text-align:right; direction:rtl;">'
                    email_body = "تم الانتهاء من النشاط المجدول للطلب رقم ({} - {}) من قبل الموظف: {}، يرجى مراجعة الطلب في نظام موارد".format(
                        res_id.name, res_id.category_id.with_context(lang="ar_001").name, assigned_employee.arabic_name)
                    message = email_body
                    end_div = '</div>'
                    email_body += '\n'
                    if activity.summary:
                        email_body += "{}".format(activity.summary)
                    email_body += '\n'
                    if activity.note:
                        email_body += "{}".format(activity.note)
                    email_body = initial_div + email_body + end_div
                    template.body_html = email_body
                    template.send_mail(activity.id, force_send=True)
                    create_employee.sudo().with_context(message=message).send_sms_message()
                elif model.send_activity_mail:
                    res_id = activity.env['{}'.format(model.model)].search([('id', '=', activity.res_id)])
                    name = model.field_name.with_context(lang='ar_001').name
                    type = model.field_type.with_context(lang='ar_001').name
                    if model.field_name.ttype == 'many2one':
                        name = res_id['{}'.format(name)].with_context(lang='ar_001').name
                    else:
                        name = res_id.with_context(lang='ar_001')['{}'.format(name)]
                    if model.field_type.ttype == 'many2one':
                        type = res_id['{}'.format(type)].with_context(lang='ar_001').name
                    else:
                        type = res_id.with_context(lang='ar_001')['{}'.format(type)]
                    template.subject = '{}'.format(activity.activity_type_id.with_context(lang='ar_001').name)
                    template.email_from = create_employee.work_email
                    template.email_to = assigned_employee.work_email
                    initial_div = f'<div style="text-align:right; direction:rtl;">'
                    email_body = "إشعار طلب استكمال/اعتماد إجراء بشأن: ({} / {} / {})".format(name, type,
                                                                                              model.with_context(
                                                                                                 lang='ar_001').name)
                    message = email_body
                    end_div = '</div>'
                    email_body += '\n'
                    if activity.summary:
                        email_body += "{}".format(activity.summary)
                    email_body += '\n'
                    if activity.note:
                        email_body += "{}".format(activity.note)
                    email_body = initial_div + email_body + end_div
                    template.body_html = email_body
                    template.send_mail(activity.id, force_send=True)
                    create_employee.sudo().with_context(message=message).send_sms_message()
        return super(MailActivity, self)._action_done(feedback=feedback, attachment_ids=attachment_ids)
