from odoo import api, fields, models, _

class ebsCrmServiceStage(models.Model):
    _name = 'ebs.crm.service.stage'
    _description = 'EBS CRM Service Stage'

    name = fields.Char('Name')
    state = fields.Selection([
        ('active', 'Active'),
        ('pending', 'pending'),
        ('closed','Closed'),
    ], default="active")
    activity_ids = fields.One2many('ebs.crm.service.activity', 'stage_id', string="Activities")

