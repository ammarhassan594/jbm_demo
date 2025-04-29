# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import date


class InheritHLeave(models.Model):
    _inherit = 'hr.leave'

    validation_document_after = fields.Integer(related='holiday_status_id.validation_document_after', store=True)

    @api.constrains('validation_document_after', 'supported_attachment_ids')
    def _restrict_supported_attachment(self):
        for rec in self:
            if rec.validation_document_after and rec.validation_document_after <= rec.number_of_days:
                raise UserError(_('Please attach file in supported attachments'))

    # @api.model_create_multi
    # def create(self, vals_list):
    #     holidays = super(InheritHLeave, self).create(vals_list)
    #     for holiday in holidays:
    #         hr_managers = self.env.ref('jbm_group_access_right_extended.custom_hr_manager').users
    #         for notify_user in hr_managers:
    #             holiday.activity_schedule('ebs_hr_leave_custom.mail_activity_leave_created', user_id=notify_user.id,
    #                                       note='للتكرم بمراجعة طلب الإجازة على نظام موارد.')
    #     return holidays

    def activity_update(self):
        res = super(InheritHLeave, self).activity_update()
        for holiday in self:
            holiday = holiday.sudo()
            if holiday.state == 'confirm':
                user_id = holiday.sudo()._get_responsible_for_approval() or self.env.user
                template_id = self.env.ref('jbm_hr_leave_custom.leave_notify_approver').id
                template = self.env['mail.template'].browse(template_id)
                template.subject = 'إشعار طلب اعتماد إجازة'
                template.email_from = holiday.employee_id.work_email if holiday.employee_id else False
                template.email_to = user_id.employee_id.work_email if user_id and user_id.employee_id else False
                template.body_html = """
                           تم تقديم طلب إجازة ({})  بتاريخ من {}إلى  {} للموظف : {}، يرجى مراجعة الطلب في نظام موارد.
                           """.format(
                    holiday.with_context(lang='ar_001').holiday_status_id.name,
                    holiday.request_date_from,
                    holiday.request_date_to,
                    holiday.employee_id.arabic_name
                )
                template.send_mail(holiday.id, force_send=True, raise_exception=False)

        return res

    def action_approve(self):
        res = super().action_approve()
        for holiday in self:
            holiday = holiday.sudo()
            if holiday.validation_type == 'both' and holiday.state == 'validate1':
                user_id = holiday.holiday_status_id.responsible_id
                template_id = self.env.ref('jbm_hr_leave_custom.leave_notify_approver').id
                template = self.env['mail.template'].browse(template_id)
                template.subject = 'إشعار طلب اعتماد إجازة'
                template.email_from = holiday.employee_id.work_email if holiday.employee_id else False
                template.email_to = user_id.employee_id.work_email if user_id and user_id.employee_id else False
                template.body_html = """
                                          تم تقديم طلب إجازة ({})  بتاريخ من {}إلى  {} للموظف : {}، يرجى مراجعة الطلب في نظام موارد.
                                          """.format(
                    holiday.with_context(lang='ar_001').holiday_status_id.name,
                    holiday.request_date_from,
                    holiday.request_date_to,
                    holiday.employee_id.arabic_name
                )
                template.send_mail(holiday.id, force_send=True, raise_exception=False)

        return res

    def unlink(self):
        res = super(InheritHLeave, self).unlink()

        self.env['resource.calendar.leaves'].search([('holiday_id', 'in', self.ids)]).unlink()

        return res
