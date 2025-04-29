from odoo import api, fields, models, _

class ebsPricelistCategory(models.Model):
    _name = 'ebs.crm.pricelist.category'
    _description = 'EBS CRM Pricelist Category'

    name = fields.Char('Name')

