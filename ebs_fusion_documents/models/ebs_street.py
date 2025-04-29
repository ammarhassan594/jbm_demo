from odoo import api, fields, models, _


class ebsNAStreet(models.Model):
    _name = 'ebs.na.street'
    _description = 'EBS NA Street'

    name = fields.Char('Name')
    zone_id = fields.Many2one('ebs.na.zone', 'Zone')


class ebsNAZone(models.Model):
    _name = 'ebs.na.zone'
    _description = 'EBS NA Zone'

    name = fields.Char('Name')


class ebsNABuilding(models.Model):
    _name = 'ebs.na.building'
    _description = 'EBS NA Building'

    name = fields.Char('Name')
    street_id = fields.Many2one('ebs.na.street', 'Street')


class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    address_type = fields.Selection(
        [('head_office', 'Head Office'),
         ('local_office', 'Local Office'),
         ('Work_sites', 'Work Sites'),
         ("labor_accommodation", "Labor Accommodation"),
         ("national_address", "National Address"),
         ], string='Contact Address Type')

    is_shareholder = fields.Boolean(string="Is Shareholder")
