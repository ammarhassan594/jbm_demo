import re
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SendMailWizard(models.TransientModel):
    _name = 'send.mail.wizard'
    _description = 'Send Mail Wizard'

    email_to = fields.Char(string='Email To')
    email_cc = fields.Char(string='Cc')
    subject = fields.Char('Subject')
    body = fields.Html('Contents', default='', sanitize_style=True)
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    document_ids = fields.Many2many('documents.document', string="Document",
                                    domain=lambda self: [('id', 'in', self._context.get('document_ids'))])
    mail_server_id = fields.Many2one('ir.mail_server', 'Outgoing mail server')
    email_from = fields.Char(string='Email From')

    @api.constrains('email_to', 'email_from')
    def _check_tenent_email(self):
        expr = "^[a-zA-Z0-9._+]+@[a-zA-Z0-9.-]+\.[a-zA-Z0-9.-]*\.*[a-zA-Z.-]{2,4}$"
        for rec in self:
            if rec.email_from:
                if re.match(expr, rec.email_from) is None:
                    raise ValidationError(
                        _('Please Enter Valid Email From!!'))
            if rec.email_to:
                if re.match(expr, rec.email_to) is None:
                    raise ValidationError(
                        _('Please Enter Valid Email To!!'))

    @api.model
    def default_get(self, fields):
        res = super(SendMailWizard, self).default_get(fields)
        template_id = self._context.get('template_id')
        res_id = self._context.get('res_id')
        temp_vals = self.env['mail.template'].with_context(tpl_partners_only=True).browse(template_id).generate_email(
            res_id, fields=['body_html', 'subject'])
        mail_server_id = self.env['ir.mail_server'].sudo().search([], order='sequence asc', limit=1)
        res.update({'body': temp_vals.get('body_html'),
                    'subject': temp_vals.get('subject'),
                    'mail_server_id': mail_server_id.id})
        return res

    def action_send_mail(self):
        model = self._context.get('model')
        res_id = self._context.get('res_id')
        object = self.env[model].browse(res_id)
        ctx = dict(attachment_ids=self.attachment_ids.ids,
                   email_cc=self.email_cc,
                   email_from=self.email_from,
                   mail_server_id=self.mail_server_id.id,
                   subject=self.subject,
                   email_to=self.email_to,
                   body_html=self.body)
        object.with_context(ctx).send_mail()

    @api.onchange('document_ids')
    def onchange_document_ids(self):
        for rec in self:
            rec.attachment_ids = [(6, 0, rec.document_ids.attachment_id.ids)]

    @api.onchange('mail_server_id')
    def onchange_mail_server_id(self):
        for rec in self:
            rec.email_from = rec.mail_server_id.smtp_user
