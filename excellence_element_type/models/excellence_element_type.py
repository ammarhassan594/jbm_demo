from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ExcellenceElementsType(models.Model):
    _name = 'excellence.element.type'

    name = fields.Char()

    @api.constrains('name')
    def constrains_unique_namen(self):
        old_names = self.search([('id', '!=', self.id)])
        for rec in old_names:
            name = self.name.strip().lower()
            if rec.name.strip().lower() == name:
                raise ValidationError('This name already exists!')