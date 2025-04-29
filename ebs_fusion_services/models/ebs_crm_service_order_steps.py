from odoo import api, fields, models, _

class ebsCrmServiceOrderSteps(models.Model):
    _name = 'ebs.crm.service.order.steps'
    _description = 'EBS CRM Service Order Steps'

    name = fields.Char('Name')

