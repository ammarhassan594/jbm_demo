from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    deposit_default_product_id = fields.Many2one(
        'product.product',
        'Deposit Product',
        domain="[('type', '=', 'service')]",
        config_parameter='ebs_fusion_services.default_deposit_product_id',
        help='Default product used for payment advances')