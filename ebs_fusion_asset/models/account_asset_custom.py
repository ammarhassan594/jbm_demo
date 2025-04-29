# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Related Employee',
        required=False)

    department_id = fields.Many2one(
        comodel_name='hr.department',
        string='Department',
        related='employee_id.department_id',
        required=False)

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Related Product',
        required=False)

    po_id = fields.Many2one(
        comodel_name='purchase.order',
        string='Purchase Order',
        required=False)

    po_line_id = fields.Many2one(
        comodel_name='purchase.order.line',
        string='Purchase Order Line',
        required=False)

    contract_id = fields.Many2one(
        comodel_name='ebs.crm.proposal',
        string='Contract',
        )

    type_of_asset = fields.Selection([('hr','HR'),('marketing','Marketing'),('sales','Sales'),('social','Social Media'),
                                   ('legal','Legal'),('account','Account'),('it','Information Technology'),('procurement','Procurement')],
                                  string='Type')

    def go_transfer_log(self):
        self.ensure_one()
        return {
            'name': _('Assets Transfer Log'),
            'res_model': 'ebs.asset.transfer.log',
            'type': 'ir.actions.act_window',
            'views': [(False, 'tree')],
            'view_mode': 'tree',
            'domain': [('asset_id', '=', self.id)]
        }
        
        
    def action_asset_modify(self):
        """ Returns an action opening the asset modification wizard.
        """
        self.ensure_one()
        new_wizard = self.env['asset.modify'].create({
            'asset_id': self.id,
            'name': self.name,
        })
        return {
            'name': _('Modify Asset'),
            'view_mode': 'form',
            'res_model': 'asset.modify',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': new_wizard.id,
            'context': self.env.context,
        }

    def _set_value(self):
        for record in self:
            if not record.acquisition_date:
                record.acquisition_date = min(record.original_move_line_ids.mapped('date') + [
                    record.prorata_date or record.first_depreciation_date or fields.Date.today()])
            record.first_depreciation_date = record._get_first_depreciation_date()
            record.value_residual = record.original_value - record.salvage_value
            record.name = record.name or (record.original_move_line_ids and record.original_move_line_ids[0].name or '')
            if not record.asset_type and 'asset_type' in self.env.context:
                record.asset_type = self.env.context['asset_type']
            if not record.asset_type and record.original_move_line_ids:
                account = record.original_move_line_ids.account_id
                record.asset_type = account.asset_type
            record._onchange_depreciation_account()
