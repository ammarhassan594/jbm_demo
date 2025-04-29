from odoo import fields, models, _, api


class EbsServiceGroupsLine(models.Model):
    _name = 'ebs.crm.service.groups.line'
    _description = 'EBS CRM Service Group Line'

    sequence = fields.Integer(string="Sequence", copy=False, index=True, store=True)
    group_id = fields.Many2one('ebs.crm.service.groups', string="Group")
    services_id = fields.Many2one('ebs.crm.service', string="Service")

