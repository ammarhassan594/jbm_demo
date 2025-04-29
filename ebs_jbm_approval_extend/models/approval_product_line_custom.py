# -*- coding: utf-8 -*-
import logging
from odoo.exceptions import UserError

from odoo.osv import expression
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class ApprovalProductLineCustom(models.Model):
    _inherit = 'approval.product.line'

    account_id = fields.Many2one('account.account', string="Account id")
    is_finance_manager = fields.Boolean(string="Is Finance Manager", compute="compute_is_finance_manager")
    is_available = fields.Boolean(string="Available On Stock", readonly=True)
    virtual_available = fields.Float(string="Forecasted Quantity", readonly=True)
    qty_available = fields.Float(related='product_id.qty_available')
    location_id = fields.Many2one(
        'stock.location',
        string='Source Location',
    )
    dest_location_id = fields.Many2one(
        'stock.location',
        string='Destination Location',
        required=False,
    )

    picking_type_id = fields.Many2one(
        'stock.picking.type',
        string='Picking Type',
    )

    @api.depends()
    def compute_is_finance_manager(self):
        for record in self:
            if self.env.user.has_group('account.group_account_manager'):
                record.is_finance_manager = True
            else:
                record.is_finance_manager = False

    @api.onchange('product_id', 'account_id')
    def onchange_product_id_custom(self):
        if self.product_id and self.product_id.property_account_expense_id and self.env.user.has_group(
                'account.group_account_manager'):
            self.account_id = self.product_id.property_account_expense_id
        elif self.product_id and not self.product_id.property_account_expense_id and self.account_id and self.env.user.has_group(
                'account.group_account_manager'):
            self.product_id.sudo().write({'property_account_expense_id': self.account_id.id})

    @api.onchange('product_id')
    def get_related_product_fields(self):
        if self.product_id:
            print('qty_available', self.qty_available)
            self.virtual_available = self.product_id.virtual_available
            _logger.info('Product availability')
            _logger.info('qty_available {}, virtual_available {}, free_qty {}'.
                         format(self.product_id.qty_available, self.product_id.virtual_available,
                                self.product_id.free_qty))
            current = self.product_id._compute_quantities_dict(self.product_id._context.get('lot_id'),
                                                               self.product_id._context.get('owner_id'),
                                                               self.product_id._context.get('package_id'),
                                                               self.product_id._context.get('from_date'),
                                                               self.product_id._context.get('to_date'))
            if self.product_id.qty_available > 0:
                material_location = self.env['stock.location'].search([('is_material_request_location', '=', True)],
                                                                      limit=1)
                internal_transfer = self.env['stock.picking.type'].search([('code', '=', 'internal')], limit=1)

                self.is_available = True
                self.dest_location_id = material_location.id
                self.picking_type_id = internal_transfer.id
            else:
                self.is_available = False
        else:
            self.is_available = False
            self.virtual_available = 0

    def _check_products_vendor(self):
        """ Raise an error if at least one product that not available in stock requires a seller. """
        product_lines_without_seller = self.filtered(lambda line: not line._get_seller_id() and not line.is_available)
        if product_lines_without_seller:
            product_names = product_lines_without_seller.product_id.mapped('display_name')
            raise UserError(
                _('Please set a vendor on product(s) %s.') % ', '.join(product_names)
            )

    def _get_purchase_order_values(self, vendor):
        """ Get some values used to create a purchase order.
        Called in approval.request `action_create_purchase_orders`.

        :param vendor: a res.partner record
        :return: dict of values
        """
        self.ensure_one()
        picking_type = self._get_picking_type()
        mr_user = None
        mr_request = None
        if self.approval_request_id:
            if self.approval_request_id.requester_id:
                mr_user = self.sudo().approval_request_id.requester_id.id
            if self.approval_request_id.approval_request_id:
                mr_request = self.sudo().approval_request_id.approval_request_id.id

        vals = {
            'origin': self.approval_request_id.name,
            'partner_id': vendor.id if vendor else False,
            'company_id': self.company_id.id,
            'payment_term_id': vendor.property_supplier_payment_term_id.id if vendor else False,
            'fiscal_position_id': self.env['account.fiscal.position'].get_fiscal_position(
                vendor.id).id if vendor else False,
            'approval_request_id': self.sudo().approval_request_id.id,
            'mr_request_id': mr_request,
            'mr_user_id': mr_user,
            'first_approval_request': self._context.get('first_approval_request')
        }
        if picking_type:
            vals['picking_type_id'] = picking_type.id
        return vals

    def _get_purchase_orders_domain(self, vendor):
        """ Override to filter purchase orders on warehouse. """
        domain = super()._get_purchase_orders_domain(vendor)
        domain = expression.AND([
            domain,
            [('approval_request_id', '=', self.approval_request_id.id)]
        ])
        return domain
