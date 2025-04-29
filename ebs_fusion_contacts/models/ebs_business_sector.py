from odoo import api, fields, models, _


class Authorised_Signatory(models.Model):
    _name = 'ebs.business.sector'
    _description = "Ebs Business Sector"

    name = fields.Char('Name', required=1)
