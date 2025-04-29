# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, date


class HrContract(models.Model):
    _inherit = 'hr.contract'

    ticket_type_alw = fields.Selection([
        ('ticket_ALW', 'Ticket Allowance'),
        ('onceayear', 'Company ticket once/year'),
        ('once2year', 'Company ticket once/2 years')
    ],
        string='Ticket Type',
        default='ticket_ALW', help="Select the ticket type")
    amount = fields.Float()

    ticket_allowance = fields.Monetary(
        string='Ticket Allowance', compute='_compute_ticket_allowance', groups="base.group_no_one")

    adult_fare = fields.Monetary(string='Adult Fare', compute='_get_fares')

    child_fare = fields.Monetary(string='Child Fare', compute='_get_fares')

    infant_fare = fields.Monetary(string='Infant Fare', compute='_get_fares')

    number_of_children_allowed = fields.Integer(string="Number of allowed dependents", default=0, required=False)

    # airport_name = fields.Many2one(comodel_name="world.airports", string="Airport", required=False, )
    # required_airport = fields.Boolean(string="is required airport", default=False)
    # year = fields.Date(string="Year", default=lambda self: fields.Datetime.now(), required=True)

    # @api.onchange('airport_name')
    # def _check_airport(self):
    #     for rec in self:
    #         if rec.wassef_employee_type == '' and (rec.employee_id.country_id.code in ['QA', 'QD']
    #                                  or rec.mother_nationality == 'qatari' or rec.employee_id.is_gcc_country):
    #             rec.required_airport = True

    # @api.depends('airport_name')
    def _get_fares(self):
        fares = self.env['dependents.fares'].search([('airport_id', '=', self.airport_id.id)],
                                                    order='year desc', limit=1)
        self.adult_fare = fares.adult_fare
        self.child_fare = fares.child_fare
        self.infant_fare = fares.infant_fare

    @api.onchange('ticket_type_alw')
    def _change_ticket_allowance_value(self):
        for rec in self:
            if rec.ticket_type_alw not in ['ticket_ALW']:
                rec.ticket_allowance = 0
            else:
                rec._compute_ticket_allowance()

    @api.depends('adult_fare', 'child_fare', 'infant_fare', 'number_of_children_allowed')
    def _compute_ticket_allowance(self):
        self.ticket_allowance = 0
        # self._number_of_dependants()
    #
    # def _number_of_dependants(self):
    #     for rec in self:
    #         for line in rec.employee_id.emp_childs:
    #             if line.relation == 'wife':
    #                 self._ticket_allowance_with_wife()
    #                 break
    #             else:
    #                 self._ticket_allowance_without_wife()
    #
    # def _ticket_allowance_with_wife(self):
    #     total_number_of_children = self._number_of_children()
    #     total_number_of_infants = self._number_of_infants()
    #     for rec in self:
    #         allowed_number = rec.number_of_children_allowed
    #         if allowed_number >= (total_number_of_children + total_number_of_infants):
    #             rec.ticket_allowance = 2 * rec.adult_fare + total_number_of_children * rec.child_fare + \
    #                                    total_number_of_infants * rec.infant_fare
    #         else:
    #             if allowed_number <= total_number_of_children:
    #                 rec.ticket_allowance = 2 * rec.adult_fare + allowed_number * rec.child_fare
    #             elif allowed_number <= total_number_of_infants and total_number_of_children == 0:
    #                 rec.ticket_allowance = 2 * rec.adult_fare + allowed_number * rec.infant_fare
    #             else:
    #                 total_number_of_infants = allowed_number - total_number_of_children
    #                 rec.ticket_allowance = 2 * rec.adult_fare + total_number_of_children * rec.child_fare + \
    #                                        total_number_of_infants * rec.infant_fare
    #
    # def _ticket_allowance_without_wife(self):
    #     total_number_of_children = self._number_of_children()
    #     total_number_of_infants = self._number_of_infants()
    #     for rec in self:
    #         allowed_number = rec.number_of_children_allowed
    #         if allowed_number >= (total_number_of_children + total_number_of_infants):
    #             rec.ticket_allowance = rec.adult_fare + total_number_of_children * rec.child_fare + \
    #                                    total_number_of_infants * rec.infant_fare
    #         else:
    #             if allowed_number <= total_number_of_children:
    #                 rec.ticket_allowance = rec.adult_fare + allowed_number * rec.child_fare
    #             elif allowed_number <= total_number_of_infants and total_number_of_children == 0:
    #                 rec.ticket_allowance = rec.adult_fare + allowed_number * rec.infant_fare
    #             else:
    #                 total_number_of_infants = allowed_number - total_number_of_children
    #                 rec.ticket_allowance = rec.adult_fare + total_number_of_children * rec.child_fare + \
    #                                        total_number_of_infants * rec.infant_fare
    #
    # def _number_of_children(self):
    #     for rec in self:
    #         children_total_number = 0
    #         date_of_today = fields.Date.today()
    #         comparing_date = date(date_of_today.year + 1, 1, 1)
    #         # for line in rec.employee_id.emp_childs:
    #         #     age_of_child = (comparing_date - line.date_of_birth).days / 365
    #         #     if 2 <= age_of_child < 12:
    #         #         children_total_number += 1
    #         return children_total_number
    #
    # def _number_of_infants(self):
    #     for rec in self:
    #         infants_total_number = 0
    #         date_of_today = fields.Date.today()
    #         comparing_date = date(date_of_today.year + 1, 1, 1)
    #         # for line in rec.employee_id.emp_childs:
    #         #     age_of_child = (comparing_date - line.date_of_birth).days / 365
    #         #     if 0 < age_of_child < 2:
    #         #         infants_total_number += 1
    #     return infants_total_number
