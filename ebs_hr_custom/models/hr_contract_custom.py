# -*- coding: utf-8 -*-
import json
import logging
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import float_round

_logger = logging.getLogger(__name__)

GCC_COUNTRIES_CODES = ['BH', 'OM', 'AE', 'KW', 'SA']


class HRContractCustom(models.Model):
    _inherit = 'hr.contract'

    leave_type = fields.One2many(
        comodel_name='contract.leave.type',
        inverse_name='contract_id',
        string='Leave Type',
        groups='base.group_user')

    permanent_staff_employee = fields.Many2one(comodel_name="permanent.employee.pay.scale",
                                               string="Pay Scale", required=False, store=True,
                                               readonly=False)
    permanent_staff_contract_domain = fields.Char(
        compute="_compute_permanent_staff_contract_domain",
        readonly=True
    )
    is_married = fields.Boolean(string="Married ?", compute="_check_is_married", default=False)
    is_qatari = fields.Boolean(string="Qatari ?", compute="_check_is_qatari", default=False)
    is_male = fields.Boolean(string="Male ?", compute="_check_is_male", default=False)
    is_gcc_country = fields.Boolean(string="GCC ?", compute="_check_is_gcc", default=False)

    @api.onchange('structure_type_id')
    def _onchange_structure_type_id(self):
        """override _onchange_structure_type to force get the resource calendar from employee"""
        if self.structure_type_id.default_resource_calendar_id:
            self.resource_calendar_id = self.employee_id.resource_calendar_id

    resource_calendar_id = fields.Many2one(
        'resource.calendar', 'Working Schedule', copy=False,
        default=lambda self: self.env['hr.employee'].browse(self.env.context.get('default_employee_id'))
        .mapped('resource_calendar_id')
    )

    resource_calendar_domain = fields.Char("Resource Calendar Domain", compute="_compute_resource_calendar")

    @api.depends('employee_id')
    def _compute_resource_calendar(self):
        for contract in self:
            company = contract.company_id and contract.company_id.id
            if contract.employee_id and contract.employee_id.wassef_employee_type == 'perm_in_house':
                contract.resource_calendar_domain = json.dumps(
                    [('default_work_calendar', '=', 'in_house'), '|', ('company_id', '=', False),
                     ('company_id', '=', company)]
                )
            elif contract.employee_id and contract.employee_id.wassef_employee_type == 'perm_staff':
                contract.resource_calendar_domain = json.dumps(
                    [('default_work_calendar', '=', 'staff'), '|', ('company_id', '=', False),
                     ('company_id', '=', company)]
                )
            elif contract.employee_id and contract.employee_id.wassef_employee_type == 'temp':
                contract.resource_calendar_domain = json.dumps(
                    [('default_work_calendar', '=', 'temp'), '|', ('company_id', '=', False),
                     ('company_id', '=', company)]
                )
            else:
                contract.resource_calendar_domain = json.dumps(
                    [('default_work_calendar', '=', False), '|', ('company_id', '=', False),
                     ('company_id', '=', company)]
                )

    @api.depends('employee_id.country_id')
    def _check_is_gcc(self):
        for rec in self:
            if rec.employee_id.country_id.code in GCC_COUNTRIES_CODES:
                rec.is_gcc_country = True
            else:
                rec.is_gcc_country = False

    @api.depends('employee_id.contract_status')
    def _check_is_married(self):
        for rec in self:
            if rec.employee_id.contract_status == "married":
                rec.is_married = True
            else:
                rec.is_married = False

    @api.depends('employee_id.country_id')
    def _check_is_qatari(self):
        for rec in self:
            if rec.employee_id.country_id.code == "QA":
                rec.is_qatari = True
            else:
                rec.is_qatari = False

    @api.depends('employee_id.gender')
    def _check_is_male(self):
        for rec in self:
            if rec.employee_id.gender == "male":
                rec.is_male = True
            else:
                rec.is_male = False

    @api.depends('is_married', 'is_qatari', 'employee_id.country_id', 'employee_id.gender')
    def _compute_permanent_staff_contract_domain(self):
        for rec in self:
            if rec.employee_id.gender == "male":
                rec.permanent_staff_contract_domain = json.dumps(
                    [('is_married', '=', rec.is_married), ('is_qatari', '=', rec.is_qatari),
                     ('is_gcc_country', '=', rec.is_gcc_country), ('gender', '=', 'male')]
                )
            elif rec.employee_id.gender == 'female':
                rec.permanent_staff_contract_domain = json.dumps(
                    [('is_married', '=', rec.is_married), ('is_qatari', '=', rec.is_qatari),
                     ('is_gcc_country', '=', rec.is_gcc_country), ('gender', '=', 'female')]
                )
            else:
                rec.permanent_staff_contract_domain = json.dumps(
                    [('is_married', '=', rec.is_married), ('is_qatari', '=', rec.is_qatari),
                     ('is_gcc_country', '=', rec.is_gcc_country), ('gender', '=', 'other')]
                )

    is_classified = fields.Boolean(string="Classified", related="employee_id.is_classified", default=False)
    is_confidential = fields.Boolean(string="Confidential ?", related="employee_id.is_confidential", default=False)
    wassef_employee_type = fields.Selection(string="Employment Category", default="", store=True,
                                            selection=[('temp', 'Temporary Employee'),
                                                       ('perm_in_house', 'Permanent In house'),
                                                       ('perm_staff', 'Permanent Staff')],
                                            related="employee_id.wassef_employee_type")

    social_allowance_for_permanent_staff = fields.Monetary(string="Social Allowance ", default=0, required=False)
    housing_allowance_for_permanent_staff = fields.Monetary(string="Housing Allowance", default=0, required=False)
    mobilisation_allowance_for_permanent_staff = fields.Monetary(string="Mobilisation/ Repatriation/Shipping Allowance",
                                                                 default=0,
                                                                 required=False)
    car_loan_for_permanent_staff = fields.Monetary(string="Car Loan", default=0, required=False)
    marriage_loan_for_permanent_staff = fields.Monetary(string="Marriage Loan", default=0, required=False)
    furniture_allowance_for_permanent_staff = fields.Monetary(string="Furniture Allowance", default=0, required=False)
    education_allowance_for_permanent_staff = fields.Monetary(string="Education Allowance", default=0, required=False)
    business_allowance_non_gulf = fields.Monetary(string="BUSINESS/TRAINING TRIP GCC", default=0, required=False)
    business_allowance_gulf = fields.Monetary(string="BUSINESS/TRAINING TRIP All Countries", default=0, required=False)
    gross_salary_for_permanent_staff = fields.Monetary(string="Gross Salary", default=0, required=False)

    # group = fields.Selection(string="Group", related="employee_id.group", required=False, )
    registration_number = fields.Char(string="Employee Code", compute="get_employee_number", readonly=False)
    payroll_group = fields.Many2one(comodel_name="employee.payroll.group",
                                    string="Grade", required=False, store=True)
    country = fields.Many2one(comodel_name="res.country", related="employee_id.country",
                              string="Country", required=False, )
    retroactive = fields.Boolean(string="Retroactive")
    previous_contract = fields.Many2one(comodel_name="hr.contract", string="Previous Contract")
    retroactive_salary = fields.Monetary(
        string='Retroactive Salary', store=True, compute='_compute_retroactive_salary')
    airport_name = fields.Many2one(comodel_name="world.airports", string="Airport", required=False, )
    required_airport = fields.Boolean(string="is required airport", default=False)

    @api.onchange('employee_id')
    @api.depends('employee_id')
    def get_employee_number(self):
        for rec in self:
            rec.registration_number = rec.employee_id.registration_number

    @api.onchange('employee_id')
    def _check_airport(self):
        for rec in self:
            if rec.wassef_employee_type == 'perm_in_house' or not (rec.employee_id.country_id.code in ['QA', 'QD']
                                                                   or rec.employee_id.mother_nationality == 'qatari'
                                                                   or rec.employee_id.is_gcc_country):
                rec.required_airport = True
            else:
                rec.required_airport = False

    @api.model
    def create(self, vals):
        self.date_start = self.employee_id.joining_date
        return super(HRContractCustom, self).create(vals)

    def reset_to_draft(self):
        self.state = 'draft'

    def move_to_probation(self):
        self.state = 'probation'

    def move_to_running(self):
        self.state = 'open'
        # self._check_values()
        # # if self.state == 'open':
        # for each_leave_type in self.leave_type:
        #     if each_leave_type and not each_leave_type.allocation_id:
        #         allocation = self.env['hr.leave.allocation'].create(
        #             {
        #                 'name': each_leave_type.leave_type.name + ': ' + self.employee_id.name,
        #                 'holiday_status_id': each_leave_type.leave_type.id,
        #                 'allocation_type': 'regular',
        #                 'holiday_type': 'employee',
        #                 'employee_id': self.employee_id.id,
        #                 'number_of_days': each_leave_type.days,
        #             }
        #         )
        #         each_leave_type.allocation_id = allocation

    def move_to_cancel(self):
        self.state = 'cancel'

    def move_to_expired(self):
        self.state = 'close'

    # def add_annual_leave(self, annual_leaves):
    #     """ Adds a new annual leave type line """
    #     leave_type = self.env["hr.leave.type"].search([('is_annual', '=', True), ('legal', '=', True)], limit=1)
    #     annual_leave_line = self.env["contract.leave.type"].create({
    #         'leave_type': leave_type.id,
    #         'days': annual_leaves
    #     })
    #     return annual_leave_line

    # def add_long_sick_leave(self, long_sick_leaves):
    #     """ Adds a new long sick leave type line """
    #     leave_type = self.env["hr.leave.type"].search([('code', '=', 'LSL'), ('legal', '=', True)], limit=1)
    #     long_sick_leave_line = self.env["contract.leave.type"].create({
    #         'leave_type': leave_type.id,
    #         'days': long_sick_leaves
    #     })
    #     return long_sick_leave_line

    # def add_short_sick_leave(self, short_sick_leaves):
    #     """ Adds a new short sick leave type line """
    #     leave_type = self.env["hr.leave.type"].search([('code', '=', 'SSL'), ('legal', '=', True)], limit=1)
    #     short_sick_leave_line = self.env["contract.leave.type"].create({
    #         'leave_type': leave_type.id,
    #         'days': short_sick_leaves
    #     })
    #     return short_sick_leave_line

    def add_leave_type_lines(self):
        """Add leave type lines on contract"""
        for rec in self:
            if rec.permanent_staff_employee and rec.employee_id.wassef_employee_type == 'perm_staff':
                pay_scale_for_staff = rec.env['permanent.employee.pay.scale'].browse(
                    rec.permanent_staff_employee.id or rec.permanent_staff_employee.id)
                if pay_scale_for_staff and pay_scale_for_staff.leave_type_ids:
                    leaves_lines_list = []
                    for leave_type in pay_scale_for_staff.leave_type_ids:
                        holiday_female = leave_type.leave_type and leave_type.leave_type.is_female
                        holiday_qatari = leave_type.leave_type and leave_type.leave_type.is_qatari
                        holiday_muslim = leave_type.leave_type and leave_type.leave_type.is_muslim
                        if leave_type.leave_type and self.employee_id and \
                                holiday_female and self.employee_id.gender != 'female':
                            continue
                        elif leave_type.leave_type and self.employee_id and self.employee_id.country_id and \
                                holiday_qatari and self.employee_id.country_id.code != 'QA':
                            continue
                        elif leave_type.leave_type and self.employee_id and holiday_muslim and \
                                self.employee_id.wassef_religion != 'muslim':
                            continue
                        else:
                            leaves_lines_list.append(leave_type.id)
                    # delete old leaves
                    # rec.leave_type = [(2, line.id) for line in rec.leave_type]
                    # Link new leaves

                    rec.leave_type = [(4, line) for line in leaves_lines_list]

            elif rec.employee_id.payroll_group and rec.employee_id.wassef_employee_type == 'perm_in_house':

                pay_scale = rec.env['employee.payroll.group'].browse(rec.payroll_group.id or
                                                                     rec.employee_id.payroll_group.id)
                if pay_scale and pay_scale.leave_type_ids:
                    leaves_lines_list = []
                    for leave_type in pay_scale.leave_type_ids:
                        holiday_female = leave_type.leave_type and leave_type.leave_type.is_female
                        holiday_qatari = leave_type.leave_type and leave_type.leave_type.is_qatari
                        holiday_muslim = leave_type.leave_type and leave_type.leave_type.is_muslim
                        if leave_type.leave_type and self.employee_id and \
                                holiday_female and self.employee_id.gender != 'female':
                            continue
                        elif leave_type.leave_type and self.employee_id and self.employee_id.country_id and \
                                holiday_qatari and self.employee_id.country_id.code != 'QA':
                            continue
                        elif leave_type.leave_type and self.employee_id and holiday_muslim and \
                                self.employee_id.wassef_religion != 'muslim':
                            continue
                        else:
                            leaves_lines_list.append(leave_type.id)
                    # delete old leaves
                    # rec.leave_type = [(2, line.id) for line in rec.leave_type]
                    # Link new leaves
                    rec.leave_type = [(4, line) for line in leaves_lines_list]

    @api.depends('employee_id', 'wage', 'accommodation', 'transport_allowance', 'mobile_allowance', 'other_allowance',
                 'food_allowance', 'fixed_overtime_allowance', 'site_allowance', 'provided_1', 'provided_2',
                 'provided_3', 'uniform', 'uniform_provided', 'social_allowance_for_permanent_staff')
    def _compute_gross_salary(self):
        for record in self:
            if record.employee_id.wassef_employee_type == 'perm_staff':
                record.gross_salary = record.wage \
                                      + record.transport_allowance \
                                      + record.social_allowance_for_permanent_staff \
                                      + record.accommodation \
                                      + record.mobile_allowance \
                                      + record.other_allowance
            elif record.employee_id.wassef_employee_type == 'perm_in_house' or record.payroll_group:
                record.gross_salary = record.wage \
                                      + record.transport_allowance \
                                      + record.food_allowance \
                                      + record.accommodation \
                                      + record.site_allowance \
                                      + record.mobile_allowance \
                                      + record.fixed_overtime_allowance \
                                      + record.other_allowance \
                                      + record.uniform
                # if record.provided_1:
                #     if record.payroll_group.provided_1:
                #         record.gross_salary -= record.accommodation
                #     else:
                #         record.provided_1 = False
                #         raise ValidationError(_("Can not be provided by the company"))
                #
                # if record.provided_2:
                #     if record.payroll_group.provided_2:
                #         record.gross_salary -= record.transport_allowance
                #     else:
                #         record.provided_2 = False
                #         raise ValidationError(_("Can not be provided by the company"))
                #
                # if record.provided_3:
                #     if record.payroll_group.provided_3:
                #         record.gross_salary -= record.food_allowance
                #     else:
                #         record.provided_3 = False
                #         raise ValidationError(_("Can not be provided by the company"))
                # if record.uniform_provided:
                #     if record.payroll_group.uniform_provided:
                #         record.gross_salary -= record.uniform
                #     else:
                #         record.uniform_provided = False
                #         raise ValidationError(_("Can not be provided by the company"))
            else:
                record.gross_salary = 0.0

    @api.onchange('employee_id', 'permanent_staff_employee', 'payroll_group')
    @api.depends('employee_id', 'permanent_staff_employee', 'payroll_group')
    def get_payscale_values(self):
        # annual_leaves = 0
        # long_sick_leaves = 0
        # short_sick_leaves = 0
        if self.state == 'draft' and self.employee_id and self.employee_id.wassef_employee_type == 'perm_in_house':
            # self.payroll_group = self.employee_id.payroll_group.id
            pay_scale = self.env['employee.payroll.group'].browse(self.payroll_group.id)
            if pay_scale:
                self.wage = pay_scale.basic_from
                self.accommodation = pay_scale.accommodation_from
                self.transport_allowance = pay_scale.transportation_from
                self.food_allowance = pay_scale.food_from
                self.site_allowance = pay_scale.site_from
                # if pay_scale.annual_leaves:
                #     annual_leaves = pay_scale.annual_leaves
                # if pay_scale.long_sick_leaves:
                #     long_sick_leaves = pay_scale.long_sick_leaves
                # if pay_scale.short_sick_leaves:
                #     short_sick_leaves = pay_scale.short_sick_leaves
            self.add_leave_type_lines()

        elif self.state == 'draft' and self.employee_id and \
                self.employee_id.wassef_employee_type == 'perm_staff':
            # self.permanent_staff_employee = self.employee_id.permanent_staff_employee.id
            pay_scale_for_staff = self.env['permanent.employee.pay.scale'].browse(
                self.permanent_staff_employee.id)
            self.permanent_staff_employee = pay_scale_for_staff if pay_scale_for_staff else self.employee_id.permanent_staff_employee
            self.wage = pay_scale_for_staff.basic_from
            self.social_allowance_for_permanent_staff = pay_scale_for_staff.social_allowance
            # self.housing_allowance_for_permanent_staff = pay_scale_for_staff.housing_allowance
            self.accommodation = pay_scale_for_staff.housing_allowance
            self.transport_allowance = pay_scale_for_staff.transport_allowance
            self.mobile_allowance = pay_scale_for_staff.mobile_allowance
            self.mobilisation_allowance_for_permanent_staff = pay_scale_for_staff.mobilisation_allowance
            self.car_loan_for_permanent_staff = pay_scale_for_staff.car_loan
            self.marriage_loan_for_permanent_staff = 40000 if 40000 < (
                    4 * self.wage) else (4 * self.wage)
            self.furniture_allowance_for_permanent_staff = pay_scale_for_staff.furniture_allowance
            self.education_allowance_for_permanent_staff = pay_scale_for_staff.education_allowance
            self.business_allowance_non_gulf = pay_scale_for_staff.business_allowance_non_gulf
            self.business_allowance_gulf = pay_scale_for_staff.business_allowance_gulf
            self.gross_salary = pay_scale_for_staff.total_salary_from
            # if pay_scale_for_staff.annual_leaves:
            #     annual_leaves = pay_scale_for_staff.annual_leaves
            # if pay_scale_for_staff.long_sick_leaves:
            #     long_sick_leaves = pay_scale_for_staff.long_sick_leaves
            # if pay_scale_for_staff.short_sick_leaves:
            #     short_sick_leaves = pay_scale_for_staff.short_sick_leaves
            # check if employee have leave type lines
            self.add_leave_type_lines()

        # if annual_leaves:
        #     annual_leaves_found = self.leave_type.filtered(lambda line: line.leave_type.is_annual)
        #     if annual_leaves_found:
        #         self.leave_type = [(2, line.id) for line in annual_leaves_found]
        #     annual_leave_line = self.add_annual_leave(annual_leaves)
        #     self.leave_type = [(4, annual_leave_line.id)]
        #
        # if long_sick_leaves:
        #     long_sick_leaves_found = self.leave_type.filtered(lambda line: line.leave_type.code == 'LSL')
        #     if long_sick_leaves_found:
        #         self.leave_type = [(2, line.id) for line in long_sick_leaves_found]
        #     long_sick_leave_line = self.add_long_sick_leave(long_sick_leaves)
        #     self.leave_type = [(4, long_sick_leave_line.id)]
        #
        # if short_sick_leaves:
        #     short_sick_leaves_found = self.leave_type.filtered(lambda line: line.leave_type.code == 'SSL')
        #     if short_sick_leaves_found:
        #         self.leave_type = [(2, line.id) for line in short_sick_leaves_found]
        #     short_sick_leave_line = self.add_short_sick_leave(short_sick_leaves)
        #     self.leave_type = [(4, short_sick_leave_line.id)]

    @api.onchange('wage')
    @api.depends('wage')
    def change_marriage_loan_for_permanent_staff(self):
        if self.permanent_staff_employee:
            self.marriage_loan_for_permanent_staff = 40000 \
                if 40000 < (4 * self.wage) else (4 * self.wage)

    @api.onchange('previous_contract', 'previous_contract.date_end', 'date_start', 'retroactive',
                  'previous_contract.gross_salary', 'gross_salary')
    @api.depends('previous_contract', 'previous_contract.date_end', 'date_start', 'retroactive',
                 'previous_contract.gross_salary', 'gross_salary')
    def _compute_retroactive_salary(self):
        if self.previous_contract.date_end and self.date_start and self.gross_salary and self.previous_contract.gross_salary:
            # time_difference = ((self.previous_contract.date_end.year - self.date_start.year) * 12 + self.previous_contract.date_end.month - self.date_start.month) + 1
            payslips = self.env['hr.payslip'].search(
                [('contract_id', '=', self.previous_contract.id), ('date_to', '>', self.previous_contract.date_end)])
            salary_difference = self.gross_salary - self.previous_contract.gross_salary
            self.retroactive_salary = salary_difference * len(payslips)
        else:
            self.retroactive_salary = 0

    @api.constrains('wage')
    def _check_basic_for_permanent_staff(self):
        for rec in self:
            if rec.hold_contract:
                if rec.employee_id.wassef_employee_type == 'perm_staff' and rec.permanent_staff_employee and not rec.is_classified:
                    pay_scale_for_staff = self.env['permanent.employee.pay.scale'].browse(
                        rec.permanent_staff_employee.id or rec.employee_id.permanent_staff_employee.id)
                    if rec.wage < pay_scale_for_staff.basic_from or rec.wage > \
                            pay_scale_for_staff.basic_to:
                        raise ValidationError(_("Basic Wage: should be in between %s and %s") %
                                              (pay_scale_for_staff.basic_from, pay_scale_for_staff.basic_to))

    # @api.onchange('state')
    # def _onchange_state_open(self):
    #     self._check_values()
    #     if self.state == 'open':
    #         for each_leave_type in self.leave_type:
    #             if each_leave_type and not each_leave_type.allocation_id:
    #                 allocation = self.env['hr.leave.allocation'].create(
    #                     {
    #                         'name': each_leave_type.leave_type.name + ': ' + self.employee_id.name,
    #                         'holiday_status_id': each_leave_type.leave_type.id,
    #                         'allocation_type': 'regular',
    #                         'holiday_type': 'employee',
    #                         'employee_id': self.employee_id.id,
    #                         'number_of_days': each_leave_type.days,
    #                     }
    #                 )
    #                 each_leave_type.allocation_id = allocation
    #     else:
    #         pass

    @api.model
    def _create_employees_sick_allocation_every_year(self):
        today_date = date.today()
        current_year = today_date.year
        if today_date and today_date.day == 1 and today_date.month == 1:
            _logger.info('Run cron job for creating allocation on %s , %s', today_date, current_year)
            all_contracts = self.env["hr.contract"].search(
                [('state', '=', 'open'), ('wassef_employee_type', 'in', ['perm_staff', 'perm_in_house'])])
            all_contracts = all_contracts.filtered(
                lambda
                    contract: contract.employee_id.probation_date and contract.employee_id.probation_date < today_date)
            for contract in all_contracts:
                for each_leave_type in contract.leave_type:
                    if each_leave_type.leave_type.is_sick_leave:
                        employee = contract.employee_id
                        days = each_leave_type.days
                        sick_balance = self._get_employee_remaining_sick_balance(employee, each_leave_type.leave_type)
                        if all((days, sick_balance < days)):
                            difference = days - sick_balance
                            self.create_sick_leave_allocation(employee, each_leave_type, current_year, difference)
        else:
            _logger.info('Can not run cron job for creating allocation on %s', today_date)

    def _get_employee_remaining_sick_balance(self, employee, leave_type):
        remaining_leaves = 0
        balance = self.env['hr.leave.allocation'].search([('employee_id', '=', employee.id),
                                                          ('holiday_status_id.id', '=', leave_type.id),
                                                          ('state', '=', 'validate')])
        n_of_allocations = sum(balance.mapped('number_of_days'))
        leaves_taken = sum(self.env['hr.leave'].search([('employee_id', '=', employee.id),
                                                        ('holiday_status_id.id', '=', leave_type.id),
                                                        ('state', '=', 'validate')]).mapped('number_of_days'))
        remaining_leaves += n_of_allocations - leaves_taken

        return remaining_leaves

    def create_sick_leave_allocation(self, employee, each_leave_type, current_year, difference):
        allocation = self.env['hr.leave.allocation'].create(
            {
                'name': each_leave_type.leave_type.name + f': year {(current_year)} ' + ': ' +
                        employee.name,
                'holiday_status_id': each_leave_type.leave_type.id,
                'allocation_type': 'regular',
                'holiday_type': 'employee',
                'employee_id': employee.id,
                'number_of_days': difference,
                'year': current_year,
            }
        )
        # allocation.action_approve()
        allocation.sudo().write({'state': 'validate'})
        # allocation.action_validate()

    @api.model
    def _create_allocation_employees_every_year(self):
        today_date = date.today()
        current_year = today_date.year
        if today_date and today_date.month == 1 and today_date.day == 1:
            _logger.info('Run cron job for creating allocation on %s , %s', today_date, today_date.year)
            all_contracts = self.env["hr.contract"].search(
                [('state', '=', 'open'), '|', ('wassef_employee_type', '=', 'perm_staff'), '&',
                 ('wassef_employee_type', '=', 'perm_in_house'), ('employee_id.emp_allocation_type', '=', 'regular')])
            all_contracts = all_contracts.filtered(
                lambda contract: contract.employee_id.probation_date < today_date)

            for contract in all_contracts:
                for each_leave_type in contract.leave_type:
                    if contract.wassef_employee_type == 'perm_staff' and each_leave_type.leave_type.is_annual:
                        employee = contract.employee_id
                        r_balance = self._get_employee_remaining_balance(employee, each_leave_type.leave_type,
                                                                         current_year)
                        leave_carry_forwards = contract.permanent_staff_employee.leave_carry_forwards
                        if r_balance > 0:
                            if leave_carry_forwards and r_balance > leave_carry_forwards:
                                # difference = r_balance - leave_carry_forwards
                                self.create_allocation_4_r_balance_and_carry_forward(employee, each_leave_type,
                                                                                     current_year, r_balance,
                                                                                     leave_carry_forwards)
                            elif leave_carry_forwards and r_balance < leave_carry_forwards:
                                self.create_allocation_4_r_balance(employee, each_leave_type,
                                                                   current_year, r_balance)

                        self.create_annual_leave_allocation(employee, each_leave_type, current_year)

                    elif contract.wassef_employee_type == 'perm_in_house' and each_leave_type.leave_type.is_annual:
                        employee = contract.employee_id
                        self._create_inhouse_annual_leave(employee, each_leave_type.leave_type)
        else:
            _logger.info('Can not run cron job for creating allocation on %s', today_date)

    def _create_inhouse_annual_leave(self, employee, leave_type):

        allocation_obj = self.env['hr.leave.allocation']
        if employee:
            if leave_type and employee.joining_date and employee.wassef_employee_type == 'perm_in_house' and employee.emp_allocation_type == 'regular':
                delta = relativedelta(date.today(), employee.joining_date)
                number_of_days = 21
                if delta.years >= 5:
                    number_of_days = 30
                res = allocation_obj.sudo().with_context(is_created_cron=True).create({
                    'employee_id': employee.id,
                    'name': 'Annual ' + f': year {(date.today().year)} ' + ': ' +
                            employee.name,
                    'year': date.today().year + 1,
                    'allocation_type': 'regular',
                    'number_of_days': number_of_days,
                    'holiday_status_id': leave_type.id,
                    'number_of_days_display': number_of_days,
                })

                res.action_approve()
                # res.sudo().write({'state': 'validate1'})
                res.action_validate()

    def create_annual_leave_allocation(self, employee, each_leave_type, current_year):
        # new_year = current_year + 1

        allocation = self.env['hr.leave.allocation'].create(
            {
                'name': each_leave_type.leave_type.name + f': year {(current_year)} ' + ': ' +
                        employee.name,
                'holiday_status_id': each_leave_type.leave_type.id,
                'allocation_type': 'regular',
                'holiday_type': 'employee',
                'employee_id': employee.id,
                'number_of_days': each_leave_type.days,
                'year': current_year,
            }
        )
        allocation.action_approve()
        # allocation.sudo().write({'state': 'validate1'})
        allocation.action_validate()

    def create_allocation_4_r_balance_and_carry_forward(self, employee, each_leave_type, current_year, r_balance,
                                                        leave_carry_forwards):
        res = [
            {
                'name': each_leave_type.leave_type.name + f': year {current_year - 1} ' + ': ' +
                        employee.name,
                'holiday_status_id': each_leave_type.leave_type.id,
                'allocation_type': 'regular',
                'holiday_type': 'employee',
                'employee_id': employee.id,
                'number_of_days': -r_balance,
                'year': current_year - 1,
                'allocated_yearly': True,

            },

            {
                'name': each_leave_type.leave_type.name + f': year {current_year} ' + ': ' +
                        employee.name,
                'holiday_status_id': each_leave_type.leave_type.id,
                'allocation_type': 'regular',
                'holiday_type': 'employee',
                'employee_id': employee.id,
                'number_of_days': leave_carry_forwards,
                'year': current_year,
            }
        ]
        allocations = self.env['hr.leave.allocation'].create(res)
        # self._cr.execute(
        #     'Update hr_leave_allocation set create_date= %s WHERE id IN %s and year = %s',
        #     [date.today() + relativedelta(days=-1),tuple(allocations.ids), 2022])
        allocations.action_approve()
        # allocation.sudo().write({'state': 'validate1'})
        allocations.action_validate()

    def create_allocation_4_r_balance(self, employee, each_leave_type, current_year, r_balance):
        res = [
            {
                'name': each_leave_type.leave_type.name + f': year {current_year - 1} ' + ': ' +
                        employee.name,
                'holiday_status_id': each_leave_type.leave_type.id,
                'allocation_type': 'regular',
                'holiday_type': 'employee',
                'employee_id': employee.id,
                'number_of_days': -r_balance,
                'year': current_year - 1,
                'allocated_yearly': True,
            },

            {
                'name': each_leave_type.leave_type.name + f': year {current_year} ' + ': ' +
                        employee.name,
                'holiday_status_id': each_leave_type.leave_type.id,
                'allocation_type': 'regular',
                'holiday_type': 'employee',
                'employee_id': employee.id,
                'number_of_days': r_balance,
                'year': current_year,
            }
        ]
        allocations = self.env['hr.leave.allocation'].create(res)
        # self._cr.execute(
        #     'Update hr_leave_allocation set create_date= %s WHERE id IN %s and year = %s',
        #     [date.today() + relativedelta(days=-1),tuple(allocations.ids), 2022])

        allocations.action_approve()
        # allocation.sudo().write({'state': 'validate1'})
        allocations.action_validate()

        # allocation_obj = self.env['hr.leave.allocation'].search([('employee_id', '=', employee.id),
        #                                                          ('holiday_status_id.is_annual', '=', True),
        #                                                          ('state', '=', 'validate'),
        #                                                          ('year', '=', year - 1)], order='number_of_days desc',
        #                                                         limit=1)
        #
        # if allocation_obj:
        #     # allocation_obj.number_of_days -= difference
        #     # allocation_obj.deducted_days = difference
        #     allocation_obj.write({
        #         'number_of_days': allocation_obj.number_of_days - difference,
        #         'deducted_days':difference,
        #         'name': allocation_obj.name + f" - Number of {difference} days has been deducted to apply the carry forward rule" if allocation_obj.name else \
        #             f" Number of {difference} days has been deducted to apply the carry forward rule"
        #     })
        #     allocation_obj.message_post(
        #         subject='Carry Forwards Rule',
        #         body=f'Number of {difference} days has been deducted to apply the '
        #              f'carry forward rule')
        # if allocation_obj.name:
        #     allocation_obj.name += f" - Number of {difference} days has been deducted to apply the carry forward rule"
        # else:
        #     allocation_obj.name = f" Number of {difference} days has been deducted to apply the carry forward rule"

    def _get_employee_remaining_balance(self, employee, leave_type, current_year):
        max_leaves = leaves_taken = old_leaves = extracted_leaves = 0
        allocation_obj = self.env['hr.leave.allocation'].search([('employee_id', '=', employee.id),
                                                                 ('holiday_status_id.id', '=', leave_type.id),
                                                                 ('state', '=', 'validate'),
                                                                 ('year', '<', current_year)])
        leaves_obj = self.env['hr.leave'].search([('employee_id', '=', employee.id),
                                                  ('holiday_status_id.id', '=', leave_type.id),
                                                  ('state', '=', 'validate')]).filtered(
            lambda x: x.date_from.year < current_year)

        if allocation_obj:
            max_leaves += sum(allocation_obj.mapped('number_of_days'))
        if leaves_obj:
            # first we should get leave requests taken within the current year
            old_leaves += sum(leaves_obj.filtered(lambda x: x.date_to.year <= current_year).mapped(
                'number_of_days')) if leaves_obj else 0
            # second we check if there are leave requests holds days that are not in the current year
            upcoming_leaves = leaves_obj.filtered(lambda x: x.date_to.year >= current_year)
            if upcoming_leaves:
                for leave in upcoming_leaves:
                    extracted_leaves += employee._get_work_days_data_batch(leave.date_from,
                                                                           leave.date_to.replace(year=current_year - 1,
                                                                                                 month=12, day=31))[
                        employee.id]['days']
            leaves_taken += old_leaves + extracted_leaves

        return max_leaves - leaves_taken

    @api.model
    def _create_allocation_for_probation_employees(self):
        today_date = date.today()
        _logger.info('Run cron job for creating allocation for probation employees on %s ', today_date)
        valid_contracts = self.env["hr.contract"].search(['&',
                                                          ('state', '=', 'open'),
                                                          ('employee_id.wassef_employee_type', 'in',
                                                           ['perm_in_house', 'perm_staff']),
                                                          ]).filtered(
            lambda contract: contract.employee_id.probation_date == today_date and not
            contract.employee_id.is_end_probation_period)

        for contract in valid_contracts:
            if contract.employee_id.wassef_employee_type == 'perm_staff':
                # case 1
                if contract.employee_id.joining_date and \
                        contract.employee_id.probation_date.year == contract.employee_id.joining_date.year:
                    join_date_datetime = datetime.combine(contract.employee_id.joining_date, datetime.min.time())
                    end_year = datetime.combine(date(today_date.year, 12, 31), datetime.min.time())
                    work_days = contract.employee_id._get_work_days_data(join_date_datetime, end_year,
                                                                         calendar=contract.resource_calendar_id)
                    annual_leave = self.env['hr.leave.type'].search([('is_annual', '=', True)], limit=1)
                    if work_days.get('days'):
                        number_of_days = (21 * work_days['days']) / 261
                        number_of_days = float_round(number_of_days, precision_digits=2)
                        self._create_allocation(annual_leave, contract, number_of_days, today_date)
                # case 3
                elif contract.employee_id.joining_date and contract.employee_id.probation_date and \
                        contract.employee_id.probation_date.year == (contract.employee_id.joining_date.year + 1):

                    join_date_datetime = datetime.combine(contract.employee_id.joining_date, datetime.min.time())
                    end_last_year = datetime.combine(date(join_date_datetime.date().year, 12, 31), datetime.min.time())
                    work_days = contract.employee_id._get_work_days_data(join_date_datetime, end_last_year,
                                                                         calendar=contract.resource_calendar_id)
                    annual_leave = self.env['hr.leave.type'].search([('is_annual', '=', True)], limit=1)
                    if work_days.get('days'):
                        number_of_days = ((21 * work_days['days']) / 261) + 21
                        number_of_days = float_round(number_of_days, precision_digits=2)
                        self._create_allocation(annual_leave, contract, number_of_days, today_date)

            elif contract.employee_id.wassef_employee_type == 'perm_in_house':
                # case 2
                if contract.employee_id.joining_date and contract.employee_id.probation_date and \
                        contract.employee_id.probation_date.year == contract.employee_id.joining_date.year:
                    number_of_days = 0
                    if contract.employee_id.emp_allocation_type == 'accrual':
                        calendar_days = abs(
                            (contract.employee_id.probation_date - contract.employee_id.joining_date).days)
                        number_of_days = (21 * calendar_days) / 365
                        number_of_days = float_round(number_of_days, precision_digits=2)
                    elif contract.employee_id.emp_allocation_type == 'regular':
                        calendar_days = abs(
                            (date(contract.employee_id.probation_date.year, 12, 31) -
                             contract.employee_id.joining_date).days)
                        number_of_days = (21 * calendar_days) / 365
                        number_of_days = float_round(number_of_days, precision_digits=2)
                    annual_leave = self.env['hr.leave.type'].search([('is_annual', '=', True)], limit=1)
                    if number_of_days:
                        self._create_allocation(annual_leave, contract, number_of_days, today_date)

                # case 4
                elif contract.employee_id.joining_date and contract.employee_id.probation_date and \
                        contract.employee_id.probation_date.year == (contract.employee_id.joining_date.year + 1):
                    number_of_days = 0
                    if contract.employee_id.emp_allocation_type == 'accrual':
                        calendar_days = abs(
                            (contract.employee_id.probation_date - contract.employee_id.joining_date).days)
                        number_of_days = (21 * calendar_days) / 365
                        number_of_days = float_round(number_of_days, precision_digits=2)
                    elif contract.employee_id.emp_allocation_type == 'regular':
                        calendar_days = abs(
                            (date(contract.employee_id.joining_date.year, 12, 31) -
                             contract.employee_id.joining_date).days)
                        number_of_days = ((21 * calendar_days) / 365) + 21
                        number_of_days = float_round(number_of_days, precision_digits=2)
                    annual_leave = self.env['hr.leave.type'].search([('is_annual', '=', True)], limit=1)
                    if number_of_days:
                        self._create_allocation(annual_leave, contract, number_of_days, today_date)

    def _create_allocation(self, annual_leave, contract, number_of_days, today_date):
        allocation = self.env['hr.leave.allocation'].create(
            {
                'name': 'Annual ' + f': year {today_date.year} ' + ' : ' + contract.employee_id.name,
                'holiday_status_id': annual_leave.id,
                'allocation_type': 'regular',
                'holiday_type': 'employee',
                'employee_id': contract.employee_id.id,
                'number_of_days': number_of_days,
                'year': today_date.year,
            }
        )
        allocation.action_approve()
        allocation.sudo().write({'state': 'validate1'})
        allocation.action_validate()
        contract.employee_id.sudo().write({'is_end_probation_period': True})

    type_leave = fields.Selection([('working_days', 'Working Days'),
                                   ('calendar_days', 'Calendar Days')], string="Type Of Leave",
                                  default="working_days")
    effective_date = fields.Date()

    @api.onchange('wassef_employee_type', 'employee_id')
    def _onchange_employee_type(self):
        for rec in self:
            if rec.employee_id.wassef_employee_type == 'perm_staff':
                rec.type_leave = 'working_days'
            elif rec.employee_id.wassef_employee_type == 'perm_in_house':
                rec.type_leave = 'calendar_days'

    @api.model
    def action_write_effective_date(self, employee_id, effective_date):
        if date and employee_id:
            self.sudo().browse(int(employee_id)).sudo().update({'effective_date': effective_date})
            return True

    def write(self, vals):
        for rec in self:
            rec._check_values()
            if rec.state == 'open':
                today = date.today()
                last_date = datetime(today.year, 12, 31, 0, 0, 0)
                joining_date = rec.employee_id.joining_date
                # for each_leave_type in rec.leave_type:
                #     if each_leave_type and not each_leave_type.allocation_id:
                #         if joining_date.year == today.year:
                #             emp_joining_date = datetime(joining_date.year, joining_date.month, joining_date.day, 0, 0,
                #                                         0)
                #             remaining_working_days = rec.employee_id._get_work_days_data(emp_joining_date, last_date,
                #                                                                          calendar=rec.resource_calendar_id)[
                #                 'days']
                #             balance = 0
                #             if rec.employee_type == 'perm_staff':
                #                 balance += math.ceil(remaining_working_days / 261 * each_leave_type.days)
                #
                #             elif rec.employee_type == 'perm_in_house':
                #
                #                 remaining_calendar_days = (last_date.date() - joining_date).days + 1
                #                 balance += math.ceil(remaining_calendar_days / 360 * each_leave_type.days)
                # TODO: REMOVE FROM LIVE
                # allocation = rec.env['hr.leave.allocation'].sudo().create(
                #     {
                #         'name': each_leave_type.leave_type.name + ': ' + rec.employee_id.name,
                #         'holiday_status_id': each_leave_type.leave_type.id,
                #         'allocation_type': 'regular',
                #         'holiday_type': 'employee',
                #         'employee_id': rec.employee_id.id,
                #         'number_of_days': balance,
                #         'year': today.year,
                #     }
                # )
                # allocation.action_approve()
                # allocation.sudo().write({'state': 'validate1'})
                # allocation.action_validate()
                # each_leave_type.allocation_id = allocation
                # else:
                #     allocation = rec.env['hr.leave.allocation'].sudo().create(
                #         {
                #             'name': each_leave_type.leave_type.name + ': ' + rec.employee_id.name,
                #             'holiday_status_id': each_leave_type.leave_type.id,
                #             'allocation_type': 'regular',
                #             'holiday_type': 'employee',
                #             'employee_id': rec.employee_id.id,
                #             'number_of_days': each_leave_type.days,
                #             'year': today.year,
                #         }
                #     )
                #     allocation.action_approve()
                #     allocation.sudo().write({'state': 'validate1'})
                #     allocation.action_validate()
                #     each_leave_type.allocation_id = allocation
            fields_list = ['registration_number', 'employee_id', 'payroll_group', 'permanent_staff_employee',
                           'resource_calendar_id',
                           'registration_number_previous', 'payroll_group_previous',
                           'permanent_staff_employee_previous', 'resource_calendar_id_previous']
            if not vals.get('effective_date') and rec.effective_date and 'is_created_cron' not in rec._context:
                applied_fields = list(set(fields_list).intersection(vals.keys()))
                if len(applied_fields) > 0:
                    final_vals = {}
                    temp_vals = vals
                    for key, value in list(temp_vals.items()):
                        if key not in fields_list:
                            final_vals[key] = vals[key]
                        is_one2many = isinstance(rec._fields[key], (fields.One2many))
                        if is_one2many:
                            final_vals[key] = vals[key]
                            del vals[key]
                        vals[key + '_previous'] = getattr(self, key, None)
                    rec.create_employee_event(rec.effective_date, vals)
                    if final_vals:
                        res = super(HRContractCustom, self).write(final_vals)
                        return res
                    return False
                else:
                    res = super(HRContractCustom, self).write(vals)
                    return res
            else:
                res = super(HRContractCustom, self).write(vals)
            return res

    def create_employee_event(self, effective_date, vals):
        event_obj = self.env['employee.event']
        data = {}
        final_data = {}
        ctx = {}
        fields_list = ['registration_number', 'employee_id', 'payroll_group', 'permanent_staff_employee',
                       'resource_calendar_id']
        previous_vals = ['registration_number_previous', 'payroll_group_previous', 'permanent_staff_employee_previous',
                         'resource_calendar_id_previous']

        if vals:
            for key, value in vals.items():
                if key in fields_list:
                    field = self.env['ir.model.fields'].sudo().search(
                        [('model', '=', 'employee.event'), ('name', '=', key)])
                    if field.name and field.name not in previous_vals:
                        data[field.name] = value
                        if hasattr(self, key):
                            if field.ttype == 'many2one' and field.relation:
                                name = self.env[field.relation].sudo().browse(value).name_get()
                                old_value = getattr(self, key) if getattr(self, key) else ''
                                values = name[0][1] or ''
                                final_data[field.field_description] = [
                                    old_value.sudo().name_get()[0][1] or '' if old_value else '',
                                    values]
                            else:
                                values = value
                                final_data[field.field_description] = [getattr(self, key) if getattr(self, key) else '',
                                                                       values]
                        else:
                            final_data[field.field_description] = ['', value]
                    if field.name:
                        data[field.name] = value
        if data:
            res = event_obj.sudo().create({
                'contract_id': self.id,
                'employee_id': self.employee_id.id,
                'event_type': 'update_contract',
                'effective_date': effective_date,
            })
            res.onchange_employee_id()
            res.sudo().write(data)
            template = self.env.ref('ebs_hr_custom.email_template_for_event')
            ctx.update({'final_data': final_data})
            template.with_context(ctx).send_mail(res.id, force_send=False)


class ContractLeaveTypeCustom(models.Model):
    _name = 'contract.leave.type'

    leave_type = fields.Many2one(comodel_name="hr.leave.type", string="Leave Type", required=True)
    days = fields.Float(required=True)
    contract_id = fields.Many2one('hr.contract', 'Contract', readonly=True, ondelete="cascade")
    allocation_id = fields.Many2one('hr.leave.allocation', 'Allocation', ondelete="cascade", readonly=True)
    payscale_id = fields.Many2one('permanent.employee.pay.scale', 'Pay Scale', ondelete="cascade", readonly=True)
    payroll_group_id = fields.Many2one('employee.payroll.group', 'Group', ondelete="cascade", readonly=True)

    @api.onchange('leave_type')
    def _get_default_number_of_days(self):
        for rec in self:
            if rec.leave_type:
                if rec.leave_type.default_days and not rec.days:
                    rec.days = rec.leave_type.default_days
