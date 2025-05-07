import calendar
from datetime import datetime, time

from odoo import models, fields, api, _


class EmployeeManager(models.Model):
    _inherit = "hr.employee"

    def _get_year_selection(self):
        """Generate a list of years from 1900 to the current year + 80."""
        current_year = datetime.now().year
        return [(str(year), str(year)) for year in range(1900, current_year + 80)]

    allocation_ids = fields.Many2many('hr.leave.allocation', string="Allocation", compute="_get_employee_allocation")
    # allowed_violation_balance = fields.Float(related="allowed_violation_balance",
    #                                          string="Violation Balance")
    # employee_violation_balance = fields.Float(related="employee_violation_balance",
    #                                           string="Current Negative Violation Balance")

    leave_start_date = fields.Date(string="Start Date")
    leave_end_date = fields.Date(string="End Date")
    leave_ids = fields.Many2many("hr.leave", string="Leaves", compute="_get_employee_leaves")

    attendance_month_selection = fields.Selection([
        ('1', 'January'), ('2', 'February'), ('3', 'March'),
        ('4', 'April'), ('5', 'May'), ('6', 'June'),
        ('7', 'July'), ('8', 'August'), ('9', 'September'),
        ('10', 'October'), ('11', 'November'), ('12', 'December'),
    ], string="Month")
    attendance_year_selection = fields.Selection(
        selection=_get_year_selection,
        string="Year",
        default=str(datetime.now().year),
    )
    attendance_ids = fields.Many2many('hr.attendance', string="Employee Attendances",
                                      compute="_get_employee_attendances")

    finance_month_selection = fields.Selection([
        ('1', 'January'), ('2', 'February'), ('3', 'March'),
        ('4', 'April'), ('5', 'May'), ('6', 'June'),
        ('7', 'July'), ('8', 'August'), ('9', 'September'),
        ('10', 'October'), ('11', 'November'), ('12', 'December'),
    ], string="Month")

    finance_year_selection = fields.Selection(
        selection=_get_year_selection,
        string="Year",
        default=str(datetime.now().year),
    )
    payslip_ids = fields.Many2many('hr.payslip', string="Salary", compute="_get_employee_salary")
    loan_ids = fields.Many2many('hr.loan', string="Loans", compute="_get_employee_loans")
    allowance_ids = fields.Many2many('allowance.request', string="Allowances", compute="_get_employee_allowances")

    employee_promotion_ids = fields.Many2many('employee.promotion', string="Promotions",
                                              compute="_get_employee_promotions")

    approval_month_selection = fields.Selection([
        ('1', 'January'), ('2', 'February'), ('3', 'March'),
        ('4', 'April'), ('5', 'May'), ('6', 'June'),
        ('7', 'July'), ('8', 'August'), ('9', 'September'),
        ('10', 'October'), ('11', 'November'), ('12', 'December'),
    ], string="Month")

    approval_year_selection = fields.Selection(
        selection=_get_year_selection,
        string="Year",
        default=str(datetime.now().year),
    )
    approval_request_ids = fields.Many2many('approval.request', string="Requests", compute="_get_employee_approval_request")

    def _get_employee_allocation(self):
        current_year = datetime.now().year
        for record in self:
            employee_allocations = self.env['hr.leave.allocation'].search([
                ('employee_id', '=', record.id),
                ('year', '=', current_year),
                ('state', '=', 'validate')
            ])
            record.allocation_ids = employee_allocations if employee_allocations else None

    @api.onchange('leave_start_date', 'leave_end_date')
    @api.depends('leave_start_date', 'leave_end_date')
    def _get_employee_leaves(self):
        for record in self:
            employee_leaves = self.env['hr.leave'].search([
                ('employee_ids', '=', self._origin.id),
                ('request_date_from', '>=', record.leave_start_date),
                ('request_date_to', '<=', record.leave_end_date)
            ])
            record.leave_ids = employee_leaves if employee_leaves else None


    @api.onchange('attendance_month_selection', 'attendance_year_selection')
    @api.depends('attendance_month_selection', 'attendance_year_selection')
    def _get_employee_attendances(self):
        for record in self:
            if record.attendance_month_selection and record.attendance_year_selection:
                first_day_of_month = datetime(int(record.attendance_year_selection),
                                              int(record.attendance_month_selection), 1)
                last_day_of_month = datetime(int(record.attendance_year_selection),
                                             int(record.attendance_month_selection),
                                             calendar.monthrange(int(record.attendance_year_selection),
                                                                 int(record.attendance_month_selection))[1])
                first_day_of_month = datetime.combine(first_day_of_month, datetime.min.time())
                last_day_of_month = datetime.combine(last_day_of_month, time(23, 59, 59))

                employee_attendances = self.env['hr.attendance'].search([
                    ('employee_id', '=', self._origin.id),
                    ('check_in', '>=', first_day_of_month),
                    ('check_out', '<=', last_day_of_month)
                ])
                record.attendance_ids = employee_attendances.ids if employee_attendances else None
            else:
                record.attendance_ids = None


    @api.depends('finance_month_selection', 'finance_year_selection')
    @api.onchange('finance_month_selection', 'finance_year_selection')
    def _get_employee_salary(self):
        for record in self:
            if record.finance_month_selection and record.finance_year_selection:
                first_day_of_month = datetime(int(record.finance_year_selection),
                                              int(record.finance_month_selection), 1)
                last_day_of_month = datetime(int(record.finance_year_selection),
                                             int(record.finance_month_selection),
                                             calendar.monthrange(int(record.finance_year_selection),
                                                                 int(record.finance_month_selection))[1])

                employee_payslips = self.env['hr.payslip'].search([
                    ('employee_id', '=', self._origin.id),
                    ('date_from', '>=', first_day_of_month),
                    ('date_to', '<=', last_day_of_month)
                ])

                record.payslip_ids = employee_payslips.ids if employee_payslips else None
            else:
                record.payslip_ids = None

    def _get_employee_loans(self):
        for record in self:
            employee_loans = self.env['hr.loan'].search([
                ('employee_id', '=', self._origin.id),
                ('state', 'not in', ['draft', 'settle', 'refuse', 'cancel'])
            ])

            record.loan_ids = employee_loans.ids if employee_loans else None


    @api.depends('finance_month_selection', 'finance_year_selection')
    @api.onchange('finance_month_selection', 'finance_year_selection')
    def _get_employee_allowances(self):
        for record in self:
            if record.finance_month_selection and record.finance_year_selection:
                first_day_of_month = datetime(int(record.finance_year_selection),
                                              int(record.finance_month_selection), 1)
                last_day_of_month = datetime(int(record.finance_year_selection),
                                             int(record.finance_month_selection),
                                             calendar.monthrange(int(record.finance_year_selection),
                                                                 int(record.finance_month_selection))[1])

                employee_allowances = self.env['allowance.request'].search([
                    ('employee_id', '=', self._origin.id),
                    ('date', '>=', first_day_of_month),
                    ('date', '<=', last_day_of_month),
                ])
                record.allowance_ids = employee_allowances.ids if employee_allowances else None
            else:
                record.allowance_ids = None

    def _get_employee_promotions(self):
        for record in self:
            employee_promotions = self.env['employee.promotion'].search([
                ('employee_id', '=', self._origin.id),
            ])
            record.employee_promotion_ids = employee_promotions.ids if employee_promotions else None


    @api.depends('approval_month_selection', 'approval_year_selection')
    @api.onchange('approval_month_selection', 'approval_year_selection')
    def _get_employee_approval_request(self):
        for record in self:
            if record.approval_month_selection and record.approval_year_selection:
                first_day_of_month = datetime(int(record.approval_year_selection),
                                              int(record.approval_month_selection), 1)
                last_day_of_month = datetime(int(record.approval_year_selection),
                                             int(record.approval_month_selection),
                                             calendar.monthrange(int(record.approval_year_selection),
                                                                 int(record.approval_month_selection))[1])
                approval_requests = self.env['approval.request'].search([
                    ('create_uid', '=', self._origin.user_id.id),
                    ('date', '>=', first_day_of_month),
                    ('date', '<=', last_day_of_month)
                ])
                record.approval_request_ids = approval_requests.ids if approval_requests else None
            else:
                record.approval_request_ids = None
