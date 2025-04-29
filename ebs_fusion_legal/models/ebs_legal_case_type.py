from odoo import api, fields, models, _

class ebsLegalCaseType(models.Model):
    _name = 'ebs.legal.case.type'
    _description = 'EBS Legal Case Type'

    name = fields.Char('Name', required=1)


class ebsLegalTypes(models.Model):
    _name = 'ebs.legal.types'
    _description = 'EBS Legal Types'

    name = fields.Char(string='Name', required=1)
