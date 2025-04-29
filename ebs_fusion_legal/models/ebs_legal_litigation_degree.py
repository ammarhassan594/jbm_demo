from odoo import fields, models


class ebsLegalLitigationDegree(models.Model):
    _name = 'ebs.legal.litigation.degree'
    _description = 'EBS Legal Litigation Degree'

    name = fields.Char(string='Name')
    arabic_name = fields.Char(string='Arabic Name')
