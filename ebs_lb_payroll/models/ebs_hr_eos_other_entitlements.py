# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ebsHrEosOtherEntitlements(models.Model):
    _name = 'ebs.hr.eos.other.entitlements'
    _description = 'EOS Other Entitlement'

    type = fields.Many2one('ebs.hr.eos.other.entitlements.types', string="Type", ondelete='restrict')
    # domain = lambda self: [('partner_id', '=', self.env.context.get('default_partner_id')), (
    # 'document_type_id', '=', self.env['ebs.document.type'].sudo().search([('name', '=', 'Passport')]).id)]
    label = fields.Char(string="Label")
    amount = fields.Float(string="Amount")
    end_of_service_id = fields.Many2one('ebs.mod.end.of.service.payment.request', string="End Of Service")

    @api.onchange('type')
    def onchange_type(self):
        for rec in self:
            if rec.end_of_service_id.eos_config_id:
                type_ids = rec.end_of_service_id.eos_config_id.entitlements_types_ids
                return {'domain': {'type': [('id', 'in', type_ids.ids)]}}


