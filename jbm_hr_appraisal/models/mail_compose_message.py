# -*- coding: utf-8 -*-

from odoo import models


class InheritMailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def _action_send_mail(self, **kwargs):
        for wizard in self:
            if self._context.get('mark_appraisal_batch_as_sent') and \
                    wizard.model == 'hr.appraisal.batch' and wizard.partner_ids:
                # Mark batch as sent
                self.env[wizard.model].sudo().browse(wizard.res_id).state = 'sent'
        return super()._action_send_mail(**kwargs)
