from odoo import fields, models


class EBSEmpResidence(models.Model):
    _name = 'ebs.emp.residence'
    _description = 'EBS Emp Residence'

    name = fields.Char("Name")
    zone_id = fields.Many2one('ebs.na.zone', string="Zone")
    street = fields.Many2one('ebs.na.street', string="Street")
    building = fields.Many2one('ebs.na.building', string="Building")
    unit = fields.Char('Unit')
