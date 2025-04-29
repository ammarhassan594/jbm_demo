from odoo import models, fields, api, _
from datetime import datetime

class TransferDocumentWizard(models.TransientModel):
    _name = 'ebs.transfer.document.wizard'
    _description = 'Transfer Document Wizard'

    transfer_date = fields.Datetime('Transfer Date',default=datetime.today())
    receiver = fields.Many2one('res.users', 'Receiver')
    description = fields.Text('Description')

    @api.onchange('receiver')
    def onchange_receiver(self):
        users = self.env['res.users'].search(['!',('id','=',self.env.uid)])
        return {'domain': {
            'receiver': [('id', 'in', users.ids)],
        }}

    def confirm_button(self):
        log_id = self.env['ebs.transfer.document.log'].search([('document_id','=',self.env.context.get('active_id')),('state','=','pending')])
        if log_id:
            log_id.unlink()
        self.env['ebs.transfer.document.log'].create({
            'sender':self.env.uid,
            'receiver': self.receiver.id,
            'transfer_date': self.transfer_date,
            'description': self.description,
            'document_id': self.env.context.get('active_id'),
            'state':'pending'
        })
