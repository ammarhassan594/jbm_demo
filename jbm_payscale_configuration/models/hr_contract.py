# -*- coding: utf-8 -*-
import json
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import float_round


class HRContractCustom(models.Model):
    _inherit = 'hr.contract'

    registration_number = fields.Char(related='employee_id.registration_number', store=True)
    leave_type = fields.One2many(comodel_name='contract.leave.type', inverse_name='contract_id', string='Leave Type')
    payscale_id = fields.Many2one(comodel_name="employee.payscale", string="Pay Scale")
    employee_payscale_domain = fields.Char(
        compute="_get_employee_payscale",
        readonly=True
    )
    is_married = fields.Boolean(string="Married ?", compute="_check_is_married", default=False)
    is_qatari = fields.Boolean(string="Qatari ?", compute="_check_is_qatari", default=False)
    # is_male = fields.Boolean(string="Male ?", compute="_check_is_male", default=False)

    # wage = fields.Monetary(compute="_get_salary_elements")
    basic = fields.Monetary(string="Basic")
    social_alw = fields.Monetary(string="Social Allowance ", default=0, compute="_get_salary_elements", readonly=False, store=True)
    housing_alw = fields.Monetary(string="Housing Allowance", default=0, compute="_get_salary_elements",readonly=False,store=True)
    transport_alw = fields.Monetary(string="Transport Allowance", default=0, compute="_get_salary_elements",readonly=False,store=True)
    other_alw = fields.Monetary(string="Other Allowance", default=0, compute="_get_salary_elements",readonly=False, store=True)
    mobile_alw = fields.Monetary(string="Mobile Allowance", default=0, compute="_get_salary_elements",readonly=False,store=True)
    car_alw = fields.Monetary(string="Car Allowance", default=0, compute="_get_salary_elements",readonly=False,store=True)
    car_loan = fields.Monetary(string="Car Loan", default=0,readonly=False,store=True)
    marriage_loan = fields.Monetary(string="Marriage Loan", default=0,readonly=False,store=True)
    air_ticket_alw = fields.Selection(string="Annual Air Ticket Allowance ", compute="_get_salary_elements",
                                      selection=[('b', 'Business'), ('e', 'Economy')], store=True)
    furniture_alw = fields.Monetary(string="Furniture Allowance", default=0, compute="_get_salary_elements", readonly=False, store=True)
    education_alw = fields.Monetary(string="Education Allowance", default=0, compute="_get_salary_elements",readonly=False, store=True)
    supervision_alw = fields.Monetary(string="Supervision Allowance", default=0, compute="_get_salary_elements",readonly=False, store=True)
    mobilisation_alw = fields.Monetary(string="Mobilization Allowance", default=0, compute="_get_salary_elements",readonly=False, store=True)
    business_alw = fields.Monetary(string="Business Allowance", default=0, compute="_get_salary_elements",readonly=False, store=True)
    gross = fields.Monetary(string="Gross Salary", default=0, compute="_get_gross_amount", store=True)
    # job_level = fields.Selection(related="job_id.level", store=True)

    end_of_basic_salary_bonus = fields.Monetary(string="End of Basic Salary Bonus")
    monthly_incentive = fields.Monetary(string="Monthly Incentive")
    representative_monthly_allowance = fields.Monetary(string="Representative Monthly Allowance")
    work_condition_allowance = fields.Monetary(string="Work Condition Allowance")
    extra_amount = fields.Monetary('Extra Amount')

    @api.depends('wage', 'social_alw', 'housing_alw', 'transport_alw', 'other_alw', 'mobile_alw', 'car_alw',
                 'supervision_alw', 'extra_amount', 'end_of_basic_salary_bonus', 'monthly_incentive',
                 'representative_monthly_allowance', 'work_condition_allowance')
    def _get_gross_amount(self):
        for rec in self:
            rec.gross = rec.wage + rec.social_alw + rec.housing_alw + rec.transport_alw + rec.other_alw + rec.mobile_alw \
                        + rec.car_alw + rec.supervision_alw + rec.extra_amount + rec.end_of_basic_salary_bonus + rec.monthly_incentive \
                        + rec.representative_monthly_allowance + rec.work_condition_allowance

    @api.depends('payscale_id')
    def _get_salary_elements(self):
        for rec in self:
            payscale = rec.payscale_id
            res = {}
            if payscale:
                job_id = rec.job_id
                res.update({
                    # 'wage': payscale.basic_from,
                    'social_alw': payscale.social_allowance,
                    'housing_alw': payscale.housing_allowance,
                    'transport_alw': payscale.transport_allowance,
                    'other_alw': payscale.other_allowance,
                })

                if job_id and job_id.level == 'director':
                    res.update({
                        'mobile_alw': payscale.mob_department_director,
                        'car_alw': payscale.car_alw_dept_director,
                        'supervision_alw': payscale.supervision_unit_director,

                    })
                elif job_id and job_id.level == 'manager':
                    res.update({
                        'mobile_alw': payscale.mob_department_manager,
                        'car_alw': payscale.car_alw_dept_manager,
                        'supervision_alw': payscale.supervision_department_manager,

                    })
                elif job_id and job_id.level == 'assistant_manager':
                    res.update({
                        'mobile_alw': payscale.mob_other,
                        'car_alw': payscale.car_alw_other,
                        'supervision_alw': payscale.supervision_department_manager_ass,

                    })
                elif job_id and job_id.level == 'others':
                    res.update({
                        'mobile_alw': payscale.mob_other,
                        'car_alw': payscale.car_alw_other,
                        'supervision_alw': 0,
                    })
                else:
                    res.update({
                        'mobile_alw': 0,
                        'car_alw': 0,
                        'supervision_alw': 0,
                    })
                res.update({
                    'air_ticket_alw': payscale.air_ticket_allowance,
                    'furniture_alw': payscale.furniture_allowance,
                    'education_alw': payscale.education_allowance,
                    'mobilisation_alw': payscale.mobilisation_allowance,
                    'business_alw': payscale.business_allowance,
                    'car_loan': payscale.car_loan,
                    'marriage_loan': payscale.marriage_loan,

                })
                rec.write(res)
                rec.add_leave_type_lines()
            else:
                rec.write({
                    # 'wage': 0,
                    'social_alw': 0,
                    'housing_alw': 0,
                    'transport_alw': 0,
                    'other_alw': 0,
                    'mobile_alw': 0,
                    'car_alw': 0,
                    'air_ticket_alw': 0,
                    'furniture_alw': 0,
                    'education_alw': 0,
                    'supervision_alw': 0,
                    'mobilisation_alw': 0,
                    'business_alw': 0,
                    'car_loan': 0,
                    'marriage_loan': 0,
                })

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

    # @api.depends('employee_id.gender')
    # def _check_is_male(self):
    #     for rec in self:
    #         if rec.employee_id.gender == "male":
    #             rec.is_male = True
    #         else:
    #             rec.is_male = False

    @api.depends('is_married', 'is_qatari', 'employee_id.country_id', 'employee_id.gender')
    def _get_employee_payscale(self):
        for rec in self:
            rec.employee_payscale_domain = json.dumps(
                [('is_married', '=', rec.is_married), ('is_qatari', '=', rec.is_qatari)]
            )

    @api.onchange('state')
    def _create_allocation_in_running_state(self):
        for rec in self:
            if rec.state == 'open':
                for each_leave_type in rec.leave_type:
                    if each_leave_type and not each_leave_type.allocation_id:
                        allocation = rec.env['hr.leave.allocation'].create(
                            {
                                'name': each_leave_type.leave_type.name + ': ' + rec.employee_id.name,
                                'holiday_status_id': each_leave_type.leave_type.id,
                                'allocation_type': 'regular',
                                'holiday_type': 'employee',
                                'employee_id': rec.employee_id.id,
                                'number_of_days': each_leave_type.days,
                            }
                        )
                        each_leave_type.allocation_id = allocation

    def add_leave_type_lines(self):
        """Add leave type lines on contract"""
        for rec in self:
            payscale = rec.payscale_id
            if payscale and payscale.leave_type_ids:
                leaves_lines_list = []
                for leave_type in payscale.leave_type_ids:
                    leaves_lines_list.append(leave_type.id)
                rec.leave_type = [(4, line) for line in leaves_lines_list]

    @api.onchange('payscale_id')
    def _onchange_payscale(self):
        for rec in self:
            if rec.payscale_id:
                rec.wage = rec.payscale_id.basic_from

    @api.onchange('wage')
    def _onchange_wage_notification(self):
        for rec in self:
            if rec.wage:
                he_manager_role_users = self.env.ref(
                    'jbm_group_access_right_extended.custom_hr_manager').users
                if he_manager_role_users:
                    rec.sudo()._create_activity_for_hr_mangers(he_manager_role_users)

    def _create_activity_for_hr_mangers(self, users):
        for user in users:
            self.with_context(mail_activity_quick_update=True).activity_schedule(
                date_deadline=fields.Date.today(),
                activity_type_id=self.env.ref('mail.mail_activity_data_todo',
                                              raise_if_not_found=False).id, user_id=user.id)
