from odoo import models, fields, api, _

from datetime import datetime, timedelta


class InheritEbsDocumentType(models.Model):
    _inherit = 'ebs.document.type'

    notify_before = fields.Integer(string="Notify Before")
    mail_template_id = fields.Many2one('mail.template', string="Mail Template")

    @api.model
    def notify_document_expiry(self):
        current_day = datetime.today()
        documents = self.env['documents.document'].search([('expiry_date', '<=', current_day), ('notify_before', '!=', False)])
        if documents:
            for document in documents:
                # if document.expiry_date and document.document_type_id.notify_before:
                day = document.expiry_date - timedelta(days=document.document_type_id.notify_before)
                if current_day.date() == day:
                    document.document_type_id.mail_template_id.send_mail(document.id)

