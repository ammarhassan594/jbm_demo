# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons.mail.wizard.mail_compose_message import _reopen
from odoo.exceptions import UserError
from odoo.tools.misc import get_lang


class JobOfferSend(models.TransientModel):
    _name = 'job.offer.send'
    _inherits = {'mail.compose.message': 'composer_id'}
    _description = 'Job Offer Send'

    is_email = fields.Boolean('Email', default=True)
    is_print = fields.Boolean('Print')
    contract_ids = fields.Many2many('hr.contract', 'hr_contract_job_offer_send_rel', string='Contracts')
    composer_id = fields.Many2one('mail.compose.message', string='Composer', required=True, ondelete='cascade')
    template_id = fields.Many2one(
        'mail.template', 'Use template', index=True,
        domain="[('model', '=', 'hr.contract')]"
    )

    @api.model
    def default_get(self, fields):
        res = super(JobOfferSend, self).default_get(fields)
        res_ids = self._context.get('active_ids')

        contracts = self.env['hr.contract'].browse(res_ids)
        if not contracts:
            raise UserError(_("You can only send contracts."))

        composer = self.env['mail.compose.message'].create({
            'composition_mode': 'comment' if len(res_ids) == 1 else 'mass_mail',
        })
        res.update({
            'contract_ids': res_ids,
            'composer_id': composer.id,
        })
        return res

    @api.onchange('contract_ids')
    def _compute_composition_mode(self):
        for wizard in self:
            wizard.composer_id.composition_mode = 'comment' if len(wizard.contract_ids) == 1 else 'mass_mail'

    @api.onchange('template_id')
    def onchange_template_id(self):
        for wizard in self:
            if wizard.composer_id:
                wizard.composer_id.template_id = wizard.template_id.id
                wizard.composer_id._onchange_template_id_wrapper()

    @api.onchange('is_email')
    def onchange_is_email(self):
        if self.is_email:
            if not self.composer_id:
                res_ids = self._context.get('active_ids')
                self.composer_id = self.env['mail.compose.message'].create({
                    'composition_mode': 'comment' if len(res_ids) == 1 else 'mass_mail',
                    'template_id': self.template_id.id
                })
            self.composer_id._onchange_template_id_wrapper()

    def _send_email(self):
        if self.is_email:
            self.composer_id._action_send_mail()
            # if self.env.context.get('mark_offer_as_sent'):
            #     self.mapped('contracts_ids').write({'offer_sent': True})

    def _print_document(self):
        """ to override for each type of models that will use this composer."""
        self.ensure_one()
        action = self.contract_ids.action_offer_print()
        action.update({'close_on_report_download': True})
        return action

    def send_and_print_action(self):
        self.ensure_one()
        # Send the mails in the correct language by splitting the ids per lang.
        # This should ideally be fixed in mail_compose_message, so when a fix is made there this whole commit should be reverted.
        # basically self.body (which could be manually edited) extracts self.template_id,
        # which is then not translated for each customer.
        if self.composition_mode == 'mass_mail' and self.template_id:
            active_ids = self.env.context.get('active_ids', self.res_id)
            active_records = self.env[self.model].browse(active_ids)
            # langs = active_records.mapped('partner_id.lang')
            default_lang = get_lang(self.env)
            # # for lang in (set(langs) or [default_lang]):
            # for lang in [default_lang]:
            #     active_ids_lang = active_records.filtered(lambda r: r.partner_id.lang == lang).ids
            self_lang = self.with_context(active_ids=active_records)
            self_lang.onchange_template_id()
            self_lang._send_email()
        else:
            self._send_email()
        if self.is_print:
            return self._print_document()
        return {'type': 'ir.actions.act_window_close'}

    def save_as_template(self):
        self.ensure_one()
        self.composer_id.save_as_template()
        action = _reopen(self, self.id, self.model, context=self._context)
        action.update({'name': _('Send Job Offer')})
        return action
