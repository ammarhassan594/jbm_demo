# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PayslipSendMail(models.TransientModel):
    _name = 'payslip.send.mail'
    _description = 'Payslip Send Mail'

    template_id = fields.Many2one(
        'mail.template', 'Use template', index=True)


    def send_and_print_action(self):
        active_records = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_ids'))
        for result in active_records:
            mail_obj = self.env['mail.mail']
            mail_template = self.template_id
            mail_id = mail_template.send_mail(result.id)
            mail = mail_obj.browse(mail_id)
            # mail.recipient_ids = self.travel_settings_id.travel_agency_ids
            mail.email_from = self.env.user.email
            mail.reply_to = result.employee_id.work_email
            mail.send()




