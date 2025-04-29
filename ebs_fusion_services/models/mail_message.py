from odoo import api, fields, models


class MessageInherit(models.Model):
    _inherit = 'mail.message'

    @api.model_create_multi
    def create(self, values_list):
        rec = super(MessageInherit, self).create(values_list)
        for res in rec:
            w_line = self.env['ebs.crm.proposal.workflow.line'].search([('id', '=', res.res_id)])
            if res.model == 'ebs.crm.proposal.workflow.line':
                if w_line.service_process_id:
                    data = {
                        'message_type': res.message_type,
                        'subject': res.subject,
                        'body': w_line.name + '  ' + res.body,
                        'author_id': res.author_id.id,
                        'model': 'ebs.crm.service.process',
                        'res_id': w_line.service_process_id.id,
                    }
                    self.env['mail.message'].create(data)
        return rec