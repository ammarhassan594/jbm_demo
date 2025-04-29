from odoo import api, fields, models, _

class ebsLegalLawFirms(models.Model):
    _name = 'ebs.legal.law.firm'
    _description = 'EBS Legal Law Firm'

    name = fields.Char('Name')
