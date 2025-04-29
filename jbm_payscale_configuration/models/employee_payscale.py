from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import date, datetime


class PayScale(models.Model):
    _name = 'employee.payscale'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Pay Scale'

    name = fields.Integer(string="Grade", required=True, copy=False)
    description = fields.Char(string="Description", default="", required=True, copy=False)
    active = fields.Boolean(string="Active", default=True)
    employee_ids = fields.One2many(comodel_name="hr.employee", inverse_name="payscale_id",
                                   string="Employee")
    contract_ids = fields.One2many(comodel_name="hr.contract", inverse_name="payscale_id",
                                   string="Contract",)
    is_qatari = fields.Boolean(string="Qatari ?", default=True)
    is_married = fields.Boolean(string="Married ?", default=False)
    is_male = fields.Boolean(string="Male ?", default=False)
    is_female = fields.Boolean(string="Female ?", default=False)

    gender = fields.Selection([("male", 'Male'), ("female", 'Female'), ], string='Gender')
    basic_from = fields.Monetary(string="", default=0,)
    basic_mid = fields.Monetary(string="", default=0,)
    basic_to = fields.Monetary(string="", default=0,)
    social_allowance = fields.Monetary(string="Social Allowance ", default=0)
    housing_allowance = fields.Monetary(string="Housing Allowance", default=0)
    transport_allowance = fields.Monetary(string="Transport Allowance", default=0)
    other_allowance = fields.Monetary(string="Other Allowance", default=0)
    child_allowance = fields.Monetary(string="Child Allowance", default=0)
    medical_insurance = fields.Monetary(string="Medical Insurance", default=0)
    # mobile_allowance = fields.Monetary(string="Mobile Phone Allowance", default=0)
    mob_department_director = fields.Monetary(string="Department Director", default=0)
    mob_department_manager = fields.Monetary(string="Department Manager", default=0)
    mob_other = fields.Monetary(string="Others", default=0)
    car_alw_dept_director = fields.Monetary(string="Department Director", default=0)
    car_alw_dept_manager = fields.Monetary(string="Department Manager", default=0)
    car_alw_other = fields.Monetary(string="Others", default=0)
    air_ticket_allowance = fields.Selection(string="Annual Air Ticket Allowance ", default="b",
                                            selection=[('b', 'Business'), ('e', 'Economy')],)

    mobilisation_class = fields.Selection(string="Mobilisation Class", default="b",
                                          selection=[('b', 'Business'), ('e', 'Economy')],)
    mobilisation_allowance = fields.Monetary(string="Mobilisation/ Repatriation/Shipping Allowance", default=0,
                                          required=False)
    total_salary_from = fields.Monetary(string="", default=0)
    total_salary_to = fields.Monetary(string="", default=0)
    car_loan = fields.Monetary(string="Car Loan", default=0)
    marriage_loan = fields.Monetary(string="Marriage Loan", default=0)
    furniture_allowance = fields.Monetary(string="Furniture Allowance", default=0)
    education_allowance = fields.Monetary(string="Education Allowance", default=0)
    travel_class = fields.Selection(string="Travel Class", default="b",
                                    selection=[('b', 'Business'), ('e', 'Economy')],)
    business_allowance = fields.Monetary(string="BUSINESS/TRAINING TRIP All Countries", default=0)
    # business_allowance_gulf = fields.Monetary(string="BUSINESS/TRAINING TRIP GCC", default=0)
    supervision_unit_director = fields.Monetary(string="Unit Director", default=0)
    supervision_department_manager = fields.Monetary(string="Department Manager", default=0)
    supervision_department_manager_ass = fields.Monetary(string="Department Manager Assistant", default=0)
    annual_leaves = fields.Integer(string="Annual Leaves", default=0)
    leave_carry_forwards = fields.Integer(string="Leave Carry Forwards")
    long_sick_leaves = fields.Integer(string="Long Sick Leaves")
    short_sick_leaves = fields.Integer(string="Short Sick Leaves")
    special = fields.Boolean(defalt =False)
    emp_type_value = fields.Char(string="", default="Permanent Staff",)
    currency_id = fields.Many2one(string='Currency', comodel_name='res.currency', default=lambda x: x.env.company.currency_id)
    leave_type_ids = fields.One2many("contract.leave.type", "payscale_id", string="Leave Types")



    def _create_activity(self, all_users):
        all_users = all_users.sudo()
        activity_to_do = self.env.ref('mail.mail_activity_data_todo').id
        model_id = self.env['ir.model']._get('employee.payscale').id
        activity = self.env['mail.activity']
        for user in all_users:
            if user:
                act_dct = {
                    'activity_type_id': activity_to_do,
                    'note': "kindly check this Payscale Edite's!",
                    'user_id': user.id,
                    'res_id': self.id,
                    'res_model_id': model_id,
                    'date_deadline': datetime.today().date()
                }
                activity.sudo().create(act_dct)


    # def write(self, vals):
    #     object = super(PayScale, self).write(vals)
    #     if vals:
    #         users = self.env['res.users'].search([])
    #         if users:
    #             for user in users:
    #                 if user.has_group("jbm_group_access_right_extended.custom_group_shared_service_manager"):
    #                     self._create_activity(user)
    #     return object

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

    @api.constrains('name', 'is_qatari', 'is_married', 'active','special')
    def constrains_unique_payscale(self):
        if not self.special:
            pay_scales = self.search([('id', '!=', self.id)])
            for payscale in pay_scales:
                if (
                        payscale.name == self.name and payscale.is_qatari == self.is_qatari and payscale.is_married == self.is_married and payscale.active == self.active):
                    raise UserError('Duplicate group name or qatar or married is not allowed!\n'
                                    'Please, enter another name or qatar or married')
