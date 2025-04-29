# -*- coding: utf-8 -*-
from datetime import date
from odoo import fields, models, api, _
from odoo.exceptions import Warning, UserError
from sys import platform
from datetime import datetime
from dateutil import relativedelta
from pytz import timezone


class EmployeeGratuity(models.Model):
    _name = 'hr.gratuity'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Employee Gratuity"

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('first_approve', 'First Approved'),
        ('approve', 'Approved'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled')],
        default='draft')
    name = fields.Char(string='Reference', required=True, copy=False,
                       readonly=True,
                       default=lambda self: _('New'))
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  required=True, help="Employee")
    employee_contract_type = fields.Selection([
        ('limited', 'Limited'),
        ('unlimited', 'Unlimited')], string='Contract Type', readonly=True,
        store=True, help="Choose the contract type."
                         "if contract type is limited then during gratuity settlement if you have not specify the end date for contract, gratuity configration of limited type will be taken or"
                         "if contract type is Unlimited then during gratuity settlement if you have specify the end date for contract, gratuity configration of limited type will be taken.")
    employee_joining_date = fields.Date(string='Joining Date', readonly=True,
                                        store=True, help="Employee joining date")
    wage_type = fields.Selection([('monthly', 'Monthly Fixed Wage'), ('hourly', 'Hourly Wage')],
                                 help="Select the wage type monthly or hourly")
    total_working_years = fields.Float(string='Total Years Worked', readonly=True, store=True,
                                       help="Total working years")
    employee_probation_years = fields.Float(string='Leaves Taken(Years)', readonly=True, store=True,
                                            help="Employee probation years")
    employee_probation_days = fields.Float(string='Unpaid Leaves(Days)', readonly=True, store=True,
                                           help="Employee Unpaid Leaves days")
    is_employee_probation_years = fields.Boolean(string="is in ?", default=False)
    employee_gratuity_years = fields.Float(string='Gratuity Calculation Years',
                                           readonly=True, store=True, help="Employee gratuity years")
    employee_basic_salary = fields.Float(string='Basic Salary',
                                         readonly=True,
                                         help="Employee's basic salary.")
    employee_gratuity_duration = fields.Many2one('gratuity.configuration',
                                                 readonly=True,
                                                 string='Configuration Line')

    employee_gratuity_amount = fields.Float(string='Total Gratuity Payment', readonly=True, store=True,
                                            help="Gratuity amount for the employee. \it is calculated If the wage type is hourly then gratuity payment is calculated as employee basic salary * Employee Daily Wage Days * gratuity configration rule percentage * gratuity calculation years.orIf the wage type is monthly then gratuity payment is calculated as employee basic salary * (Working Days/Employee Daily Wage Days) * gratuity configration rule percentage * gratuity calculation years.")
    gratuity_amount = fields.Float(string='Gratuity Payment', readonly=True, store=True)

    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 default=lambda self: self.env.company, help="Company")
    currency_id = fields.Many2one(related="company_id.currency_id",
                                  string="Currency", readonly=True, help="Currency")

    ticket_entitlement = fields.Monetary('Ticket entitlement')
    ticket_to_home = fields.Boolean('Ticket to home town')

    effective_date = fields.Date(string="Effective Date", default=lambda self: fields.Datetime.now())
    other_deductions = fields.Float(string="Other Deductions", default=0.0)
    notice_period = fields.Selection(string="Notice Period", default="1", selection=[('1', '1 Month'),
                                                                                     ('2', '2 Months')])
    is_notice_period = fields.Boolean(string="is in notice period ?", default=False)
    total_notice_pay = fields.Float(string='Total Notice Pay', compute='_notice_period   ', readonly=True, store=True)
    leave_balance_years = fields.Float(string='Leave Balance', readonly=True, store=True,
                                       help="Leave Balance")
    leave_balance_days = fields.Float(string='Leave Balance', readonly=True, store=True,
                                      help="Leave Balance")
    advance_salary = fields.Float(string='Advance Salary', readonly=True, store=True,
                                  help="Advance Salary")
    total_working_days = fields.Float(string='Total Days Worked', readonly=True, store=True)
    salary_rate = fields.Float(string='Salary Rate', readonly=True, store=True)
    leave_salary_rate = fields.Float(string='Leave Salary Rate', readonly=True, store=True)
    gross_salary = fields.Float(string='Gross Salary', readonly=True, store=True)
    status = fields.Selection([('active', 'Active'), ('on vacation', 'On Vacation'),
                               ('terminated', 'Terminated'), ('terminated_w_reason', 'Terminated with Reason'),
                               ('resigned', 'Resigned')],
                              string='Status', related='employee_id.status')
    total_amount_working_days_no_store = fields.Float(string='Gratuity Payment', compute='_onchange_employee_id', default=0.0, store=True)

    total_amount_working_days = fields.Float(string='Gratuity Payment', readonly=True, store=True,
                                             related='total_amount_working_days_no_store')
    other_additions = fields.Float(string='Other Additions', store=True)
    any_material = fields.Float(string='Any Material', store=True)
    notice_period_deduction = fields.Float(string='Notice Period Deduction', store=True)
    misc_deduction = fields.Float(string='Misc Deduction', store=True)
    total_amount_deduction = fields.Float(string='Total Amount Deduction', compute='_total_amount_deduction',
                                          store=True)
    leaves_amount = fields.Float(string='Leaves Amount', compute='_leaves_amount',
                                 store=True)
    total_amount_pay = fields.Float(string='Total Amount Pay', compute='_total_amount_pay',
                                    store=True)
    total_amount_final_settlement = fields.Float(string='Amount Final Settlement', compute='_amount_final_settlement',
                                                 store=True)
    deduction_remarks = fields.Char(string='Deduction Remarks')
    addition_remarks = fields.Char(string='Addition Remarks')

    mode_final_settlement = fields.Selection(
        [('cash', 'Cash'), ('cheque', 'Cheque'), ('bank_transfer', 'Bank Transfer')],
        help="Select the Mode Final Settlement", required=True)
    ref_final_settlement = fields.Char(string='Cheque No./Bank Transfer Reference')
    date_final_settlement = fields.Date(string="Date")
    attachment_ids = fields.Many2many('ir.attachment', string='Attachment',
                                      help='You can attach the copy of your document', copy=False)
    eosb_advance_deduction = fields.Float(readonly=True, compute='_onchange_eosb_advance',
                                          help="EOSB Advance Deduction")
    ticket_deduction = fields.Float(readonly=True, compute='_onchange_ticket_ded', string='Ticket Deduction',
                                    help="Ticket Deduction")
    furniture_deduction = fields.Float(readonly=True, compute='_onchange_furniture_ded', string='Furniture Allowance',
                                       help="Furniture Allowance")
    termination_type = fields.Selection([('resignation_term', 'RESIGNATION / TERMINATION'), ('termination_cause', 'TERMINATION “FOR CAUSE”')])
    loan_deduction = fields.Float(readonly=True, compute='_onchange_loan_deduction',
                                  help="Loan Deduction")
    payslip_count = fields.Integer(compute='compute_count')

    def compute_count(self):
        for record in self:
            record.payslip_count = self.env['hr.payslip'].search_count(
                [('employee_id', '=', self.employee_id.id)])

    def get_payslips(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payslips',
            'view_mode': 'tree',
            'res_model': 'hr.payslip',
            'domain': [('employee_id', '=', self.employee_id.id)],
            'context': "{'create': False}"
        }

    @api.model
    def create(self, vals):
        """ assigning the sequence for the record """
        # vals['name'] = self.env['ir.sequence'].next_by_code('hr.gratuity')
        return super(EmployeeGratuity, self).create(vals)

    @api.depends('is_notice_period')
    @api.onchange('is_notice_period')
    def _notice_period(self):
        if self.is_notice_period:
            self.total_notice_pay = self.gross_salary * float(self.notice_period)
        else:
            self.total_notice_pay -= (self.gross_salary * float(self.notice_period))

    @api.depends('employee_id')
    @api.onchange('employee_id')
    def _onchange_ticket_ded(self):
        ticket = self.env['allowance.type'].sudo().search([('code', '=', 'ticket')]).id
        for rec in self:
            rec.ticket_deduction = 0.0
            if ticket and rec.employee_id and rec.effective_date:
                ticket_allowance = self.env['allowance.request'].sudo().search(
                    [('employee_id', '=', rec.employee_id.id), ('allowance_type', '=', ticket), ('state', '=', 'paid')],
                    order='id desc', limit=1)
                last_day_of_year = datetime.now().date().replace(month=12, day=31)
                total_days = (last_day_of_year - rec.effective_date).days
                rec.ticket_deduction = ticket_allowance.eligible_amount * (total_days/365)

    @api.depends('employee_id', 'termination_type', 'effective_date')
    @api.onchange('employee_id', 'termination_type', 'effective_date')
    def _onchange_furniture_ded(self):
        for rec in self:
            rec.furniture_deduction = 0.0
            furniture_allowance = 0.0
            if rec.employee_id.employee_type == 'perm_staff':
                furniture_allowance = self.env['hr.contract'].sudo().search(
                    [('employee_id', '=', rec.employee_id.id), ('state', '=', 'open')], limit=1).furniture_allowance_for_permanent_staff
            if rec.employee_id.joining_date and rec.effective_date and rec.termination_type and furniture_allowance:
                delta = (rec.effective_date - rec.employee_id.joining_date).days
                if rec.termination_type == 'resignation_term':
                    if delta < 365:
                        rec.furniture_deduction = furniture_allowance * 60 / 100
                    elif delta >= 365 and delta < 730:
                        rec.furniture_deduction = furniture_allowance * 40 / 100
                    elif delta >= 730 and delta < 1095:
                        rec.furniture_deduction = furniture_allowance * 30 / 100
                    elif delta >= 1095 and delta < 1460:
                        rec.furniture_deduction = furniture_allowance * 10 / 100
                elif rec.termination_type == 'termination_cause':
                    if delta < 365:
                        rec.furniture_deduction = furniture_allowance * 80 / 100
                    elif delta >= 365 and delta < 730:
                        rec.furniture_deduction = furniture_allowance * 60 / 100
                    elif delta >= 730 and delta < 1095:
                        rec.furniture_deduction = furniture_allowance * 40 / 100
                    elif delta >= 1095 and delta < 1460:
                        rec.furniture_deduction = furniture_allowance * 20 / 100


    @api.depends('employee_id')
    @api.onchange('employee_id')
    def _onchange_eosb_advance(self):
        self.eosb_advance_deduction = 0
        eosb_advance_deduction = self.env['allowance.request'].search([('employee_id', '=', self.employee_id.id),
                                                                       ('allowance_type.code', '=', 'eosb'),
                                                                       ('state', '=', 'approved')])
        if eosb_advance_deduction:
            self.eosb_advance_deduction = eosb_advance_deduction.requested_amount

    @api.depends('employee_id')
    @api.onchange('employee_id')
    def _onchange_loan_deduction(self):
        self.loan_deduction = 0
        loan_deduction = self.env['hr.loan'].search([('employee_id', '=', self.employee_id.id),
                                                     ('state', '=', 'paid')])
        for rec in loan_deduction:
            if rec:
                self.loan_deduction = rec.balance_amount

    @api.depends('leave_balance_days', 'leave_salary_rate')
    @api.onchange('leave_balance_days', 'leave_salary_rate')
    def _leaves_amount(self):
        for each in self:
            if each.leave_balance_days or each.leave_salary_rate:
                each.leaves_amount = each.leave_salary_rate * each.leave_balance_days
            else:
                each.leaves_amount = 0

    @api.depends('any_material', 'notice_period_deduction', 'advance_salary', 'other_deductions',
                 'misc_deduction', 'eosb_advance_deduction', 'loan_deduction', 'ticket_deduction', 'furniture_deduction')
    @api.onchange('any_material', 'notice_period_deduction', 'advance_salary', 'other_deductions',
                  'misc_deduction', 'eosb_advance_deduction', 'loan_deduction', 'ticket_deduction', 'furniture_deduction')
    def _total_amount_deduction(self):
        if self.other_deductions or self.misc_deduction or self.advance_salary or self.any_material or \
                self.notice_period_deduction or self.eosb_advance_deduction or self.loan_deduction or \
                self.ticket_deduction or self.furniture_deduction:
            self.total_amount_deduction = self.other_deductions + self.misc_deduction + self.advance_salary + \
                                          self.any_material + self.notice_period_deduction + self.furniture_deduction +\
                                          self.eosb_advance_deduction + self.loan_deduction + self.ticket_deduction
        else:
            self.total_amount_deduction = 0

    @api.depends('total_amount_working_days', 'total_notice_pay', 'ticket_entitlement', 'leaves_amount',
                 'other_additions')
    @api.onchange('total_amount_working_days', 'total_notice_pay', 'ticket_entitlement', 'leaves_amount',
                  'other_additions')
    def _total_amount_pay(self):
        for each in self:
            if each.total_amount_working_days or each.total_notice_pay or each.ticket_entitlement or each.other_additions \
                    or each.leaves_amount:
                each.total_amount_pay = each.total_amount_working_days + each.total_notice_pay + \
                                        each.ticket_entitlement + each.other_additions + each.leaves_amount
            else:
                each.total_amount_pay = 0

    @api.depends('total_amount_deduction', 'total_amount_pay')
    @api.onchange('total_amount_deduction', 'total_amount_pay')
    def _amount_final_settlement(self):
        for each in self:
            if each.total_amount_deduction or each.total_amount_pay:
                each.total_amount_final_settlement = each.total_amount_pay - each.total_amount_deduction
            else:
                each.total_amount_final_settlement = 0

    @api.depends('employee_id', 'ticket_entitlement', 'is_employee_probation_years', 'effective_date',
                 'other_deductions', 'notice_period', 'is_notice_period', 'total_amount_deduction')
    @api.onchange('employee_id', 'ticket_entitlement', 'is_employee_probation_years', 'effective_date',
                  'other_deductions', 'notice_period', 'is_notice_period', 'total_amount_deduction')
    def _onchange_employee_id(self):
        """ calculating the gratuity pay based on the contract and gratuity
        configurations """
        # each.ensure_one()
        for each in self:
            each.total_amount_working_days_no_store = 0
            if each.employee_id.id:
                leave_id = self.env['hr.leave.type'].search([('is_unpaid', '=', True)], limit=1)
                unpaid_leave_ids = self.env['hr.leave'].search([('employee_id', '=', each.employee_id.id),
                                                                ('holiday_status_id', '=', leave_id.id),
                                                                ('state', '=', 'validate')])
                leave_allocation_id = self.env['hr.leave.type'].search([('is_annual', '=', True)], limit=1)
                annual_leave_ids = self.env['hr.leave'].search([('employee_id', '=', each.employee_id.id),
                                                                ('holiday_status_id', '=', leave_allocation_id.id),
                                                                ('state', '=', 'validate')])
                annual_allocation_ids = self.env['hr.leave.allocation'].search(
                    [('employee_id', '=', each.employee_id.id),
                     ('holiday_status_id', '=',
                      leave_allocation_id.id),
                     ('state', '=', 'validate')])
                allowance_amount = 0
                allowance_request_id = self.env['ebs.payroll.allowance.request'].search([
                    ('employee_id', '=', each.employee_id.id)])
                if allowance_request_id:
                    for each_allowance_request in allowance_request_id:
                        allowance_request_line_id = self.env['ebs.payroll.allowance.request.lines'].search([
                            ('parent_id', '=', each_allowance_request.id)])
                        for each_allowance_request_lines in allowance_request_line_id:
                            if not each_allowance_request_lines.payslip_id:
                                allowance_amount = allowance_amount + each_allowance_request_lines.amount
                                each.advance_salary = allowance_amount
                annual_leave_days = 0
                annual_allocation_days = 0
                for each_annual_allocation in annual_allocation_ids:
                    annual_allocation_days += each_annual_allocation.number_of_days
                for each_annual_leave in annual_leave_ids:
                    annual_leave_days += each_annual_leave.number_of_days
                leave_balance_days = annual_allocation_days - annual_leave_days
                each.leave_balance_days = leave_balance_days
                if not each.employee_id.contract_id:
                    raise Warning(_('No contracts found for the selected employee...!\n'
                                    'Employee must have at least one contract to compute gratuity settelement.'))
                else:
                    gross_salary = each.employee_id.contract_id.gross_salary
                    each.gross_salary = gross_salary
                    if each.employee_id.employee_type == 'perm_in_house':
                        each.leave_salary_rate = each.employee_basic_salary / 30
                    elif each.employee_id.employee_type == 'perm_staff':
                        each.leave_salary_rate = each.gross_salary / (((365/12)/7)*5)
                    else:
                        # each.leave_salary_rate = each.gross_salary / 30
                        raise Warning("Employee type does not exist")
                each.employee_joining_date = joining_date = each.employee_id.contract_id.date_start
                employee_probation_days = 0
                # find total probation days
                for unpaid_leave in unpaid_leave_ids:
                    employee_probation_days += unpaid_leave.number_of_days
                each.employee_probation_days = employee_probation_days
                # get running contract
                hr_contract_id = self.env['hr.contract'].search(
                    [('employee_id', '=', each.employee_id.id), ('state', '=', 'open')])
                if len(hr_contract_id) > 1 or not hr_contract_id:
                    raise Warning(_('Selected employee have multiple or no running contracts!'))
                each.wage_type = hr_contract_id.wage_type

                each.employee_basic_salary = hr_contract_id.wage

                if each.effective_date:
                    # each.employee_contract_type = 'limited'
                    each.employee_contract_type = 'unlimited'
                    employee_working_days = (each.effective_date - joining_date).days
                    each.total_working_days = employee_working_days
                    each.total_working_years = employee_working_days / 365
                    if each.is_employee_probation_years:
                        each.employee_probation_years = employee_probation_days / 365
                        each.leave_balance_years = leave_balance_days / 365
                        employee_gratuity_years = (employee_working_days - employee_probation_days) / 365
                        each.employee_gratuity_years = employee_gratuity_years
                    else:
                        each.employee_gratuity_years = employee_working_days / 365

                gratuity_duration_id = False
                if each.employee_id.country_id.code == 'QA':
                    nationality = 'QA'
                else:
                    nationality = 'expatriate'
                hr_accounting_configuration_id = self.env[
                    'hr.gratuity.accounting.configuration'].search(
                    [('active', '=', True), ('config_contract_type', '=', each.employee_contract_type),
                     ('employment_category', '=', each.employee_id.wassef_employee_type),
                     ('nationality', '=', nationality),
                     '|', ('gratuity_end_date', '>=', date.today()), ('gratuity_end_date', '=', False),
                     '|', ('gratuity_start_date', '<=', date.today()), ('gratuity_start_date', '=', False)])
                if len(hr_accounting_configuration_id) > 1:
                    raise UserError(_(
                        "There is a date conflict in Gratuity accounting configuration. "
                        "Please remove the conflict and try again!"))
                elif not hr_accounting_configuration_id:
                    raise UserError(
                        _('No gratuity accounting configuration found '
                          'or please set proper start date and end date for gratuity configuration!'))
                # find configuration ids related to the gratuity accounting configuration
                # each.employee_gratuity_configuration = hr_accounting_configuration_id.id
                conf_ids = hr_accounting_configuration_id.gratuity_configuration_table.mapped('id')
                hr_duration_config_ids = self.env['gratuity.configuration'].browse(conf_ids)
                for duration in hr_duration_config_ids:
                    if duration.from_year and duration.to_year and duration.from_year <= each.total_working_years <= duration.to_year:
                        gratuity_duration_id = duration
                        break

                    elif duration.from_year and not duration.to_year and duration.from_year <= each.total_working_years:
                        gratuity_duration_id = duration
                        break
                    elif duration.to_year and not duration.from_year and each.total_working_years <= duration.to_year:
                        gratuity_duration_id = duration
                        break
                if gratuity_duration_id:
                    each.employee_gratuity_duration = gratuity_duration_id.id
                else:
                    raise Warning(_('No suitable gratuity durations found !'))
                # show warning when the employee's working years is less than
                # one year or no running employee found.
                # if each.total_working_years < 1 and each.employee_id.id:
                #     raise Warning(_('Selected Employee is not eligible for Gratuity Settlement'))
                # each.hr_gratuity_journal = hr_accounting_configuration_id.gratuity_journal.id
                # each.hr_gratuity_credit_account = hr_accounting_configuration_id.gratuity_credit_account.id
                # each.hr_gratuity_debit_account = hr_accounting_configuration_id.gratuity_debit_account.id
                # if each.employee_gratuity_duration and each.wage_type == 'hourly':
                #     if each.employee_gratuity_duration.employee_working_days != 0:
                #         if each.employee_id.resource_calendar_id and each.employee_id.resource_calendar_id.hours_per_day:
                #             daily_wage = each.employee_basic_salary * each.employee_id.resource_calendar_id.hours_per_day
                #         else:
                #             daily_wage = each.employee_basic_salary * 8
                #         working_days_salary = daily_wage * each.employee_gratuity_duration.employee_working_days
                #         gratuity_pay_per_year = working_days_salary * each.employee_gratuity_duration.percentage
                #         employee_gratuity_amount = gratuity_pay_per_year * each.employee_gratuity_years
                #         each.employee_gratuity_amount = round(employee_gratuity_amount, 2)
                #     else:
                #         raise Warning(_("Employee working days is not configured in "
                #                         "the gratuity configuration..!"))
                if each.employee_gratuity_duration and each.wage_type == 'monthly':
                    if each.employee_gratuity_duration.employee_daily_wage_days != 0:
                        # daily_wage = each.employee_basic_salary / each.employee_gratuity_duration.employee_daily_wage_days
                        # working_days_salary = daily_wage * each.employee_gratuity_duration.employee_working_days
                        # gratuity_pay_per_year = working_days_salary * each.employee_gratuity_duration.percentage
                        # each.salary_rate = gratuity_pay_per_year
                        each.salary_rate = ((each.employee_basic_salary /
                                             each.employee_gratuity_duration.employee_daily_wage_days) *
                                            each.employee_gratuity_duration.employee_working_days) * \
                                           each.employee_gratuity_duration.percentage
                        each.employee_gratuity_amount = round(each.salary_rate * each.employee_gratuity_years, 2)
                        each.total_amount_working_days_no_store = each.employee_gratuity_years * each.salary_rate
                    else:
                        raise Warning(_("Employee wage days is not configured in "
                                        "the gratuity configuration..!"))
                leave_balance = (gross_salary / 30) * leave_balance_days
                deductions = allowance_amount + each.total_amount_deduction
                if each.is_notice_period:
                    # each.total_notice_pay = gross_salary * float(each.notice_period)
                    each.employee_gratuity_amount = each.employee_gratuity_amount - deductions + leave_balance + \
                                                    each.total_notice_pay
                else:
                    each.employee_gratuity_amount = each.employee_gratuity_amount - deductions + leave_balance
                if each.total_working_years < 1:
                    each.total_amount_working_days_no_store = 0
                # each.total_amount_working_days_no_store = each.total_working_years < 1 and 0 or each.total_amount_working_days_no_store
                # each.gratuity_amount = each.employee_gratuity_years * ((each.employee_basic_salary/30)*21)

    def get_url(self):
        self.ensure_one()
        get_url = str(self.env['ir.config_parameter'].sudo().search(
            [('key', '=', 'web.base.url')]).value) + '/web?#id=' + str(
            self.id) + '&view_type=form&model=hr.gratuity&action=' + str(
            self.env.ref('hr_gratuity_settlement.action_employee_gratuity').id) + ' & menu_id = '
        return get_url

    # Changing state to submit
    def submit_request(self):
        first_approve_users = self.env.ref('hr_gratuity_settlement.group_gratuity_first_approval').users
        for rec in self:
            rec.write({'state': 'submit'})
            if self.state == 'submit':
                self.send_notification_of_loan_request(first_approve_users)
                self.update_activity(first_approve_users)
            return True

    def first_approve_request(self):
        self.write({'state': 'first_approve'})
        if self.state == 'first_approve':
            second_approve_users = self.env.ref('hr_gratuity_settlement.group_gratuity_second_approval').users
            self.send_notification_of_loan_request(second_approve_users)
            self.update_activity(second_approve_users)

    def send_notification_of_loan_request(self, users):
        template = self.env.ref('hr_gratuity_settlement.mail_template_send_notification_of_gratuity_settlement_request',
                                raise_if_not_found=False)
        if users and template:
            partner_to = [str(user.partner_id.id) for user in users if users]
            if partner_to:
                user_tz = self.env.user.partner_id.tz or 'Africa/Nairobi'
                create_date = timezone('UTC').localize(self.create_date).astimezone(timezone(user_tz))
                gratuity_settlement_state = 'First Approval' if self.state == 'submit' else 'Second Approval'
                template.sudo().with_context(
                    partner_to=','.join(partner_to), create_date=create_date,
                    loan_approval_state=gratuity_settlement_state).send_mail(self.id, force_send=True)

    def update_activity(self, users):
        activity_to_do = self.env.ref('hr_gratuity_settlement.mail_act_gratuity_approval').id
        model_id = self.env['ir.model']._get('hr.gratuity').id
        activity = self.env['mail.activity']
        if self.state in ['submit', 'first_approve']:
            for user in users:
                if user:
                    act_dct = {
                        'activity_type_id': activity_to_do,
                        'note': "kindly check this Gratuity Settlement Request, it's awaiting your approval",
                        'user_id': user.id,
                        'res_id': self.id,
                        'res_model_id': model_id,
                        'date_deadline': datetime.today().date()
                    }
                    activity.sudo().create(act_dct)
        elif self.state == 'approve':
            activity_id = self.env['mail.activity'].search(
                [('res_id', '=', self.id), ('user_id', 'in', users.ids),
                 ('activity_type_id', '=', activity_to_do)])
            activity_id.action_feedback(feedback='Approve')
            other_activity_ids = self.env['mail.activity'].search(
                [('res_id', '=', self.id),
                 ('activity_type_id', '=', activity_to_do)])
            other_activity_ids.unlink()

    # Canceling the gratuity request
    def cancel_request(self):
        self.write({'state': 'cancel'})

    # Set the canceled request to draft
    def set_to_draft(self):
        self.write({'state': 'draft'})

    # function for creating the account move with gratuity amount and
    # account credentials
    def approved_request(self):
        # for hr_gratuity_id in self:
        # debit_vals = {
        #     'name': hr_gratuity_id.employee_id.name,
        #     # 'account_id': hr_gratuity_id.hr_gratuity_debit_account.id,
        #     'partner_id': hr_gratuity_id.employee_id.address_home_id.id or False,
        #     # 'journal_id': hr_gratuity_id.hr_gratuity_journal.id,
        #     'date': date.today(),
        #     'debit': hr_gratuity_id.employee_gratuity_amount > 0.0 and hr_gratuity_id.employee_gratuity_amount or 0.0,
        #     'credit': hr_gratuity_id.employee_gratuity_amount < 0.0 and -hr_gratuity_id.employee_gratuity_amount or 0.0,
        # }
        # credit_vals = {
        #     'name': hr_gratuity_id.employee_id.name,
        #     # 'account_id': hr_gratuity_id.hr_gratuity_credit_account.id,
        #     'partner_id': hr_gratuity_id.employee_id.address_home_id.id or False,
        #     # 'journal_id': hr_gratuity_id.hr_gratuity_journal.id,
        #     'date': date.today(),
        #     'debit': hr_gratuity_id.employee_gratuity_amount < 0.0 and -hr_gratuity_id.employee_gratuity_amount or 0.0,
        #     'credit': hr_gratuity_id.employee_gratuity_amount > 0.0 and hr_gratuity_id.employee_gratuity_amount or 0.0,
        # }
        # vals = {
        #     'name': hr_gratuity_id.name + " - " + 'Gratuity for' + ' ' + hr_gratuity_id.employee_id.name,
        #     'narration': hr_gratuity_id.employee_id.name,
        #     'ref': hr_gratuity_id.name,
        #     'partner_id': hr_gratuity_id.employee_id.address_home_id.id or False,
        #     # 'journal_id': hr_gratuity_id.hr_gratuity_journal.id,
        #     'date': date.today(),
        #     'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)],
        # }
        # move = hr_gratuity_id.env['account.move'].create(vals)
        # move.post()
        self.write({'state': 'approve'})
        second_approve_users = self.env.ref('hr_gratuity_settlement.group_gratuity_second_approval').users
        first_approve_users = self.env.ref('hr_gratuity_settlement.group_gratuity_first_approval').users
        if second_approve_users and first_approve_users:
            second_approve_users += first_approve_users
        self.update_activity(second_approve_users)
        # emp_loans = self.env['hr.loan'].sudo().search([('employee_id', '=', self.employee_id.id), ('state', '=', 'paid')])
        # for loan in emp_loans:
        #     loan.action_loan_settle()

        # eosb allowance
        # eosb_allowance = self.env['allowance.request'].search([('employee_id', '=', self.employee_id.id),
        #                                                                ('allowance_type.code', '=', 'eosb'),
        #                                                                ('state', 'in', ['approved', 'paid'])])
        # for rec in eosb_allowance:
        #     rec.eligible_amount = 0.0

        # # furniture allowance
        # furniture_allowance = self.env['allowance.request'].search([('employee_id', '=', self.employee_id.id),
        #                                                                ('allowance_type.code', '=', 'furniture'),
        #                                                                ('state', '=', 'approved')])
        # print("********furniture_allowance********", furniture_allowance)
        # for rec in furniture_allowance:
        #     rec.sudo().action_cancel()
        #
        # # ticket allowance
        # ticket_allowance = self.env['allowance.request'].search([('employee_id', '=', self.employee_id.id),
        #                                                             ('allowance_type.code', '=', 'furniture'),
        #                                                             ('state', '=', 'approved')])
        # print("********ticket_allowance********", ticket_allowance)
        # for rec in ticket_allowance:
        #     rec.sudo().action_cancel()

    @api.model
    def action_generate_gratuity_report(self):
        rec = self.filtered(lambda x: x.state == 'approve')
        if rec:
            data = {
                'records': rec.ids,
            }
            return self.env.ref('hr_gratuity_settlement.action_gratuity_xlsx_report').report_action(self, data=data)
        else:
            raise UserError(_('Please, select records approved records.'))

    def action_paid(self):
        for rec in self:
            rec.write({
                'state': 'paid'
            })

    def print(self):
        if platform == "linux" or platform == "linux2":
            return self.env.ref('hr_gratuity_settlement.action_report_final_settlement').report_action(self)
        elif platform == "win32":
            return self.env.ref('hr_gratuity_settlement.action_report_final_settlement_windows').report_action(self)

    # Create Payslip
    def create_payslip(self):
        last_payslip = self.env['hr.payslip'].search([('employee_id', '=', self.employee_id.id)], limit=1)
        att_sheets = self.env['attendance.sheet'].search([('employee_id', '=', self.employee_id.id),
                                                          ('actual_date_to', '>', last_payslip.date_to)])
        for each_att_sheet in att_sheets:
            if self.employee_id.status in ['suspended', 'terminated', 'terminated_w_reason', 'resigned']:
                payslip = self.env['hr.payslip']
                # for att_sheet in each_att_sheet:
                if each_att_sheet.payslip_id:
                    new_payslip = each_att_sheet.payslip_id
                    continue
                # from_date = each_att_sheet.date_from
                # to_date = each_att_sheet.date_to
                employee = each_att_sheet.employee_id
                salary_rules = []
                res = {
                    'name': 'draft',
                    'contract_id': employee.contract_id.id,
                    'employee_id': employee.id,
                    'gratuity_id': self.id,
                    'has_gratuity': True,
                    'date_from': each_att_sheet.actual_date_from,
                    'date_to': each_att_sheet.actual_date_to,
                    'actual_day_from': each_att_sheet.actual_date_from,
                    'actual_day_to': each_att_sheet.actual_date_to,
                    'remarks': each_att_sheet.note,
                }
                if each_att_sheet.batch_id and each_att_sheet.batch_id.payslip_batch_id:
                    res['payslip_run_id'] = each_att_sheet.batch_id.payslip_batch_id.id
                new_payslip = payslip.create(res)
                # add Accommodation Allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'ACCOMM')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.accommodation_allowance
                })
                # add Transport Allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'TRA')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.transportation_allowance
                })
                # add Food Allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'FOOD')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.food_allowance
                })
                # add site Allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'Site')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.site_allowance
                })
                # add mobile Allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'MOBILE')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.mobile_allowance
                })
                # add other Allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'OTHER')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.other_allowance
                })
                # add ticket Allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'TICKET')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.ticket_allowance
                })
                # # add overtime Allowance
                # acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'OVERTIME')], limit=1)
                #
                # self.env['hr.payslip.input'].create({
                #     'code': acc_input_type.code,
                #     'contract_id': self.contract_id.id,
                #     'input_type_id': acc_input_type.id,
                #     'payslip_id': new_payslip.id,
                #     'sequence': 1,
                #     'amount': self.contract_id.accommodation
                # })
                # add Laundry Allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LAUNDRY')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.laundry_allowance
                })
                # add Earning Settlement Allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'EARNING')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.earning_allowance
                })
                # add overtime Allowance
                # acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'OVERTIME')], limit=1)
                # salary_rules.append({
                #     'code': acc_input_type.code,
                #     'contract_id': self.contract_id.id,
                #     'input_type_id': acc_input_type.id,
                #     'payslip_id': new_payslip.id,
                #     'sequence': 1,
                #     'amount': self.overtime_allowance
                # })
                # add Social Allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'SOCIAL')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.social_allowance
                })
                # # add leave advance Allowance
                # acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LEAVE')], limit=1)
                # salary_rules.append({
                #     'code': acc_input_type.code,
                #     'contract_id': self.contract_id.id,
                #     'input_type_id': acc_input_type.id,
                #     'payslip_id': new_payslip.id,
                #     'sequence': 1,
                #     'amount': self.leave_allowance
                # })
                # # add special Allowance
                # acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'sp')], limit=1)
                #
                # self.env['hr.payslip.input'].create({
                #     'code': acc_input_type.code,
                #     'contract_id': self.contract_id.id,
                #     'input_type_id': acc_input_type.id,
                #     'payslip_id': new_payslip.id,
                #     'sequence': 1,
                #     'amount': self.special_allowance
                # })
                # add furniture Allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'FURNITURE')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.furniture_allowance
                })
                # add fixed over time Allowance
                # acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'FOT')], limit=1)
                #
                # self.env['hr.payslip.input'].create({
                #     'code': acc_input_type.code,
                #     'contract_id': self.contract_id.id,
                #     'input_type_id': acc_input_type.id,
                #     'payslip_id': new_payslip.id,
                #     'sequence': 1,
                #     'amount': self.fixed_overtime_allowance
                # })
                # add leave basic salary allowance to
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LADW')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.leave_advance_wage
                })
                # add leave accommodation allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LADACM')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.leave_advance_accommodation
                })
                # add leave mobile allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LADMO')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.leave_advance_mobile_allowance
                })
                # add leave food allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LADFDW')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.leave_advance_food_allowance
                })
                # add leave site allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LADSTW')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.leave_advance_site_allowance
                })
                # add leave transportation allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LADTRW')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.leave_advance_transport_allowance
                })
                # add leave other allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LADOTHW')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.leave_advance_other_allowance
                })
                # add leave uniform allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LADUNIFORM')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.leave_advance_uniform_allowance
                })
                # add leave social allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LADSOC')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.leave_advance_social_allowance
                })
                # add leave wage deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LADWD')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.leave_advance_wage_ded
                })
                # add leave accommodation deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LADACMD')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.leave_advance_accommodation_ded
                })
                # add leave mobile deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LADMOD')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.leave_advance_mobile_ded
                })
                # add leave food deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LADFDWD')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.leave_advance_food_ded
                })
                # add leave site deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LADSTWD')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.leave_advance_site_ded
                })
                # add leave transportation deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LADTRWD')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -
                    each_att_sheet.leave_advance_transport_ded
                })
                # add leave other deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LADOTHWD')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.leave_advance_other_ded
                })
                # add leave uniform deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LADUNID')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.leave_advance_uniform_ded
                })
                # add leave social deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LADSOCD')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.leave_advance_social_ded
                })
                # add Basic Deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'BASICDED')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.basic_deduction
                })
                # add Other Deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'OTHERDED')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.other_deduction
                })
                # add Staff Hotel Deduction
                # acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'STAFFHOTELDED')], limit=1)
                # salary_rules.append({
                #     'code': acc_input_type.code,
                #     'contract_id': self.contract_id.id,
                #     'input_type_id': acc_input_type.id,
                #     'payslip_id': new_payslip.id,
                #     'sequence': 1,
                #     'amount': -self.staff_hotel_deduction
                # })
                # add Transport Deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'TRANSDED')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.transportation_deduction
                })
                # add Accommodation Deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'ACCOMMDED')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.accommodation_deduction
                })
                # add Mobile Deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'MOBILEDED')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.mobile_deduction
                })
                # add Laundry Deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'UNIFORMDED')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.uniform_deduction
                })
                # add Social Deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'SOCIALDED')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.social_deduction
                })
                # add Site Deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'SITEDED')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.site_deduction
                })
                # add overtime Deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'OVERTDED')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.overtime_deduction
                })
                # add Deduction Settlement
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'SETTLEDED')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.deduction_settlements
                })
                # add Loan Deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LO')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.loan_deduction
                })
                # add Car Loan Deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LOANDED')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.car_loan_deduction
                })
                # add Marriage Loan Deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'MARLOANDED')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.marriage_loan_deduction
                })
                # add Leave Advance Payment Deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LAP')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.advance_leave_count_days
                })
                # add Employee Pension
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'PE')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.pension_employee
                })
                # add Employer Pension
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'PER')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.pension_employer
                })
                self.env['hr.payslip.input'].create(salary_rules)
                new_payslip.compute_sheet()
                self.attendance_sheets = [(4, each_att_sheet.id)]



class EmployeeContractWage(models.Model):
    _inherit = 'hr.contract'

    # structure_type_id = fields.Many2one('hr.payroll.structure.type', string="Salary Structure Type")
    company_country_id = fields.Many2one('res.country', string="Company country", related='company_id.country_id',
                                         readonly=True)
    wage_type = fields.Selection([('monthly', 'Monthly Fixed Wage'), ('hourly', 'Hourly Wage')])
    hourly_wage = fields.Monetary('Hourly Wage', digits=(16, 2), default=0, required=True,
                                  help="Employee's hourly gross wage.")
