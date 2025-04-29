# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    accommodation_type = fields.Selection([
        ('house', 'House'),
        ('hotel', 'Hotel'),
    ], string='Accommodation Type')
    
    
