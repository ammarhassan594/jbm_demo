# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime


class CreateAssetFromPO(models.TransientModel):
    _name = 'ebs.asset.po'
    _description = 'Create Asset From PO wizard'

    asset_type = fields.Char(
        string='Asset Type',
        required=False)

    po_id = fields.Many2one(
        comodel_name='purchase.order',
        string='Purchase Order',
        required=False)

    po_line_ids = fields.One2many(
        comodel_name='ebs.asset.po.line',
        inverse_name='parent_id',
        string='Products',
        required=False)

    def create_asset(self):
        for line in self.po_line_ids:

            if not line.asset_model:
                raise ValidationError(_("Please select asset model."))

            salvage = 1.0

            vals = {
                'name': line.name,
                'company_id': self.po_id.company_id.id,
                'currency_id': self.po_id.company_id.currency_id.id,
                'po_id': self.po_id.id,
                'po_line_id': line.po_line_id.id,
                'asset_type': self.asset_type,
                'model_id': line.asset_model.id,
                'original_value': line.unit_price,
                'book_value': line.unit_price,
                'value_residual': (line.unit_price - salvage),
                'product_id': line.po_line_id.product_id.id,
                'acquisition_date': line.acquisition_date,
                'salvage_value': salvage,
                'account_asset_id': line.asset_model.account_asset_id.id
            }
            if line.po_line_id.account_analytic_id:
                vals['account_analytic_id'] = line.po_line_id.account_analytic_id.id
            if line.employee_ids:
                vals['employee_id'] = line.employee_ids.id

            if line.po_line_id.account_analytic_id:
                vals['account_analytic_id'] = line.po_line_id.account_analytic_id.id

            asset = self.env['account.asset'].create(vals)

            if line.employee_ids:
                self.env['ebs.asset.transfer.log'].create({
                    'transfer_date': line.acquisition_date,
                    'asset_id': asset.id,
                    'employee_id': line.employee_ids.id
                })
            asset._onchange_model_id()
            if line.is_validate:
                asset.validate()


            msg = _('%s created from purchase order') % (line.po_line_id.product_id.name)
            msg += ': <a href=# data-oe-model=purchase.order data-oe-id=%d>%s</a>' % (
                self.po_id.id, self.po_id.name)
            asset.message_post(body=msg)

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }


class CreateAssetFromPOLine(models.TransientModel):
    _name = 'ebs.asset.po.line'
    _description = 'Create Asset From PO Line'

    parent_id = fields.Many2one(
        comodel_name='ebs.asset.po',
        string='Asset Purchase Order',
        required=True)

    po_line_id = fields.Many2one(
        comodel_name='purchase.order.line',
        string='Product',
        required=True,
    )

    received = fields.Float(
        string='Received',
        related="po_line_id.qty_received",
        required=False
    )
    asset_model = fields.Many2one(
        comodel_name='account.asset',
        string='Asset Model',
        domain=[('state', '=', 'model')],
        required=False)

    asset_created = fields.Integer(
        string='Created Assets',
        related="po_line_id.asset_created_nb",
        required=False)

    assets_to_create = fields.Integer(
        string='Convert to Assets', default=0,
        required=True)
    name = fields.Char(
        string='Name',
        readonly=False,
        required=True)

    unit_price = fields.Float(
        string='Unit Price',
        related="po_line_id.price_unit",
        required=False)

    employee_ids = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        required=False)

    acquisition_date = fields.Date(
        string='Acquisition Date',
        default=datetime.today().date(),
        required=True)

    is_validate = fields.Boolean(
        string='Validate', default=False,
        required=False)

    @api.onchange('po_line_id')
    def po_line_onchange(self):
        result = {
            'domain': {
                'po_line_id': [('order_id', '=', self.parent_id.po_id.id),
                               ('id', 'not in', self.parent_id.po_line_ids.po_line_id.ids),
                               ('product_type', '=', 'product')]
            }
        }
        return result
