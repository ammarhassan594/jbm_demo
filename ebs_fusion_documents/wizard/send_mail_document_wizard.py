# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import re
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError


class DocumentSendMail(models.TransientModel):
    _name = 'document.send.mail'
    _inherits = {'mail.compose.message': 'composer_id'}
    _description = 'Document Send Mail'


    def get_mail_server(self):
        mail_server_id = self.env['ir.mail_server'].sudo().search([], order='sequence asc', limit=1)
        return mail_server_id

    def get_related_partner(self):
        domain = []
        partner_lst = []
        if self.env.context.get('active_doc'):
            active_records = self.env[self.env.context.get('default_model')].browse(self.env.context.get('active_doc'))
            doc_with_emp = active_records.filtered(lambda x: x.employee_id.id)
            doc_without_emp = active_records.filtered(lambda x: not x.employee_id.id)
            partner_ids = []
            if doc_without_emp:
                partner_ids += active_records.mapped('partner_id').ids
            elif doc_with_emp:
                partner_ids += active_records.mapped('employee_client_id').ids
            if partner_ids:
                client_rel = self.env['ebs.client.contact'].search([('client_id','in',partner_ids)])
                if client_rel:
                    partner_ids += client_rel.mapped('partner_id.id')
            domain = [('id', 'in', partner_ids)]
            return domain

    template_id = fields.Many2one(
        'mail.template', 'Use template', index=True)
    composer_id = fields.Many2one('mail.compose.message', string='Composer', required=True, ondelete='cascade')
    recipient_ids = fields.Many2many(comodel_name = 'res.partner',relation ='ebs_document_mail_contact',column1 ='document_id',column2="partner_id",domain=get_related_partner)
    mail_server_id = fields.Many2one('ir.mail_server', 'Outgoing mail server',default=get_mail_server)
    email_to = fields.Char(string='Email To')
    email_from = fields.Char("Email From")
    email_cc = fields.Char(string='Cc')
    body = fields.Html('Contents', default='', sanitize_style=True)

    def action_document_send_mail(self):
        if not self.email_to and not self.recipient_ids:
            raise ValidationError(_('Please set Email To OR Recipient '))
        active_records = self.env[self.env.context.get('default_model')].browse(self.env.context.get('active_doc'))
        ctx = dict(attachment_ids=self.attachment_ids.ids,
                   email_cc=self.email_cc,
                   mail_server=self.mail_server_id.id,
                   subject=self.subject,
                   recipient_ids = self.recipient_ids and [(6,0,self.recipient_ids.ids)],
                   email_to=self.email_to,
                   email_from=self.email_from,
                   body_html = self.body)
        active_records[0].with_context(ctx).send_mail()


    @api.onchange('recipient_ids')
    def onchange_recipient_ids(self):
        email_lst = []
        for rec in self.recipient_ids:
            if not rec.email:
                raise ValidationError(_("The email address of this %s partner has not been set "%(rec.name)))
            email_lst.append(rec.email)
        self.email_to = ",".join(email_lst)

    @api.onchange('mail_server_id')
    def onchange_mail_server_id(self):
        for rec in self:
            rec.email_from = rec.mail_server_id.smtp_user
