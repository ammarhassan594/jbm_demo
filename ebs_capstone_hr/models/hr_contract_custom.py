# -*- coding: utf-8 -*-

from datetime import date

from dateutil import relativedelta
from odoo.exceptions import UserError
from odoo import models, fields, api, _


class ContractInherit(models.Model):
    _inherit = 'hr.contract'

    annual_leave = fields.Float(string='Annual Leave')
    # email = fields.Char(default='e.esber@ever-bs.com', string='Email')
    has_reminder = fields.Boolean(string='Has Reminder')
    days = fields.Integer(string='Reminder Days', default='15')
    vacation = fields.Boolean(string='Vacation')
    vacation_schedule = fields.Selection([('12', '12 months'), ('24', '24 months')], string='Vacation Schedule')

    # def check_contract_duration(self):
    #     template_id = self.env.ref('ebs_capstone_hr.contract_template').id
    #     template = self.env['mail.template'].browse(template_id)
    #     for rec in self.env['hr.contract'].search([('state', '=', 'open'), ('has_reminder', '=', True)]):
    #         if rec.date_end:
    #             end_date = rec.date_end
    #             today_date = date.today()
    #             diff = today_date - end_date
    #             result = abs(diff.days)
    #             email_list = []
    #             if result == rec.days:
    #                 for employee in self.env['hr.employee'].search([('department_id.name', '=', 'Human Resources')]):
    #                     email_list.append(employee.work_email)
    #
    #                 if email_list:
    #                     template.write({'email_to': email_list})
    #                     template.send_mail(rec.id, force_send=True)

    def check_probation_contract_duration(self):

        template_id = self.env.ref('ebs_capstone_hr.email_template_probation_reminder').id
        template = self.env['mail.template'].browse(template_id)
        for rec in self.env['hr.contract'].search([('state', '=', 'open')]):
            email_list = []
            if rec.trial_date_end:
                end_date = rec.trial_date_end
                today_date = date.today()
                diff = today_date - end_date
                abs(diff.days)
                result = abs(diff.days)
                if result == 21:
                    for employee in self.env['hr.employee'].search([('department_id.is_human_resource', '=', True)]):
                        email_list.append(employee.work_email)
                    template.write({'email_to': email_list})
                    template.send_mail(rec.id, force_send=True)

    # def check_employee_vacation(self):
    #     template_id = self.env.ref('ebs_capstone_hr.email_template_vacation_reminder').id
    #     template = self.env['mail.template'].browse(template_id)
    #     for rec in self.env['hr.contract'].search([('state', '=', 'open')]):
    #         email_list = []
    #         if rec.date_start and rec.vacation and rec.vacation_schedule == 12 or 24:
    #             start_date = rec.date_start
    #             today = date.today()
    #             num_months = (today.year - start_date.year) * 12 + (today.month - start_date.month)
    #
    #             if num_months == 9 or 21:
    #                 for employee in self.env['hr.employee'].search([('department_id.name', '=', 'Human Resources')]):
    #                     email_list.append(employee.work_email)
    #                 template.write({'email_to': email_list})
    #                 template.send_mail(rec.id, force_send=True)

    @api.onchange('date_start')
    def _onchange_date_start(self):
        self.trial_date_end = self.date_start + relativedelta.relativedelta(months=3)

    # @api.model
    # def _auto_send_email_reminder_of_trial_ended(self):
    #     records = self.search([
    #         ('state', '=', 'open'),
    #         ('has_reminder', '=', True),
    #     ])
    #     ended_trial_records = records.filtered(
    #         lambda r: r.trial_date_end - relativedelta.relativedelta(days=r.days) == date.today())
    #     if len(ended_trial_records) > 0:
    #         hr_manager = self.env['res.users'].search(
    #             [('groups_id.name', '=', 'Administrator'),
    #              ('groups_id.category_id.name', '=', 'Contracts')])
    #         template = self.env.ref('ebs_capstone_hr.hr_contract_trial_end_reminder_email_template')
    #         template.write({'email_to': ",".join(user for user in hr_manager.mapped('email'))})
    #         for record in ended_trial_records:
    #             template.send_mail(record, force_send=True)
