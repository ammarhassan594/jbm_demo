from odoo import api, fields, models, _


class activity_activity(models.Model):
    _inherit = 'mail.activity'

    hubspot_id = fields.Char("Hubspot ID")


class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    def action_send_mail(self):
        res = super(MailComposer, self).action_send_mail()
        if self._context.get('proposal_send'):
            stage_id = self.env['crm.stage'].search([('code', '=', 4)])
            lead = self.env['crm.lead'].browse(self._context.get('default_res_id'))
            lead.write({'stage_id': stage_id.id})
        return res
