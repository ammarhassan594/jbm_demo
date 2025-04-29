from datetime import date
from odoo import fields,api,models,_


class UpdateDocument(models.TransientModel):
    _name = 'update.document'
    _description = 'Update Document'

    file = fields.Binary(string='File', attachment=True, required=True)
    file_name = fields.Char('File name')

    def update_document(self):
        if self.file_name:
            current_document = self.env['documents.document'].browse(self._context.get('active_id'))
            new_document = current_document.with_context({'update_doc': True}).copy()
            attachment_64 = self.env['ir.attachment'].create({
                'name': self.file_name,
                'datas': self.file,
                'type': 'binary',
            })
            new_document.with_context({'update_doc': True}).write({
                'attachment_id': attachment_64.id,
                'document_ids': [(4, current_document.id, 0)],
            })
            new_document.version += current_document.version
            active_doc = self.env['documents.document'].browse(self.env.context['active_id'])
            active_doc.toggle_active()
            active_doc.status = 'expired'
            if not active_doc.expiry_date or (active_doc.expiry_date and active_doc.expiry_date > date.today()):
                active_doc.expiry_date = date.today()



            return {
                'name': _('Documents'),
                'res_model': 'documents.document',
                'view_mode': 'form',
                'res_id' :new_document.id,
                'context': self.env.context,
                'target': 'self',
                'type': 'ir.actions.act_window',
            }
