# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class Survey(models.Model):
    _inherit = 'survey.survey'

    category = fields.Selection(selection_add=[('hr_recruitment', 'Recruitment')])


class SurveyInvite(models.TransientModel):
    _inherit = 'survey.invite'

    def _send_mail(self, answer):
        mail_server_id = self.env['ir.mail_server'].sudo().search([], order='sequence asc', limit=1)
        if mail_server_id:
            self.email_from = mail_server_id.smtp_user
        return super(SurveyInvite, self)._send_mail(answer)
