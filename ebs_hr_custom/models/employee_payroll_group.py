from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError,ValidationError


class EmployeePayrollGroup(models.Model):
    _name = 'employee.payroll.group'
    _description = 'Groups'

    name = fields.Char(string="Name", default="", required=True, copy=False)
    active = fields.Boolean(string="Active", default=True)
    employee_ids = fields.One2many(comodel_name="hr.employee", inverse_name="payroll_group",
                                   string="Employee", required=False)
    contract_ids = fields.One2many(comodel_name="hr.contract", inverse_name="payroll_group",
                                   string="Contract", required=False, )
    basic_from = fields.Float(string="", default=750.0, required=False, )
    basic_to = fields.Float(string="", default=1000.0, required=False, )

    accommodation_from = fields.Float(string="", default=500.0, required=False, )
    accommodation_to = fields.Float(string="", default=1500.0, required=False, )

    transportation_from = fields.Float(string="", default=250.0, required=False, )
    transportation_to = fields.Float(string="", default=250.0, required=False, )

    food_from = fields.Float(string="", default=300.0, required=False, )
    food_to = fields.Float(string="", default=300.0, required=False, )

    site_from = fields.Float(string="", default=0.0, required=False, )
    site_to = fields.Float(string="", default=500.0, required=False, )

    total_salary_from = fields.Float(string="", default=750.0, required=False, )
    total_salary_to = fields.Float(string="", default=1500.0, required=False, )
    provided_1 = fields.Boolean(string="", default=False)
    provided_2 = fields.Boolean(string="", default=False)
    provided_3 = fields.Boolean(string="", default=False)
    uniform = fields.Float(string="Uniform", default=False)
    uniform_provided = fields.Boolean(string="Uniform provided by the company", default=False)

    annual_leaves = fields.Integer("Annual Leaves")
    long_sick_leaves = fields.Integer(string="Long Sick Leaves")
    short_sick_leaves = fields.Integer(string="Short Sick Leaves")

    fixed_food_allowance = fields.Boolean('Fixed Food Allowance', default=False)
    l_a_food_alw = fields.Boolean('Leave advance Food Allowance', default=False)

    # leave_type_ids = fields.One2many("contract.leave.type", "payroll_group_id", string="Leave Types")

    # @api.constrains('leave_type_ids')
    # def _check_leave_type(self):
    #     for rec in self:
    #         if rec.leave_type_ids:
    #             list_types = set(leave_type for leave_type in rec.leave_type_ids.leave_type)
    #             if len(list_types) != len(rec.leave_type_ids):
    #                 raise ValidationError(_('Please can not add the same leave type again.'))
    #
    # @api.onchange('leave_type_ids', 'leave_type_ids.leave_type')
    # @api.depends('leave_type_ids', 'leave_type_ids.leave_type')
    # def _get_default_number_of_days(self):
    #     for rec in self:
    #         if rec.leave_type_ids:
    #             for leave_type in rec.leave_type_ids:
    #                 if not leave_type.days:
    #                     if leave_type.leave_type.default_days:
    #                         leave_type.days = leave_type.leave_type.default_days
    #                     else:
    #                         leave_type.days = 1

    @api.constrains('basic_from', 'basic_to', 'accommodation_from', 'accommodation_to',
                    'transportation_from', 'transportation_to', 'food_from', 'food_to', 'site_from', 'site_to',
                    'total_salary_from', 'total_salary_to')
    def check_range_from_to(self):
        for rec in self:
            if rec.basic_to < rec.basic_from:
                raise ValidationError(_("Basic: basic lower limit (%s) shouldn't be higher than basic upper"
                                        " limit (%s)") %
                                      (rec.basic_from, rec.basic_to))
            elif rec.accommodation_to < rec.accommodation_from:
                raise ValidationError(_("Accommodation Allowance: accommodation lower limit (%s) shouldn't "
                                        "be higher than accommodation upper limit (%s)") %
                                      (rec.accommodation_from, rec.accommodation_to))
            elif rec.transportation_to < rec.transportation_from:
                raise ValidationError(_("Transportation Allowance: transportation lower limit (%s) shouldn't "
                                        "be higher than transportation upper limit (%s)") %
                                      (rec.transportation_from, rec.transportation_to))
            elif rec.food_to < rec.food_from:
                raise ValidationError(_("Food Allowance: food lower limit (%s) shouldn't "
                                        "be higher than food upper limit (%s)") %
                                      (rec.food_from, rec.food_to))
            elif rec.site_to < rec.site_from:
                raise ValidationError(_("Site Allowance : site lower limit (%s) shouldn't "
                                        "be higher than site upper limit (%s)") %
                                      (rec.site_from, rec.site_to))
            elif rec.total_salary_to < rec.total_salary_from:
                raise ValidationError(_("Salary Allowance : salary lower limit (%s) shouldn't "
                                        "be higher than salary upper limit (%s)") %
                                      (rec.total_salary_from, rec.total_salary_to))

    _sql_constraints = [('unique_group', 'unique(name)',
                         'Duplicate group name is not allowed!\nPlease, enter another name')]
