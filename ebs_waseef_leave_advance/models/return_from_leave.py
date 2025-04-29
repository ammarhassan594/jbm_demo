from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from calendar import monthrange


class ReturnFromLeave(models.Model):
    _name = 'return.from.leave'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Return From Leaves"
    _rec_name = 'employee_id'

    def action_approve(self):
        # self.create_allocation()
        total_days = 0
        for rec in self:
            rec.leave_id.state = 'draft'
            rec.leave_id.planned_return_date = rec.leave_id.date_to
            rec.leave_id.date_to = rec.return_date
            rec.state = 'approved'
            rec.leave_id.state = 'validate'
            if rec.return_date and rec.leave_id.date_from and rec.employee_id:
                if rec.employee_id.employee_type == 'perm_staff':
                    total_days = rec.employee_id.resource_calendar_id.sudo().get_working_days(rec.leave_id.date_from.date(), rec.return_date)
                    rec.leave_id.sudo().write({
                        'number_of_days_display': total_days,
                        'number_of_days': total_days,
                    })

    # def action_payslip(self):
    #     self.state = 'payslip'

    def action_cancel(self):
        self.state = 'cancel'

    employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee", required=True,
                                  domain="[('wassef_employee_type', '=', 'perm_in_house')]")

    leave_id = fields.Many2one(comodel_name="hr.leave", string="Leaves", required=True,
                               domain="[('employee_id','=',employee_id), ('holiday_status_id.is_annual', '=', True),"
                                      "('has_leave_advance', '=', True)]")
    return_date = fields.Date(string="Return Date", default="", required=False)

    # date_to = fields.Date(string="Date To", default="", related='leave_id.request_date_to', readonly=True, store=True)
    date_to = fields.Date(string="Date To", default="", readonly=True, store=True)

    pay_on = fields.Date(string="Pay on", default="", required=False)

    payslip_id = fields.Many2one(comodel_name="hr.payslip", string="Payslip", required=False, readonly=True)
    currency_id = fields.Many2one('res.currency', related="employee_id.contract_id.currency_id")

    wage = fields.Monetary('Basic Salary', required=False, related="employee_id.contract_id.wage")
    return_wage = fields.Monetary('Return Basic Salary', required=False)

    has_wage = fields.Boolean(string="", default=False, related="leave_id.has_wage")

    accommodation = fields.Monetary('Accommodation', related="employee_id.contract_id.accommodation")
    return_accommodation = fields.Monetary('Return Accommodation', )
    has_accommodation = fields.Boolean(string="", default=False, related="leave_id.has_accommodation")

    mobile_allowance = fields.Monetary('Mobile Allowance',
                                       related="employee_id.contract_id.accommodation")
    return_mobile_allowance = fields.Monetary('Return Mobile Allowance')
    has_mobile_allowance = fields.Boolean(string="", default=False, related="leave_id.has_mobile_allowance")

    food_allowance = fields.Monetary('Food Allowance', related="employee_id.contract_id.accommodation")
    return_food_allowance = fields.Monetary(' Return Food Allowance')

    has_food_allowance = fields.Boolean(string="", default=False, related="leave_id.has_food_allowance")

    site_allowance = fields.Monetary('Site Allowance',
                                     related="employee_id.contract_id.accommodation")
    return_site_allowance = fields.Monetary('Site Allowance')
    has_site_allowance = fields.Boolean(string="", default=False, related="leave_id.has_site_allowance")

    transport_allowance = fields.Monetary('Transport Allowance',
                                          related="employee_id.contract_id.accommodation")

    return_transport_allowance = fields.Monetary('Return Transport Allowance')

    has_transport_allowance = fields.Boolean(string="", default=False, related="leave_id.has_transport_allowance")

    other_allowance = fields.Monetary('Other Allowance',
                                      related="employee_id.contract_id.accommodation")

    return_other_allowance = fields.Monetary('Return Other Allowance')

    has_other_allowance = fields.Boolean(string="", default=False, related="leave_id.has_transport_allowance")

    return_uniform_allowance = fields.Monetary('Leave Uniform Allowance')

    has_uniform_allowance = fields.Boolean(string="", default=False, related="leave_id.has_uniform_allowance")

    uniform_allowance = fields.Monetary('Uniform Allowance', related="employee_id.contract_id.uniform")
    has_leave_advance = fields.Boolean(compute='get_is_leave_advance', readonly=False)

    def get_is_leave_advance(self):
        for rec in self:
            rec.has_leave_advance = rec.leave_id.has_leave_advance

    # state = fields.Selection([
    #     ('draft', 'draft'),
    #     ('approved', 'Approved'),
    #     ('payslip', 'Payslip'),
    #     ('cancel', 'Cancel')], string='Status', readonly=True, default='draft', tracking=True)
    state = fields.Selection([
        ('draft', 'draft'),
        ('approved', 'Approved'),
        ('cancel', 'Cancel')], string='Status', readonly=True, default='draft')

    def _get_date_to_value(self):
        for rec in self:
            if rec.leave_id.date_to:
                return rec.leave_id.date_to

    @api.depends('employee_id', 'leave_id', 'return_date')
    def compute_return_payslip(self):
        for rec in self:
            if rec.return_date and rec.date_to and rec.leave_id.has_leave_advance:
                rec._calculate_actual_return_amount()

    # to calculate the leave amount based on the number of actual leave days
    def _calculate_actual_return_amount(self):
        for rec in self:
            difference = (rec.date_to - rec.return_date).days + 1
            if rec.has_wage:
                rec.return_wage = difference * rec.wage / 30
            else:
                rec.return_wage = 0

            if rec.accommodation:
                rec.return_accommodation = difference * rec.accommodation / 30
            else:
                rec.return_accommodation = 0

            if rec.has_transport_allowance:
                rec.return_transport_allowance = difference * rec.transport_allowance / 30
            else:
                rec.return_transport_allowance = 0

            if rec.has_food_allowance:
                rec.return_food_allowance = difference * rec.food_allowance / 30
            else:
                rec.return_food_allowance = 0

            if rec.has_site_allowance:
                rec.return_site_allowance = difference * rec.site_allowance / 30
            else:
                rec.return_site_allowance = 0

            if rec.has_other_allowance:
                rec.return_other_allowance = difference * rec.other_allowance / 30
            else:
                rec.return_other_allowance = 0

            if rec.has_mobile_allowance:
                rec.return_mobile_allowance = difference * rec.mobile_allowance / 30
            else:
                rec.return_mobile_allowance = 0
            if rec.has_uniform_allowance:
                rec.return_uniform_allowance = difference * rec.uniform_allowance / 30
            else:
                rec.return_mobile_allowance = 0

    def get_number_of_days_in_month(self, year, month):
        return monthrange(year, month)[1]

    # @api.onchange('return_date')
    # @api.constrains('return_date')
    # def _check_if_return_date_within_leave_range(self):
    #     if self.employee_id and self.leave_id:
    #         if not self.leave_id.request_date_from <= self.return_date <= self.date_to:
    #             raise ValidationError(f'Return date should be within the range {self.leave_id.request_date_from}'
    #                                   f'and {self.date_to}')

    # @api.onchange('pay_on')
    # @api.constrains('pay_on')
    # def _check_pay_on_date(self):
    #     if self.employee_id and self.leave_id and self.pay_on:
    #         if self.pay_on <= self.date_to:
    #             raise ValidationError(f'Pay On date should be after {self.date_to}')

    # def create_allocation(self):
    #     """ create allocation with the remaining number of leave days
    #             after the employee has returned early from his leave """
    #     allocation = {
    #         'name': self.employee_id.name + "'s allocation from early return",
    #         'holiday_type': 'employee',
    #         'employee_id': self.employee_id.id,
    #         'number_of_days': (self.date_to - self.return_date).days,
    #         'holiday_status_id': self.leave_id.holiday_status_id.id,
    #         'allocation_type': 'regular',
    #     }
    #     self.env['hr.leave.allocation'].create(allocation)
