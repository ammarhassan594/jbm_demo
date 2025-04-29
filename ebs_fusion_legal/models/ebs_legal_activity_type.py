from odoo import api, fields, models, _

class ebsLegalActivityType(models.Model):
    _name = 'ebs.legal.activity.type'
    _description = 'EBS Legal Activity Type'

    name = fields.Char('Name')
