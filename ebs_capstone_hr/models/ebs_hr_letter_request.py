# -*- coding: utf-8 -*-

import base64
import os

try:
    from docx import Document
except ImportError:
    pass
try:
    from docx.enum.text import WD_ALIGN_PARAGRAPH
except ImportError:
    pass
try:
    from docx.shared import Pt
except ImportError:
    pass

from odoo import models, fields, _, api
from odoo.exceptions import ValidationError

_request_type = [
    ('letter_to_embassy', 'NOC For Family Visa'),
    ('salary_breakdown', 'Experience Certificate'),
    ('open_bank_account', 'Salary in Details'),
    ('salary_certificate', 'Salary Certificate'),
    ('salary_transfer_letter', 'Salary Transfer Letter'),
]

AVAILABLE_PRIORITIES = [
    ('0', 'Low'),
    ('1', 'Medium'),
    ('2', 'High'),
    ('3', 'Very High'),
]


class EBSHRLetterRequest(models.Model):
    _name = 'ebs.hr.letter.request'
    _inherit = ['mail.thread']
    _description = 'Letter Request'

    def _get_default_employee_id(self):
        return self.env.user.employee_id.id or False

    def _get_domain_employee_id(self):
        if self.env.user.has_group('base.group_user') and not self.env.user.has_group('hr.group_hr_user'):
            return [('id', '=', self.env.user.employee_id.id)]
        else:
            return [(1, '=', 1)]

    name = fields.Char('Letter Request No.', default='New')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, index=True,
                                  default=_get_default_employee_id, domain=_get_domain_employee_id)
    date = fields.Date(string='Date', required=True, default=fields.Datetime.now(),)
    priority = fields.Selection(AVAILABLE_PRIORITIES, string='Priority', index=True,
                                default=AVAILABLE_PRIORITIES[0][0],
                                help='The priority of the request, as an integer: 0 means higher priority, 10 means '
                                     'lower priority.')
    type = fields.Selection(_request_type, required=True, default="", string='Type')
    addressed_to = fields.Char(string='Addressed To', required=True, copy=False)
    signatory_id = fields.Many2one('hr.employee', string='Signatory', required=False,
                                   domain=[('signatory', '=', True)])
    description = fields.Text(string="Description", copy=False)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)
    state = fields.Selection([
        ('draft', 'draft'),
        ('submitted', 'Submitted'),
        ('under_process', 'Under Process'),
        ('ready_for_collection', 'Ready for Collection'),
        ('done', 'Done'),
        ('rejected', 'Rejected')], string='Status', readonly=True, default='draft')

    @api.onchange('employee_id')
    def _onchange_helpdesk_move_domain(self):
        return {'domain': {'signatory_id': [('id', '!=', self.employee_id.id), ('signatory', '=', True)]}}

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_under_process(self):
        self.write({'state': 'under_process'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_submit(self):
        self.ensure_one()
        if self.name == _('New'):
            self.name = self.env['ir.sequence'].next_by_code('ebs.hr.letter.request') or _('New')
        self.write({'state': 'submitted'})
        self._send_email()

    def action_ready_for_collection(self):
        self.ensure_one()
        self.write({'state': 'ready_for_collection'})
        self._send_email()

    def action_done(self):
        self.ensure_one()
        self.write({'state': 'done'})

    # def get_letter_request_link(self):
    #     menu_id = self.env.ref('ebs_capstone_hr.menu_ebs_hr_letter_request').id or False
    #     action_id = self.env.ref('ebs_capstone_hr.open_view_ebs_hr_letter_request').id or False
    #     base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
    #     return base_url + '/web#action=' + str(action_id) + '&id=' + str(self.id) + '&menu_id=' + str(
    #         menu_id) + '&model=' + self._name + '&view_type=form'

    def _send_email(self):
        template_id = False
        if self.state == 'submitted':
            template_id = self.env.ref('ebs_capstone_hr.submitted_letter_request_email_template').id
        elif self.state == 'ready_for_collection':
            template_id = self.env.ref('ebs_capstone_hr.ready_for_collection_letter_request_email_template').id
        if template_id:
            template = self.env['mail.template'].browse(template_id)
            template.send_mail(self.id, force_send=True)

    @api.constrains('type', 'state')
    def _check_values(self):
        for rec in self:
            if rec.state == 'under_process':
                if rec.type == 'letter_to_embassy':
                    if not rec.employee_id.country_id:
                        raise ValidationError(_("Please, fill Employee's Country name"))
                    elif not rec.employee_id.qid_doc_number:
                        raise ValidationError(_("Please, fill Employee's QID"))
                    elif not rec.employee_id.joining_date:
                        raise ValidationError(_("Please, fill Employee's Joining date"))
                    elif not rec.employee_id.job_title:
                        raise ValidationError(_("Please, fill Employee's Job Title"))
                    elif not rec.employee_id.contract_id.gross_salary:
                        raise ValidationError(_("Please, fill Employee's Gross Salary"))

                if rec.type == 'salary_breakdown':
                    if not rec.employee_id.qid_doc_number:
                        raise ValidationError(_("Please, fill Employee's National ID"))
                    # elif not rec.employee_id.passport_doc_number:
                    #     raise ValidationError(_("Please, fill Employee's Passport number"))
                    elif not rec.employee_id.joining_date:
                        raise ValidationError(_("Please, fill Employee's Joining date"))
                    elif not rec.employee_id.job_title:
                        raise ValidationError(_("Please, fill Employee's Job Title"))

                if rec.type == 'open_bank_account':
                    if not rec.employee_id.qid_doc_number:
                        raise ValidationError(_("Please, fill Employee's National ID"))
                    elif not rec.employee_id.contract_id.gross_salary:
                        raise ValidationError(_("Please, fill Employee's Gross Salary"))
                    elif not rec.employee_id.joining_date:
                        raise ValidationError(_("Please, fill Employee's Joining date"))
                    elif not rec.employee_id.job_title:
                        raise ValidationError(_("Please, fill Employee's Job Title"))

                if rec.type == 'salary_certificate':
                    if not rec.employee_id.country_id.name:
                        raise ValidationError(_("Please, fill Employee's Country name"))
                    elif not rec.employee_id.id:
                        raise ValidationError(_("Please, fill Employee's ID Number"))
                    elif not rec.employee_id.joining_date:
                        raise ValidationError(_("Please, fill Employee's Joining date"))
                    elif not rec.employee_id.qid_doc_number:
                        raise ValidationError(_("Please, fill Employee's National ID"))
                    elif not rec.employee_id.contract_id.gross_salary:
                        raise ValidationError(_("Please, fill Employee's Gross Salary"))

                if rec.type == 'salary_transfer_letter':
                    if not rec.employee_id.country_id:
                        raise ValidationError(_("Please, fill Employee's Country name"))
                    elif not rec.employee_id.id:
                        raise ValidationError(_("Please, fill Employee's ID Number"))
                    elif not rec.employee_id.joining_date:
                        raise ValidationError(_("Please, fill Employee's Joining date"))
                    elif not rec.employee_id.qid_doc_number:
                        raise ValidationError(_("Please, fill Employee's National ID"))
                    elif not rec.employee_id.contract_id.gross_salary:
                        raise ValidationError(_("Please, fill Employee's Gross Salary"))
                    elif not rec.employee_id.contract_id.wage:
                        raise ValidationError(_("Please, fill Employee's Salary"))
                    elif not rec.employee_id.contract_id.site_allowance:
                        raise ValidationError(_("Please, fill Employee's Site Allowance"))
                    elif not rec.employee_id.contract_id.transport_allowance:
                        raise ValidationError(_("Please, fill Employee's Transportation Allowance"))
                    elif not rec.employee_id.contract_id.mobile_allowance:
                        raise ValidationError(_("Please, fill Employee's Mobile Allowance"))
                    elif not rec.employee_id.contract_id.gross_salary:
                        raise ValidationError(_("Please, fill Employee's Gross Salary"))
                    elif not rec.employee_id.contract_id.accommodation:
                        raise ValidationError(_("Please, fill Employee's Accommodation"))
                    elif not rec.employee_id.bank_account_id.acc_number:
                        raise ValidationError(_("Please, fill Employee's Bank Account Number"))
