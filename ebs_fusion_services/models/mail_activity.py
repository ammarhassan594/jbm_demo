from odoo import api, fields, models


class MailActivityInherit(models.Model):
    _inherit = 'mail.activity'

    def action_close_dialog(self):
        res = super(MailActivityInherit, self).action_close_dialog()
        self_sudo = self.sudo()
        w_line = self_sudo.env['ebs.crm.proposal.workflow.line'].search([('id', '=', self_sudo.res_id)])
        if self_sudo.res_model_id.name == 'EBS Proposal Workflow Lines':
            if w_line.service_process_id:
                data = {
                    'activity_type_id': self_sudo.activity_type_id.id,
                    'res_model_id': self_sudo.env['ir.model'].search([('model', '=', 'ebs.crm.service.process')]).id,
                    'res_id': w_line.service_process_id.id,
                    'note': self_sudo.note,
                    'summary': w_line.name+ ' '  + self_sudo.summary,
                    'user_id': self_sudo.user_id.id,
                }
                self_sudo.env['mail.activity'].create(data)
        return res
