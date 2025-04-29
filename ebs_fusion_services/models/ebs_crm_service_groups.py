from odoo import fields, models, _, api

class EbsServiceGroups(models.Model):
    _name = 'ebs.crm.service.groups'
    _description = 'EBS CRM Service Group'

    name = fields.Char('Name')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm')
    ], default="draft")
    group_line_ids = fields.One2many('ebs.crm.service.groups.line', 'group_id', string="Group Line")


    @api.onchange('group_line_ids')
    def group_line_ids_onchnage(self):
        counter = 0
        for rec in self.group_line_ids:
            rec.sequence = counter + 1
            counter += 1




