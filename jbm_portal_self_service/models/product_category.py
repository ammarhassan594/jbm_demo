from odoo import models, fields, api, _


class InheritProductCategory(models.Model):
    _inherit = 'product.category'

    select_type = fields.Selection([
        ('it_equipment', 'IT Equipment'),
        ('training_course', 'Training Course Request'),
        ('insurance_request', 'Insurance Request'), ])