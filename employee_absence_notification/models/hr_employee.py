import datetime
from datetime import date
import time
import requests
import logging
import pytz

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class InheritHrEmployee(models.Model):
    _inherit = 'hr.employee'

    def _get_integration_configuration(self):
        integration_configuration = self.env['dynamic.integration.configuration'].search([
            ('model', '=', 'hr.employee'),
        ], limit=1)
        object = integration_configuration if integration_configuration else False
        return object

    def _get_proxies(self):
        configuration_id = self._get_integration_configuration()
        proxies = {}
        if configuration_id:
            if configuration_id.http_proxy:
                proxies['http'] = configuration_id.http_proxy
            if configuration_id.https_proxy:
                proxies['https'] = configuration_id.https_proxy

        return proxies

    def send_sms_absences_to_manager(self, receiver_phone, receiver_name=False, employees=None, sms_message=False):
        if employees is None:
            employees = []
        url = self.env['ir.config_parameter'].sudo().get_param('ooredoo_url')
        customer_id = self.env['ir.config_parameter'].sudo().get_param('ooredoo_customerID')
        user_name = self.env['ir.config_parameter'].sudo().get_param('ooredoo_username')
        user_password = self.env['ir.config_parameter'].sudo().get_param('ooredoo_password')
        message = ''
        if sms_message:
            message = sms_message
        elif receiver_name:
            message = "Dear %s, These are today's absent employees: %s", [employees], receiver_name

        proxies = self._get_proxies()
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
            response = requests.post(url, data=xml_payload.encode('utf-8'), headers=headers, proxies=proxies)

            print(xml_payload)
            print(response.content)
            print('status of sending message:////', response.status_code)

    def send_absence_to_direct_manager(self):
        absence_employees = self.get_absence_employees()
        direct_managers = self.env['hr.employee'].search([]).mapped('parent_id')
        direct_managers = set(direct_managers.filtered(lambda x: x.job_id.id != 40))

        if direct_managers:
            for direct_manager in direct_managers:
                employees = absence_employees.filtered(lambda x: x.parent_id.id == direct_manager.id)
                if employees:
                    template = self.env.ref('employee_absence_notification.mail_template_of_absent_employees',
                                            raise_if_not_found=False)
                    emails = []
                    if direct_manager.work_email not in emails:
                        emails.append(direct_manager.work_email)

                    ctx = {}
                    ctx['email_to'] = ','.join([email for email in emails])
                    ctx['email_from'] = self.env.user.company_id.email
                    ctx['send_email'] = True
                    ctx['absence_employees'] = employees
                    ctx['direct_manager'] = direct_manager
                    ctx['time'] = time.strftime('%Y-%m-%d')
                    initial_div = f'<div style="text-align:right; direction:rtl;">'
                    first_body_part = "تم تسجيل غياب  عن الدوام بتاريخ " + f"{time.strftime('%Y-%m-%d')}" + " للموظفين التاليين: " + "<br/>"
                    second_body_part= "<br/>" + '<ul>'
                    for employee in employees:
                        second_body_part += f'<li>{employee.arabic_name if employee.arabic_name else employee.name}</li>'
                    template.body_html = initial_div + first_body_part + second_body_part + '</ul>' + '</div>'

                    template.with_context(ctx, absence_employees=employees,
                                          direct_manager=direct_manager).send_mail(self.id, force_send=True,
                                                                                   raise_exception=False)

                    # self.send_sms_absences_to_manager(direct_manager.work_phone, direct_manager.name,
                    #                                   employees.mapped('name'))
                    # for hr_manager in hr_managers:
                    #     self.send_sms_absences_to_manager(hr_manager.mobile, hr_manager.name, employees.mapped('name'))

    def get_absence_employees(self):
        start_date_time = datetime.datetime.now().replace(hour=0, minute=0, second=0).astimezone(
            pytz.UTC).replace(tzinfo=None)

        all_employees = self.env['hr.employee'].search([('out_of_attendance', '!=', True)])
        # present_employees = self.env['hr.attendance'].search([('check_in', '>=', start_date_time)]).mapped(
        #     'employee_id')
        present_employees = self.env['machine.attendance.record'].search([('punch_time', '>=', start_date_time)]).mapped(
            'employee_id')

        remaining_employees = all_employees - present_employees
        absence_employees = self.env['hr.employee']

        for employee in remaining_employees:
            weekend = str(start_date_time.today().weekday()) not in set(
                employee.contract_id.resource_calendar_id.attendance_ids.mapped('dayofweek'))

            public_holiday = employee.contract_id.resource_calendar_id.global_leave_ids.filtered(
                lambda x: x.date_from.date() <= start_date_time.date() <= x.date_to.date()) \
                if employee.contract_id else False

            leaves = self.env['hr.leave'].search([
                ('employee_id', '=', employee.id),
                ('request_date_from', '<=', start_date_time.today()),
                ('request_date_to', '>=', start_date_time.today()),
                ('state', '=', 'validate')])

            if not any((weekend, public_holiday, leaves)):
                absence_employees += employee

        return absence_employees

    def send_absence_to_hr_manager(self):
        absence_employees = self.get_absence_employees()
        departments = absence_employees.mapped('department_id.parent_id')
        hr_managers = self.env.ref('jbm_group_access_right_extended.custom_hr_manager').users
        if absence_employees:
            for hr_manager in hr_managers:
                template_id = self.env.ref('employee_absence_notification.absence_notify_hr_manager').id
                template = self.env['mail.template'].browse(template_id)
                template.subject = 'اشعار غياب'
                template.email_from = self.env.user.company_id.partner_id.email
                template.email_to = hr_manager.work_email
                initial_div = f'<div style="text-align:right; direction:rtl;">'
                first_body_part = "تم تسجيل غياب عن الدوام بتاريخ " + f"{date.today()}" + " للموظفين التاليين: " + "<br/>"
                second_body_part = '<br/>'
                for dep in departments:
                    second_body_part += f'<p style="font-weight: bold;">{dep.arabic_name if dep.arabic_name else dep.name}</p>'
                    for employee in absence_employees:
                        if employee.department_id.id in dep.child_ids.ids:
                            second_body_part += f'<li>{employee.arabic_name if employee.arabic_name else employee.name}</li>'
                    second_body_part += f'<br />'
                template.body_html = initial_div + first_body_part + second_body_part + '</div>'

                template.send_mail(self.id, force_send=True, raise_exception=False)

    def send_sms_to_absence_employees(self):
        absence_employees = self.get_absence_employees()
        message = 'تم تسجيل غيابك عن الدوام بتاريخ {}.'.format(
            date.today())
        for employee in absence_employees:
            employee_number = employee.phone_personal
            self.send_sms_absences_to_manager(receiver_phone=employee_number, sms_message=message)

    @api.model
    def get_employees_absences(self):
        try:
            self.send_absence_to_direct_manager()
        except Exception:
            _logger.debug("failed to send absence to direct managers", exc_info=True)

        try:
            self.send_absence_to_hr_manager()
        except Exception:
            _logger.debug("failed to send absence to HR managers", exc_info=True)

        try:
            self.send_sms_to_absence_employees()
        except Exception:
            _logger.debug("failed to send SMS to Absence Employees", exc_info=True)
