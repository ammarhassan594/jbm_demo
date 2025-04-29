from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ebsDocumentTypeFolder(models.Model):
    _name = 'ebs.document.type.folder'
    _description = 'EBS Document Type Folder'

    doc_type_id = fields.Many2one(comodel_name='ebs.document.type', string='Document Type')
    company_id = fields.Many2one(comodel_name='res.company', string='Company')
    folder_id = fields.Many2one(comodel_name='documents.folder', string='Folder')

    @api.constrains('doc_type_id', 'company_id')
    def check_duplicate_for_company(self):
        for rec in self:
            duplicate_rec_id = rec.search([('company_id', '=', rec.company_id.id), ('doc_type_id', '=', self.doc_type_id.id)]) - rec
            if duplicate_rec_id:
                raise UserError(_('Record For %s Company Already Exist.' % rec.company_id.name))
