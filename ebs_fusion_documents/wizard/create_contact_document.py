# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CreateContactDocument(models.TransientModel):
    _name = 'ebs_mod.contact.document'
    _description = 'Create documents for contacts wizard'

    document_number = fields.Char(
        string='Document Number',
        required=True)

    issue_date = fields.Date(
        string='Issue Date',
        required=True)
    expiry_date = fields.Date(
        string='Expiry Date',
        required=False)
    contact_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required=False)


    desc = fields.Text(
        string="Description",
        required=False)

    document_type_id = fields.Many2one(
        comodel_name='ebs.document.type',
        string='Document Type',
        required=True)


    def create_document(self):
        folder = self.env['documents.folder'].search([('is_default_folder', '=', True)], limit=1)
        if len(self.attachment_ids) == 0 or len(self.attachment_ids) > 1:
            raise ValidationError(_("Select 1 File"))


        vals = {
            'document_type_id': self.document_type_id.id,
            'document_number': self.document_number,
            'issue_date': self.issue_date.strftime("%Y-%m-%d"),
            'desc': self.desc,
            'tag_ids': self.tags,
            'attachment_id': self.attachment_ids[0].id,
            'type': 'binary',
            'folder_id': folder.id,
        }
        if self.env.context.get('upload_contact', False):
            vals['partner_id'] = self.contact_id.id

        if self.expiry_date:
            vals['expiry_date'] = self.expiry_date.strftime("%Y-%m-%d")
        self.env['documents.document'].create(vals)
        self.env.cr.commit()
