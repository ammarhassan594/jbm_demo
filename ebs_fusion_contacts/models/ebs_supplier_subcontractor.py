from odoo import api, fields, models, _


class ebsSupplierSubcontractor(models.Model):
    _name = 'ebs.supplier.subcontractor'
    _description = 'EBS Supplier Subcontractor'

    name = fields.Char(string='Name')
    country_of_operation = fields.Many2one(comodel_name='res.country', string='Country Of Operation')
    website = fields.Char(string='Website')
    primary_contact_name = fields.Char(string='Primary Contact Name')
    primary_contact_number = fields.Char(string='Primary Contact Number')
    primary_contact_email = fields.Char(string='Primary Contact Email')
    license = fields.Char(string='License')
    partner_id = fields.Many2one(comodel_name='res.partner')
