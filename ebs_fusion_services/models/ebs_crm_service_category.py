from odoo import api, fields, models, _

class ebsServiceCategory(models.Model):
    _name = 'ebs.crm.service.category'
    _description = 'EBS CRM Service Category'

    name = fields.Char('Name')

