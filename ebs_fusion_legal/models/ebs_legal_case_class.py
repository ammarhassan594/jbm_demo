from odoo import api, fields, models


class ebsLegalCaseClass(models.Model):
    _name = 'ebs.legal.case.class'
    _description = 'EBS Legal Case Class'

    name = fields.Char('Name')
    arabic_name = fields.Char(string='Arabic Name')
    case_type_id = fields.Many2one(comodel_name='ebs.legal.case.type', string='Case Type')


class ebsLegalCasePartialClass(models.Model):
    _name = 'ebs.legal.case.partial.class'
    _description = 'EBS Legal Case Partial Class'

    name = fields.Char('Name')
    arabic_name = fields.Char(string='Arabic Name')
