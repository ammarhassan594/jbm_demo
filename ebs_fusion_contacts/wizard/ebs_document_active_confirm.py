from odoo import api, fields, models, _


class ebsdocumentactiveconfirm(models.TransientModel):
    _name = 'ebs.document.active.confirm'
    _description = 'EBS Document Active Confirm'
    
    document_id = fields.Many2one('documents.document')
    partner_id = fields.Many2one('res.partner')
    field_name = fields.Char()
    
    def confirm(self):
        self.document_id.write({'status': 'active'})
        if self.partner_id:
            self.partner_id.write({
                self.field_name: True
            })