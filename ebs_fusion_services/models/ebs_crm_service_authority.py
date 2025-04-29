from odoo import api, fields, models, _

class ebsServiceAuthority(models.Model):
    _name = 'ebs.crm.service.authority'
    _description = 'EBS CRM Service Authority'

    name = fields.Char('Name')
    code = fields.Char('Code')

