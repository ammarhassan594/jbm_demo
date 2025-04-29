# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class DependentsFares(models.Model):
    _name = 'dependents.fares'
    _description = 'Dependents Fares'
    _rec_name = 'destination'

    # destination = fields.Char(string="Destination", default="", required=True)
    destination = fields.Many2one(comodel_name="world.airports", string="Destination", required=True, )

    adult_fare = fields.Monetary(string='Adult Fare')

    child_fare = fields.Monetary(string='Child Fare')

    infant_fare = fields.Monetary(string='Infant Fare', )

    date_year = fields.Date(string="Year", default=lambda self: fields.Datetime.now(), required=True)
    travel_class = fields.Selection(string="Travel Class", default="b",
                                    selection=[('b', 'Business'), ('e', 'Economy')], required=False, )

    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)

    # _sql_constraints = [('unique_destination_and_year', 'unique(destination,year)',
    #                      'Duplicate Destination with the same year is not allowed!')]

    @api.constrains('destination', 'date_year', 'travel_class')
    def fares_constraints(self):
        for rec in self:
            fares = rec.search([('id', '!=', rec.id)])
            for fare in fares:
                if fare.destination == rec.destination and fare.date_year.year == rec.date_year.year \
                        and fare.travel_class == rec.travel_class:
                    raise ValidationError('Duplicating destination with same year and travel class is not allowed')
