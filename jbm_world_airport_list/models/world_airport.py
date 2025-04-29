from odoo import models, fields, api
from odoo.exceptions import ValidationError


class WorldAirportsList(models.Model):
    _name = 'world.airport'
    _description = "World Airports List"

    name = fields.Char(string="City/Airport", required=True)
    country = fields.Char(string="Country")
    code = fields.Char(string="IATA code", required=True)

    @api.constrains('name')
    def constrains_unique_name(self):
        old_names = self.search([('id', '!=', self.id)])
        for rec in old_names:
            name = self.name.strip().lower()
            if rec.name.strip().lower() == name:
                raise ValidationError('This name already exists!')

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        domain = args + ['|', ('code', operator, name), ('name', operator, name)]
        res = super(WorldAirportsList, self).search(domain, limit=limit).name_get()
        # TODO: Can you try another solution
        """    
        solve issue appears on making a relation many2one with another model
         and select airport odoo search with id only
            name_get returns res  [(airport_id, 'airport_name')]
            this object can't search on it because odoo searches with id 
        so fetch airports ids only
        """
        return [airport[0] for airport in res]
