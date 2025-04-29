# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date


class ContractInherit(models.Model):
    _inherit = 'hr.contract'

    # payroll_grade = fields.Selection(
    #     string='Payroll Grade',
    #     selection=[('1', 'Grade 1'),
    #                ('2', 'Grade 2'), ('3', 'Grade 3')],
    #     required=False, related="job_id.payroll_grade")

    @api.onchange('wage', 'accommodation', 'mobile_allowance', 'food_allowance', 'transport_allowance',
                  'living_allowance', 'other_allowance')
    def _calculate_package(self):
        for rec in self:
            total = 0
            total += rec.wage or 0
            total += rec.accommodation or 0
            total += rec.mobile_allowance or 0
            total += rec.food_allowance or 0
            total += rec.transport_allowance or 0
            total += rec.living_allowance or 0
            total += rec.other_allowance or 0
            rec.package = total

    package = fields.Monetary('Package',
                              default=0.0,
                              help="Employee's Package.")
    accommodation = fields.Monetary('Housing Allowance',
                                    default=0.0,
                                    required=True,
                                    tracking=True,
                                    help="Employee's Accommodation.")

    mobile_allowance = fields.Monetary('Mobile Allowance',
                                       default=0.0,
                                       required=True,
                                       tracking=True,
                                       )

    food_allowance = fields.Monetary('Food Allowance',
                                     default=0.0,
                                     required=True,
                                     tracking=True,
                                     )
    site_allowance = fields.Monetary('Site Allowance',
                                     default=0.0,
                                     required=False,
                                     tracking=True,
                                     )
    transport_allowance = fields.Monetary('Transport Allowance',
                                          default=0.0,
                                          required=True,
                                          tracking=True,
                                          )
    living_allowance = fields.Monetary('Living Allowance',
                                       default=0.0,
                                       required=True,
                                       tracking=True,
                                       )
    uniform_provided = fields.Boolean(string="Uniform provided by the company", default=False)
    fixed_overtime_allowance = fields.Monetary('Fixed Overtime Allowance',
                                               default=0.0,
                                               required=False,
                                               tracking=True,
                                               )
    fixed_overtime = fields.Monetary('Fixed Overtime',
                                     default=0.0,
                                     required=False,
                                     tracking=True,
                                     )
    provided_1 = fields.Boolean(string="Accommodation provided by the company ?", default=False)
    provided_2 = fields.Boolean(string="Transportation provided by the company ?", default=False)
    provided_3 = fields.Boolean(string="Food provided by the company ?", default=False)

    uniform = fields.Monetary('Uniform',
                              default=0.0,
                              required=False,
                              tracking=True,
                              )
    other_allowance = fields.Monetary('Other Allowance',
                                      default=0.0,
                                      required=True,
                                      tracking=True,
                                      )

    maximum_ticket_allowance = fields.Monetary('Maximum Ticket Allowance',
                                               default=4500.0,
                                               required=True,
                                               tracking=True,
                                               )
    eligible_after = fields.Integer('Eligible After')
    eligible_every_year = fields.Integer('eligible every/year')
    wage_rate = fields.Float(
        string='Wage Rate',
        default=60,
        required=True)
    gross_salary = fields.Monetary('Gross Salary',
                                   tracking=True,
                                   store=True,
                                   compute='_compute_gross_salary',
                                   help="Employee's monthly gross wage.")
    hold_contract = fields.Boolean(string="Hold Contract")

    @api.constrains('wage_rate')
    def _check_payment_date(self):
        for record in self:
            if record.wage_rate > 100 or record.wage_rate < 0:
                raise ValidationError(_("Rate Must be between 0 and 100"))

    @api.onchange('wage')
    def _calculate_wage(self):
        if self.package and self.wage:
            if self.package != 0.0 and self.wage != 0.0:
                self.accommodation = self.package - self.wage

    @api.depends('wage', 'accommodation', 'transport_allowance', 'mobile_allowance', 'other_allowance', 'food_allowance'
        , 'fixed_overtime_allowance', 'site_allowance', 'provided_1', 'provided_2', 'provided_3',
                 'uniform', 'uniform_provided')
    def _compute_gross_salary(self):
        for record in self:
            if record.employee_id.employee_type == 'perm_in_house':
                record.gross_salary = record.wage \
                                      + record.transport_allowance \
                                      + record.food_allowance \
                                      + record.accommodation \
                                      + record.site_allowance \
                                      + record.mobile_allowance \
                                      + record.fixed_overtime_allowance \
                                      + record.other_allowance \
                                      + record.uniform
                if record.provided_1:
                    if record.payroll_group.provided_1:
                        record.gross_salary -= record.accommodation
                    else:
                        record.provided_1 = False
                        raise ValidationError(_("Can not be provided by the company"))

                if record.provided_2:
                    if record.payroll_group.provided_2:
                        record.gross_salary -= record.transport_allowance
                    else:
                        record.provided_2 = False
                        raise ValidationError(_("Can not be provided by the company"))

                if record.provided_3:
                    if record.payroll_group.provided_3:
                        record.gross_salary -= record.food_allowance
                    else:
                        record.provided_3 = False
                        raise ValidationError(_("Can not be provided by the company"))
                if record.uniform_provided:
                    if record.payroll_group.uniform_provided:
                        record.gross_salary -= record.uniform
                    else:
                        record.uniform_provided = False
                        raise ValidationError(_("Can not be provided by the company"))
            else:
                record.gross_salary = 0.0

    # @api.depends('employee_id', 'wage', 'accommodation', 'transport_allowance', 'mobile_allowance', 'other_allowance',
    #              'food_allowance', 'fixed_overtime_allowance', 'site_allowance', 'uniform')
    # def _compute_gross_salary(self):
    #     for record in self:
    #         if record.employee_id.employee_type == 'perm_in_house' or record.payroll_group:
    #             record.gross_salary = record.wage \
    #                                   + record.transport_allowance \
    #                                   + record.food_allowance \
    #                                   + record.accommodation \
    #                                   + record.site_allowance \
    #                                   + record.mobile_allowance \
    #                                   + record.fixed_overtime_allowance \
    #                                   + record.other_allowance \
    #                                   + record.uniform
    #             # if record.provided_1:
    #             #     if record.payroll_group.provided_1:
    #             #         record.gross_salary -= record.accommodation
    #             #     else:
    #             #         record.provided_1 = False
    #             #         raise ValidationError(_("Can not be provided by the company"))
    #             #
    #             # if record.provided_2:
    #             #     if record.payroll_group.provided_2:
    #             #         record.gross_salary -= record.transport_allowance
    #             #     else:
    #             #         record.provided_2 = False
    #             #         raise ValidationError(_("Can not be provided by the company"))
    #             #
    #             # if record.provided_3:
    #             #     if record.payroll_group.provided_3:
    #             #         record.gross_salary -= record.food_allowance
    #             #     else:
    #             #         record.provided_3 = False
    #             #         raise ValidationError(_("Can not be provided by the company"))
    #             # if record.uniform_provided:
    #             #     if record.payroll_group.uniform_provided:
    #             #         record.gross_salary -= record.uniform
    #             #     else:
    #             #         record.uniform_provided = False
    #             #         raise ValidationError(_("Can not be provided by the company"))
    #         else:
    #             record.gross_salary = 0.0

    @api.constrains('state')
    def _check_values(self):
        for rec in self:
            if rec.hold_contract:
                if rec.payroll_group and rec.employee_id.employee_type == 'perm_in_house':
                    if rec.state == 'draft' or rec.state == 'open' or rec.state == 'probation':
                        if rec.wage < rec.payroll_group.basic_from or rec.wage > rec.payroll_group.basic_to:
                            raise ValidationError(_("Basic Allowance: should be in between %s and %s") %
                                                  (rec.payroll_group.basic_from, rec.payroll_group.basic_to))
                        if rec.provided_1:
                            if rec.payroll_group.provided_1:
                                pass
                        else:
                            if rec.accommodation < rec.payroll_group.accommodation_from or rec.accommodation > rec.payroll_group.accommodation_to:
                                raise ValidationError(_("Accommodation Allowance: should be in between %s and %s") %
                                                      (
                                                          rec.payroll_group.accommodation_from,
                                                          rec.payroll_group.accommodation_to))
                        if rec.provided_2:
                            if rec.payroll_group.provided_2:
                                pass
                        else:
                            if rec.transport_allowance < rec.payroll_group.transportation_from or rec.transport_allowance > rec.payroll_group.transportation_to:
                                raise ValidationError(_("Transportation Allowance: should be inbetween %s and %s") %
                                                      (rec.payroll_group.transportation_from,
                                                       rec.payroll_group.transportation_to))

                        if rec.provided_3:
                            if rec.payroll_group.provided_3:
                                pass
                        else:
                            if rec.food_allowance < rec.payroll_group.food_from or rec.food_allowance > rec.payroll_group.food_to:
                                raise ValidationError(_("Food Allowance: should be in between %s and %s") %
                                                      (rec.payroll_group.food_from, rec.payroll_group.food_to))

                        if rec.site_allowance < rec.payroll_group.site_from or rec.site_allowance > rec.payroll_group.site_to:
                            raise ValidationError(_("Site Allowance: should be in between %s and %s") %
                                                  (rec.payroll_group.site_from, rec.payroll_group.site_to))

                        if rec.gross_salary < rec.payroll_group.total_salary_from or rec.gross_salary > rec.payroll_group.total_salary_to:
                            raise ValidationError(_("Gross Allowance: should be in between %s and %s") %
                                                  (rec.payroll_group.total_salary_from,
                                                   rec.payroll_group.total_salary_to))

    # @api.constrains('state')
    # def _check_values(self):
    #     for rec in self:
    #         if rec.hold_contract:
    #             if rec.payroll_group and rec.employee_id.employee_type == 'perm_in_house':
    #                 if rec.state == 'draft' or rec.state == 'open' or rec.state == 'probation':
    #                     if rec.wage < rec.payroll_group.basic_from or rec.wage > rec.payroll_group.basic_to:
    #                         raise ValidationError(_("Basic Allowance: should be in between %s and %s") %
    #                                               (rec.payroll_group.basic_from, rec.payroll_group.basic_to))
    #                     else:
    #                         if rec.accommodation < rec.payroll_group.accommodation_from or rec.accommodation > rec.payroll_group.accommodation_to:
    #                             raise ValidationError(_("Accommodation Allowance: should be in between %s and %s") %
    #                                                   (
    #                                                       rec.payroll_group.accommodation_from,
    #                                                       rec.payroll_group.accommodation_to))
    #                     if rec.transport_allowance < rec.payroll_group.transportation_from or rec.transport_allowance > rec.payroll_group.transportation_to:
    #                         raise ValidationError(_("Transportation Allowance: should be inbetween %s and %s") %
    #                                               (rec.payroll_group.transportation_from,
    #                                                rec.payroll_group.transportation_to))
    #                     if rec.food_allowance < rec.payroll_group.food_from or rec.food_allowance > rec.payroll_group.food_to:
    #                         raise ValidationError(_("Food Allowance: should be in between %s and %s") %
    #                                               (rec.payroll_group.food_from, rec.payroll_group.food_to))
    #
    #                     if rec.site_allowance < rec.payroll_group.site_from or rec.site_allowance > rec.payroll_group.site_to:
    #                         raise ValidationError(_("Site Allowance: should be in between %s and %s") %
    #                                               (rec.payroll_group.site_from, rec.payroll_group.site_to))
    #
    #                     if rec.gross_salary < rec.payroll_group.total_salary_from or rec.gross_salary > rec.payroll_group.total_salary_to:
    #                         raise ValidationError(_("Gross Allowance: should be in between %s and %s") %
    #                                               (rec.payroll_group.total_salary_from,
    #                                                rec.payroll_group.total_salary_to))
