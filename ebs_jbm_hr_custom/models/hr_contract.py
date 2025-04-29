# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrContractCustom(models.Model):
    _inherit = 'hr.contract'

    scale_configuration_id = fields.Many2one('hr.salary.scale.configuration', string="Salary Scale")

    @api.onchange('accommodation')
    def onchange_accommodation(self):
        if self.scale_configuration_id:
            accommodation_line = self.scale_configuration_id.element_ids.filtered(
                lambda s: s.allowance_type == 'housing_allowance')
            if accommodation_line:
                res = self.with_context(allowance_name='Housing Allowance').check_amount_validation(self.accommodation,
                                                                                                    accommodation_line)
                return res

    @api.onchange('transport_allowance')
    def onchange_transport_allowance(self):
        if self.scale_configuration_id:
            accommodation_line = self.scale_configuration_id.element_ids.filtered(
                lambda s: s.allowance_type == 'transport_allowance')
            if accommodation_line:
                res = self.with_context(allowance_name='Transport Allowance').check_amount_validation(
                    self.transport_allowance,
                    accommodation_line)
                return res

    @api.onchange('living_allowance')
    def onchange_living_allowance(self):
        if self.scale_configuration_id:
            accommodation_line = self.scale_configuration_id.element_ids.filtered(
                lambda s: s.allowance_type == 'living_allowance')
            if accommodation_line:
                res = self.with_context(allowance_name='Living Allowance').check_amount_validation(
                    self.living_allowance,
                    accommodation_line)
                return res

    @api.onchange('other_allowance')
    def onchange_other_allowance(self):
        if self.scale_configuration_id:
            accommodation_line = self.scale_configuration_id.element_ids.filtered(
                lambda s: s.allowance_type == 'other_allowance')
            if accommodation_line:
                res = self.with_context(allowance_name='Other Allowance').check_amount_validation(
                    self.other_allowance,
                    accommodation_line)
                return res

    @api.onchange('food_allowance')
    def onchange_food_allowance(self):
        if self.scale_configuration_id:
            accommodation_line = self.scale_configuration_id.element_ids.filtered(
                lambda s: s.allowance_type == 'food_allowance')
            if accommodation_line:
                res = self.with_context(allowance_name='Food Allowance').check_amount_validation(
                    self.food_allowance,
                    accommodation_line)
                return res


    @api.onchange('mobile_allowance')
    def onchange_mobile_allowance(self):
        if self.scale_configuration_id:
            accommodation_line = self.scale_configuration_id.element_ids.filtered(
                lambda s: s.allowance_type == 'mobile_allowance')
            if accommodation_line:
                res = self.with_context(allowance_name='Mobile Allowance').check_amount_validation(
                    self.mobile_allowance,
                    accommodation_line)
                return res

    @api.onchange('maximum_ticket_allowance')
    def onchange_maximum_ticket_allowance(self):
        if self.scale_configuration_id:
            accommodation_line = self.scale_configuration_id.element_ids.filtered(
                lambda s: s.allowance_type == 'maximum_ticket_allowance')
            if accommodation_line:
                res = self.with_context(allowance_name='Maximum Ticket Allowance').check_amount_validation(
                    self.maximum_ticket_allowance,
                    accommodation_line)
                return res


    def check_amount_validation(self, amount, element_line):
        if amount < element_line.from_amount or amount > element_line.to_amount:
            warning = {
                'title': _('Warning'),
                'message':
                    _('%s amount is not between of salary scale.') % self.env.context.get('allowance_name')}
            return {'warning': warning}
        else:
            {}
