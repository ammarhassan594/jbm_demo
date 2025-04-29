import requests
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta
from dateutil import tz

from odoo import fields, models, api, _
from odoo.addons.ake_attendance_sheet.tools.custom_dateutil import time_to_float
from odoo.addons.resource.models.resource import float_to_time
import pytz
import calendar

import logging

_logger = logging.getLogger(__name__)


class JustificationHrAttendance(models.Model):
    _inherit = 'hr.attendance'

    last_late_in_time = fields.Datetime(string="Last Late In Time")
    last_early_out_time = fields.Datetime(string="Last Early Out Time")

    ########
    # Business Logic
    ########

    def send_sms_justification(self, receiver_phone, message):
        url = self.env['ir.config_parameter'].sudo().get_param('ooredoo_url')
        customer_id = self.env['ir.config_parameter'].sudo().get_param('ooredoo_customerID')
        user_name = self.env['ir.config_parameter'].sudo().get_param('ooredoo_username')
        user_password = self.env['ir.config_parameter'].sudo().get_param('ooredoo_password')

        # phone = '201144868697'
        phone = receiver_phone
        # phonenumbers = self._prepare_sms_numbers()

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
                response = requests.post(url, data=xml_payload.encode('utf-8'), headers=headers)
            except Exception as e:
                _logger.info(f"Error: {str(e)}")

            # print(xml_payload)
            # print(response.content)
            # print('status of sending message:////', response.status_code)

    #######
    # Core Method
    #######
    def _enable_late_check_in(self, late_check_in_hours):
        """Override to add last late check in time
        """
        super(JustificationHrAttendance, self)._enable_late_check_in(late_check_in_hours)
        self.last_late_in_time = fields.Datetime.now()
        # message = "تم تسجيل تأخيرك عن الدوام لمدة {} بتاريخ {} "f
        # message = f"تم تسجيل تأخيرك عن الدوام لمدة {late_check_in_hours} بتاريخ {date.today()}"
        # self.send_sms_justification(self.employee_id.work_phone, message)
        # self.send_sms_message()

    def get_month_residual_violation_hour(self, violation_state=False):
        self.ensure_one()

        max_allowed_violation_hours = self.employee_id.company_id.max_allowed_hours

        month_first_date_time = self.check_in.replace(day=1, hour=0, minute=0, second=0).astimezone(
            pytz.UTC).replace(tzinfo=None)

        current_month_violation_records = self.sudo().search([
            ('employee_id', '=', self.employee_id.id), ('check_in', '>=', month_first_date_time),
            ('check_out', '<=', self.check_in.astimezone(pytz.UTC).replace(tzinfo=None)),
            '|', ('late_check_in_hour', '!=', False), ('early_check_out_hour', '!=', False)])

        current_month_violation_hours = sum(
            current_month_violation_records.mapped('late_check_in_hour') +
            current_month_violation_records.mapped('early_check_out_hour')
        )

        residual_allowed_violation_hours = (max_allowed_violation_hours - current_month_violation_hours) \
            if (max_allowed_violation_hours - current_month_violation_hours > 0.0) else 0.0
        # try:
        if violation_state == 'late_check_in':
            residual_hours_time = \
                float_to_time(round(residual_allowed_violation_hours - self.late_check_in_hour) if (
                        residual_allowed_violation_hours - self.late_check_in_hour > 0) else 0.0)
        else:
            residual_hours_time = \
                float_to_time(
                    round(residual_allowed_violation_hours - (self.late_check_in_hour + self.early_check_out_hour)) if (
                            residual_allowed_violation_hours - (
                            self.late_check_in_hour + self.early_check_out_hour) > 0) else 0.0)
        # except Exception as e:
        #     residual_hours_time = float_to_time(0.0)
        #     _logger.info(f"Error: {str(e)}")

        return residual_hours_time

    # @api.constrains('late_check_in_hour', 'is_early_check_out')
    # def send_justification_sms(self):
    #     for rec in self.filtered(lambda attendance: attendance.is_late_check_in or attendance.is_early_check_out):
    #
    #         employee_number = rec.employee_id.work_phone
    #         message = ''
    #
    #         if rec.early_check_out_hour:
    #             late_time = float_to_time(rec.early_check_out_hour)
    #             residual_hours_time = rec.get_month_residual_violation_hour(violation_state='early_check_out')
    #             message = 'تم تسجيل خروجك مبكرا عن الدوام لمدة {} بتاريخ {} يرجى تعبئة التبرير إن وجد في نظام موارد،\nمدة السماح المتبقية لديكم هي {}'.format(
    #                 late_time.strftime("%H:%M"),
    #                 rec.check_in.date().strftime("%d/%m/%Y"),
    #                 residual_hours_time.strftime("%H:%M")
    #             )
    #
    #         elif rec.late_check_in_hour:
    #             late_time = float_to_time(rec.late_check_in_hour)
    #             residual_hours_time = rec.get_month_residual_violation_hour(violation_state='late_check_in')
    #             message = 'تم تسجيل تأخيرك عن الدوام لمدة {} بتاريخ {} يرجى تعبئة التبرير إن وجد في نظام موارد،مدة السماح المتبقية لديكم هي {}'.format(
    #                 late_time.strftime("%H:%M"),
    #                 rec.check_in.date().strftime("%d/%m/%Y"),
    #                 residual_hours_time.strftime("%H:%M")
    #             )
    # self.send_sms_justification(employee_number, message)

#     @api.constrains('justification_type_id', 'justification')
#     def action_send_notify_by_mails(self):
#         for rec in self:
#             if not rec.employee_id.work_email or not rec.employee_id.parent_id or not rec.employee_id.parent_id.work_email:
#                 continue
#
#             justification_subject = 'تأخير عن الدوام\الخروج المبكر'
#             justification_body = 'تأخر عن الدوام\الخروج المبكر'
#             residual_hours_time = float_to_time(0.0)
#
#             if rec.late_check_in_hour and rec.early_check_out_hour:
#                 justification_subject = 'تأخر عن الدوام\الخروج المبكر'
#                 justification_body = 'تأخر عن الدوام لمدة {} و الخروج المبكر لمدة {} بتاريخ {} '.format(
#                     float_to_time(rec.late_check_in_hour).strftime("%H:%M"),
#                     float_to_time(rec.early_check_out_hour).strftime("%H:%M"),
#                     rec.check_in.date().strftime("%d/%m/%Y"),
#                 )
#                 residual_hours_time = rec.get_month_residual_violation_hour()
#             elif rec.late_check_in_hour:
#                 justification_subject = 'تأخر عن الدوام'
#                 justification_body = 'تأخر عن الدوام لمدة {} بتاريخ {} '.format(
#                     float_to_time(rec.late_check_in_hour).strftime("%H:%M"),
#                     rec.check_in.date().strftime("%d/%m/%Y"),
#                 )
#                 residual_hours_time = rec.get_month_residual_violation_hour(violation_state='late_check_in')
#             elif rec.early_check_out_hour:
#                 justification_subject = 'خروج المبكر'
#                 justification_body = 'خروج المبكر لمدة {} بتاريخ {} '.format(
#                     float_to_time(rec.early_check_out_hour).strftime("%H:%M"),
#                     rec.check_out.date().strftime("%d/%m/%Y"),
#                 )
#                 residual_hours_time = rec.get_month_residual_violation_hour()
#
#             template_id = self.env.ref('jbm_notification_justification.justification_notify_manager').id
#             template = self.env['mail.template'].browse(template_id)
#             template.subject = 'اشعار تقديم تبرير لل{}  من الموظف {} بتاريخ {}'.format(
#                 justification_subject, rec.employee_id.arabic_name if rec.employee_id.arabic_name else '',
#                 rec.check_in.date().strftime("%d/%m/%Y"))
#             template.email_from = rec.employee_id.work_email
#             template.email_to = rec.employee_id.parent_id.work_email
#             template.body_html = """
# تم تقديم تبرير لل{} للموظف: {},   يرجى مراجعة التبرير في نظام موارد
# <br/>
# مدة السماح المتبقية لدى الموظف: {}
# """.format(
#                 justification_body,
#                 rec.employee_id.arabic_name if rec.employee_id.arabic_name else '',
#                 residual_hours_time.strftime("%H:%M")
#             )
#             template.send_mail(rec.id, force_send=True)

    def _disable_late_check_in(self):
        """Override to clear last late check in time"""
        super(JustificationHrAttendance, self)._disable_late_check_in()
        self.last_late_in_time = False

    def _enable_early_check_out(self, early_check_out_hours):
        """Override to add last early check out time"""
        super(JustificationHrAttendance, self)._enable_early_check_out(early_check_out_hours)
        self.last_early_out_time = fields.Datetime.now()

    def _disable_early_check_out(self):
        """Override to clear last early check out time"""
        super(JustificationHrAttendance, self)._disable_early_check_out()
        self.last_early_out_time = False

    ###########
    # Cron Job
    ###########

    @api.model
    def send_notification_early_check_out(self):
        pass
        # current_date_beginning = datetime.combine(date.today(), time(00, 00, 00))
        # current_date_ending = datetime.combine(date.today(), time(23, 59, 59))
        # employee_sudo = self.env['hr.employee'].sudo()
        # attendances = self.read_group(
        #     domain=[
        #         ('check_out', '!=', False),
        #         ('check_in', '>=', current_date_beginning),
        #         ('check_out', '<=', current_date_ending),
        #     ],
        #     fields=['ids:array_agg(id)', 'employee_id'],
        #     groupby=['employee_id'], lazy=False)
        # attendance_vals = {
        #     f"{attendance_val.get('employee_id', ())[0]}": {
        #         "attendance": self.browse(attendance_val.get('ids', [])).
        #         sorted(key=lambda x: x.check_out, reverse=True),
        #     } for attendance_val in attendances
        # }
        #
        # for key, item in attendance_vals.items():
        #     employee = employee_sudo.browse(int(key))
        #     attendance = item.get('attendance') and item.get('attendance')[0]
        # if attendance.is_early_check_out:
        #     message = "Dear %s, You have today early check out " % employee.name
        #     attendance.send_sms_justification(employee.work_phone, message)
        # attendance.send_sms_message()

    @api.model
    def reject_justification_after_time(self):
        reject_after = self.env.company.reject_after
        if reject_after < 0:
            return
        datetime_now = fields.Datetime.now()
        reject_after_date = datetime_now + relativedelta(hours=-reject_after)
        justifications = self.search([
            '&', '|',
            ('last_late_in_time', '<=', reject_after_date),
            ('last_early_out_time', '<=', reject_after_date),
            '|',
            ('is_late_check_in', '=', True),
            ('is_early_check_out', '=', True),
        ])
        """
    filtered(lambda justification: justification.reject_after and
                                   (justification.create_date + relativedelta(
                                       days=justification.reject_after)).date() <= fields.Date.today())
        """
        for justification in justifications:
            all_day_attendance = self.env['hr.attendance']
            attendance_day_start = justification.check_in.replace(hour=0, minute=0, second=0).astimezone(
                pytz.UTC).replace(tzinfo=None).strftime('%Y-%m-%d %H:%M:%S')
            attendance_day_end = justification.check_in.replace(hour=23, minute=59, second=59).astimezone(
                pytz.UTC).replace(tzinfo=None).strftime('%Y-%m-%d %H:%M:%S')
            query = """SELECT id FROM hr_attendance WHERE employee_id = %s AND check_in BETWEEN %s AND %s """
            self._cr.execute(query, (justification.employee_id.id, attendance_day_start, attendance_day_end))
            existing_record_ids = self._cr.fetchall()
            if existing_record_ids:
                existing_record_ids = [rec_id[0] for rec_id in list(existing_record_ids)]
                all_day_attendance = self.env['hr.attendance'].browse(existing_record_ids).sorted('check_in')

            # if (justification.justification_type_id or \
            #         justification.justification and
            #         (
            #                 justification.attendance_status in
            #                 ['department_manager_approve', 'hr_manager'] or
            #                 justification.attendance_status_early in
            #                 ['department_manager_approve', 'hr_manager']
            #         )):
            #     users = self.env.ref('jbm_group_access_right_extended.custom_hr_manager').users
            #     if justification.is_late_check_in:
            #         note = _(
            #             'Please approve on Attendance %(name)s late check in on employee %(employee)s',
            #             name=justification.name_get()[0][1],
            #             employee=justification.employee_id.name,
            #         )
            #         for user in users:
            #             justification.activity_schedule(
            #                 'ake_early_late_attandence.mail_activity_approve_late_check_in_attendance',
            #                 note=note,
            #                 user_id=user.id)
            #     if justification.is_early_check_out:
            #         note = _(
            #             'Please approve on Attendance %(name)s early check out on employee %(employee)s',
            #             name=justification.name_get()[0][1],
            #             employee=justification.employee_id.name,
            #         )
            #         for user in users:
            #             justification.activity_schedule(
            #                 'ake_early_late_attandence.mail_activity_approve_early_check_out_attendance',
            #                 note=note,
            #                 user_id=user.id)
            # elif (
            if (
                    justification.attendance_status in
                    ['department_manager_approve', 'hr_manager'] or
                    justification.attendance_status_early in
                    ['department_manager_approve', 'hr_manager']
            ) and not (
                    justification.justification_type_id or
                    justification.justification):
                from_zone = tz.gettz('UTC')
                to_zone = tz.gettz('Asia/Qatar' or self._context.get('tz'))
                justification_checkin_utc = justification.check_in and \
                                            datetime.strptime(str(justification.check_in),
                                                              '%Y-%m-%d %H:%M:%S').replace(
                                                tzinfo=from_zone)
                justification_checkout_utc = justification.check_out and \
                                             datetime.strptime(str(justification.check_out),
                                                               '%Y-%m-%d %H:%M:%S').replace(
                                                 tzinfo=from_zone)
                justification_checkin_central = justification_checkin_utc and \
                                                justification_checkin_utc.astimezone(to_zone)
                justification_checkout_central = justification_checkout_utc and \
                                                 justification_checkout_utc.astimezone(to_zone)
                # activity = self.env.ref('ake_early_late_attandence.mail_activity_approve_attendance').id
                # attendance.sudo()._get_user_approval_activities(user=self.env.user, activity_type_id=activity).action_feedback()
                justification_date = justification_checkin_utc.date().strftime("%Y-%m-%d")
                if all_day_attendance:
                    qatar_tz = pytz.timezone('Asia/Qatar')
                    check_in = all_day_attendance[0].check_in.astimezone(qatar_tz).replace(tzinfo=None)
                    check_out = all_day_attendance[-1].check_out.astimezone(qatar_tz).replace(tzinfo=None)
                else:
                    check_in = justification_checkin_central
                    check_out = justification_checkout_central
                vals = {
                    "check_in": time_to_float(check_in),
                    "check_out": time_to_float(check_out),
                    "attendance_id": justification.id
                }

                if justification.attendance_status_early in ['department_manager_approve', 'hr_manager'] \
                        and justification.is_early_check_out and justification.early_check_out_hour > 0.0:
                    vals.update({
                        "early_check_out": justification.early_check_out_hour,
                    })
                    justification.attendance_sheet_id = justification.employee_id.updated_or_create_attendance_sheet(
                        attendance_date=justification_date,
                        **vals)
                    justification.is_early_check_out_hour_added = True
                    justification.is_early_check_out = False
                    # justification.activity_update('remove_early_check_out')
                    justification.attendance_status_early = 'rejected'

                if justification.attendance_status in ['department_manager_approve', 'hr_manager'] \
                        and justification.is_late_check_in and justification.late_check_in_hour > 0.0:
                    # violation_hours = attendance.employee_id.violation_hours + attendance.late_check_in_hour
                    # attendance.employee_id.sudo().write({'violation_hours': violation_hours})
                    vals.update({
                        "late_check_in": justification.late_check_in_hour,
                    })
                    justification.attendance_sheet_id = justification.employee_id.updated_or_create_attendance_sheet(
                        attendance_date=justification_date,
                        **vals)
                    justification.is_late_check_in_hour_added = True
                    justification.is_late_check_in = False
                    # justification.activity_update('remove_late_check_in')
                    justification.attendance_status = 'rejected'

    @api.model
    def update_last_time_justification(self):
        attendance_non_lasted = self.search([
            '&', '|', ('last_late_in_time', '=', False),
            ('last_early_out_time', '=', False),
            '|',
            ('is_late_check_in', '=', True),
            ('is_early_check_out', '=', True),
        ])

        for attend in attendance_non_lasted:
            if not attend.last_late_in_time:
                attend.last_late_in_time = attend.write_date
            if not attend.last_early_out_time:
                attend.last_early_out_time = attend.write_date
