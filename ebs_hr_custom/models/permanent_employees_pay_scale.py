from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError


class PermanentEmployeePayScale(models.Model):
    _name = 'permanent.employee.pay.scale'
    _description = 'Pay Scale'

    name = fields.Integer(string="Grade", required=True, copy=False)
    description = fields.Char(string="Description", default="", required=True, copy=False)
    active = fields.Boolean(string="Active", default=True)
    employee_ids = fields.One2many(comodel_name="hr.employee", inverse_name="permanent_staff_employee",
                                   string="Employee", required=False)
    contract_ids = fields.One2many(comodel_name="hr.contract", inverse_name="permanent_staff_employee",
                                   string="Contract", required=False, )
    is_qatari = fields.Boolean(string="Qatari ?", default=True)
    is_married = fields.Boolean(string="Married ?", default=False)
    is_male = fields.Boolean(string="Male ?", default=False)
    is_female = fields.Boolean(string="Female ?", default=False)
    is_gcc_country = fields.Boolean(string="GCC ?", default=False)

    gender = fields.Selection([("male", 'Male'), ("female", 'Female'), ], string='Gender')
    basic_from = fields.Float(string="", default=0, required=False, )
    basic_to = fields.Float(string="", default=0, required=False, )
    social_allowance = fields.Float(string="Social Allowance ", default=0, required=False)
    housing_allowance = fields.Float(string="Housing Allowance", default=0, required=False)
    transport_allowance = fields.Float(string="Transport Allowance", default=0, required=False)
    mobile_allowance = fields.Float(string="Mobile Phone Allowance", default=0, required=False)
    air_ticket_allowance = fields.Selection(string="Annual Air Ticket Allowance ", default="b",
                                            selection=[('b', 'Business'), ('e', 'Economy')], required=False, )

    mobilisation_class = fields.Selection(string="Mobilisation Class", default="b",
                                          selection=[('b', 'Business'), ('e', 'Economy')], required=False, )
    mobilisation_allowance = fields.Float(string="Mobilisation/ Repatriation/Shipping Allowance", default=0,
                                          required=False)
    total_salary_from = fields.Float(string="", default=0, required=False)
    total_salary_to = fields.Float(string="", default=0, required=False)
    car_loan = fields.Float(string="Car Loan", default=0, required=False)
    marriage_loan = fields.Float(string="Marriage Loan", default=0, required=False)
    furniture_allowance = fields.Float(string="Furniture Allowance", default=0, required=False)
    education_allowance = fields.Float(string="Education Allowance", default=0, required=False)
    travel_class = fields.Selection(string="Travel Class", default="b",
                                    selection=[('b', 'Business'), ('e', 'Economy')], required=False, )
    business_allowance_non_gulf = fields.Float(string="BUSINESS/TRAINING TRIP All Countries", default=0, required=False)
    business_allowance_gulf = fields.Float(string="BUSINESS/TRAINING TRIP GCC", default=0, required=False)
    annual_leaves = fields.Integer(string="Annual Leaves", default=0, required=False)
    leave_carry_forwards = fields.Integer(string="Leave Carry Forwards")
    long_sick_leaves = fields.Integer(string="Long Sick Leaves")
    short_sick_leaves = fields.Integer(string="Short Sick Leaves")
    special = fields.Boolean(defalt=False)
    # employee_type = fields.Selection(string="Employment Category", default="perm_staff", required=True,
    #                                  selection=[('temp', 'Temporary Employee'),
    #                                             ('perm_staff', 'Permanent Staff')])

    emp_type_value = fields.Char(string="", default="Permanent Staff", required=False, )
    leave_type_ids = fields.One2many("contract.leave.type", "payscale_id", string="Leave Types")

    @api.constrains('leave_type_ids')
    def _check_leave_type(self):
        for rec in self:
            if rec.leave_type_ids:
                list_types = set(leave_type for leave_type in rec.leave_type_ids.leave_type)
                if len(list_types) != len(rec.leave_type_ids):
                    raise ValidationError(_('Please can not add the same leave type again.'))

    # @api.onchange('leave_type_ids.leave_type')
    # def _get_default_number_of_days(self):
    #     for rec in self:
    #         if rec.leave_type_ids:
    #             for leave_type in rec.leave_type_ids:
    #                 if leave_type.leave_type.default_days:
    #                     leave_type.days = leave_type.leave_type.default_days
    #                 else:
    #                     leave_type.days = 1

    def name_get(self):
        result = []
        for record in self:
            if record.special:
                rec_name = f"special {record.name} / {record.description}"
                result.append((record.id, "%s" % rec_name))
            if not record.special:
                rec_name = f"{record.name} / {record.description}"
                result.append((record.id, "%s" % rec_name))
        return result

    @api.constrains('basic_from', 'basic_to', 'total_salary_from', 'total_salary_to')
    def check_range_from_to(self):
        for rec in self:
            if rec.basic_to < rec.basic_from:
                raise ValidationError(_("Basic: basic lower limit (%s) shouldn't be higher than basic upper"
                                        " limit (%s)") %
                                      (rec.basic_from, rec.basic_to))
            if rec.total_salary_to < rec.total_salary_from:
                raise ValidationError(_("Salary Allowance : salary lower limit (%s) shouldn't "
                                        "be higher than salary upper limit (%s)") %
                                      (rec.total_salary_from, rec.total_salary_to))

    @api.constrains('name', 'is_qatari', 'is_married', 'gender', 'active', 'special')
    def constrains_unique_payscale(self):
        if not self.special:
            payscales = self.search([('id', '!=', self.id)])
            for payscale in payscales:
                if (
                        payscale.name == self.name and payscale.is_qatari == self.is_qatari and payscale.is_married == self.is_married
                        and payscale.gender == self.gender and payscale.active == self.active):
                    raise UserError('Duplicate group name or qatar or gender or married is not allowed!\n'
                                    'Please, enter another name or gender or qatar or married')
    # @api.depends('gender')
    # @api.onchange('gender')
    # def switch_between_genders(self):
    #     if self.gender == 'male':
    #         self.is_female = False
    #         self.is_male = True
    #     else:
    #         self.is_female = True
    #         self.is_male = False

    # @api.depends('is_male')
    # @api.onchange('is_male')
    # def switch_between_genders_upon_male(self):
    #     if self.is_male:
    #         self.is_female = False
    #     else:
    #         self.is_female = True
    #
    # @api.depends('is_female')
    # @api.onchange('is_female')
    # def switch_between_genders_upon_female(self):
    #     if self.is_female:
    #         self.is_male = False
    #     else:
    #         self.is_male = True

    # @api.depends('employee_type')
    # @api.onchange('employee_type')
    # def get_emp_type(self):
    #     if self.employee_type == 'temp':
    #         self.emp_type_value = 'temp'
    #     elif self.employee_type == 'perm_staff':
    #         self.emp_type_value = 'perm_staff'
    #     else:
    #         self.emp_type_value = 'temp'
    #     print(self.emp_type_value)
    # grade, is_qatar, gender and married
    # _sql_constraints = [('unique_payscale_group_active', 'unique(name,is_qatari,is_married,gender,active)',
    #                      'Duplicate group name or qatar or gender or married is not allowed!\n'
    #                      'Please, enter another name or gender or qatar or married')]
