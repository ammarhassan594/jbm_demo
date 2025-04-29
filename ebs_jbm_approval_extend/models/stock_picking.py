# -*- coding: utf-8 -*-

from odoo import models, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    material_request_id = fields.Many2one(
        'approval.request',
        string='Material Request',
        readonly=True,
    )

    def action_print_material_request_receipt(self):
        return self.env.ref('ebs_jbm_approval_extend.material_request_receipt_report_action').report_action(self)

    def get_partner_related_user_name(self):
        self.ensure_one()
        return self.env['res.users'].search([('partner_id', '=', self.partner_id.id)])
