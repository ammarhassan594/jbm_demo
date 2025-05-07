from odoo import fields, models, api, _
from odoo.tools.date_utils import add, get_month, end_of, start_of
from odoo.exceptions import ValidationError
from datetime import datetime, date, timedelta
import json
from dateutil import relativedelta

from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT, format_date

GCC_COUNTRIES_CODES = ['BH', 'OM', 'AE', 'KW', 'SA']


class EmployeePromotion(models.Model):
    _name = 'employee.promotion'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    _description = 'Employee Promotion'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submit'),
        ('confirm', 'Confirm'),
        ('hr_approve', 'Approved'),
        ('approve', 'Approved By HR')
    ], string='Status', readonly=True, tracking=True, copy=False, default='draft')
    promoted = fields.Boolean(string="Promoted", default=False)
    exceptional_promotion = fields.Boolean(string="Exceptional Promotion")
    promotion_rule_id = fields.Many2one('promotion.rules', string="Promotion Rule")
    payscale_scheduled_raise_id = fields.Many2one('payscale.scheduled.raise', string="Payscale Scheduled Raise")
    arabic_name = fields.Char(string="Arabic Name",
                              related="employee_id.arabic_name")
    english_name = fields.Char(string="English Name",
                               related="employee_id.name")

    def action_remove_employee_promotion(self):
        for record in self.browse(self.env.context['active_ids']):
            if record.new_contract_id and record.contract_id:
                if record.new_contract_id and record.new_contract_id.state == 'open':
                    record.new_contract_id.write({
                        'state': 'draft'
                    })
                    record.new_contract_id.unlink()
                if record.contract_id and record.contract_id.state == 'close':
                    record.contract_id.write({
                        'state': 'open'
                    })
                    record.contract_id.onchange_contract_validity()
            record.write({
                'state': 'draft'
            })
            record.unlink()


    def action_submit(self):
        # check values of payroll_group or payscale
        # print('wage_new', self.wage_new, self.new_payscale_id.basic_from)
        # if self.wage_new < self.new_payscale_id.basic_from or self.wage_new > \
        #         self.new_payscale_id.basic_to:
        #     raise ValidationError(_("Basic Wage: should be in between %s and %s") %
        #                           (self.new_payscale_id.basic_from,
        #                            self.new_payscale_id.basic_to))

        self.state = 'submit'

    def action_confirm(self):
        self.state = 'confirm'

    def action_draft(self):
        self.state = 'draft'

    def action_approve_by_hr(self):
        self.state = 'hr_approve'
        users = []
        activity_to_do = self.env.ref('employee_promotion.mail_act_employee_promotion').id
        model_id = self.env['ir.model']._get('employee.promotion').id
        activity = self.env['mail.activity']
        users += self.env.ref('employee_promotion.group_promotion_manager').users
        # users += self.env.ref('hr.group_hr_user').users
        for user in users:
            if user:
                act_dct = {
                    'activity_type_id': activity_to_do,
                    'note': "للتكرم بمراجعة طلب ترقية الموظف على نظام موارد.",
                    'user_id': user.id,
                    'res_id': self.id,
                    'res_model_id': model_id,
                    'date_deadline': datetime.today().date()
                }
                activity.sudo().create(act_dct)

    def action_approve(self):
        # create new contract for permanent in house employee
        # self.create_additional_elements()
        # 5/0
        contract = self.env["hr.contract"].search([
            ('employee_id', '=', self.employee_id.id)
            , ('state', '=', 'open')], limit=1, order="id DESC")
        self.contract_id = self.employee_id.contract_id.id if self.employee_id.contract_id.state == 'open' else contract.id
        # get yesterday of start_date to run cron job
        yesterday = self.date_start + timedelta(days=-1)
        self.contract_id.sudo().write({
            'date_end': yesterday.strftime(DEFAULT_SERVER_DATE_FORMAT),
            'kanban_state': 'blocked',
        })
        # self.contract_id.date_end = yesterday
        # self.contract_id.sudo().kanban_state = 'blocked'

        resource_calendar = self.employee_id.contract_id.resource_calendar_id
        vals = {
            'name': f'New Contract for {self.employee_id.name}',
            'employee_id': self.employee_id.id,
            'department_id': self.department_id.id,
            # 'job_id': self.job_id.id,
            'state': 'draft',
            'wage': self.wage_new,
            'resource_calendar_id': resource_calendar.id
            if resource_calendar else None
        }

        vals.update({
            'social_alw': self.social_alw_new,
            'transport_alw': self.transport_allowance_new,
            'housing_alw': self.housing_new,
            'other_alw': self.other_allowance_new,
            'mobile_alw': self.mobile_allowance_new,
            'car_alw': self.car_alw_new,
            'car_loan': self.car_loan,
            'marriage_loan': self.marriage_loan_for_permanent_staff_new,
            'air_ticket_alw': self.air_ticket_alw_new,
            'furniture_alw': self.furniture_allowance,
            'education_alw': self.education_allowance,
            'supervision_alw': self.supervision_alw_new,
            'mobilisation_alw': self.mobilisation_allowance,
            'business_alw': self.business_allowance,
            'gross': self.gross_salary_new,
            'airport_id': self.contract_id.airport_id.id,
            'job_id': self.new_job_id.id if self.new_job_id else self.job_id.id,
            'date_start': self.date_start.strftime(DEFAULT_SERVER_DATE_FORMAT)
        })
        self.new_contract_id = self.env['hr.contract'].create(vals).id
        self.new_contract_id.write({'date_start': self.date_start.strftime(DEFAULT_SERVER_DATE_FORMAT)})
        self.new_contract_id.payscale_id = self.new_payscale_id.id
        self.new_contract_id.leave_type = self.new_payscale_id.leave_type_ids
        # self.allocate_annual_leave()
        # get yesterday of start_date to run cron job
        # yesterday = self.date_start + timedelta(days=-1)

        # current contract has end date and kanban_state is blocked
        # next contract has end start date and kanban_state is done
        # must apply these steps with this sequence to granulate a cron job run efficiency
        # self.contract_id.date_end = yesterday
        # self.contract_id.sudo().kanban_state = 'blocked'
        wage = 0
        extra_amount = 0
        if self.promotion_rule_id:
            if self.wage_old < self.new_payscale_id.basic_from:
                wage += self.new_payscale_id.basic_from
            else:
                wage += self.wage_old
                extra_amount += self.promotion_rule_id.extra_amount
        else:
            wage += self.new_payscale_id.basic_from
        self.new_contract_id.sudo().write(
            {'kanban_state': 'done',
             'contract_validity': self.contract_id.contract_validity,
             'date_end': self.new_contract_id.date_start + relativedelta.relativedelta(
                 years=int(self.contract_id.contract_validity)),
             'extra_amount': extra_amount,
             'wage': wage})
        self.write({'wage_new': wage})
        # self.new_contract_id.date_start = self.date_start
        # self.new_contract_id.sudo().kanban_state = 'done'

        if self.is_expired_contract:
            # cancel old contract run new contract
            self.update_employee_profile()
        users = []
        ctx = {}
        mail_template = self.env.ref('employee_promotion.update_contract_email_template')
        users += self.env.ref('hr_payroll.group_hr_payroll_manager').users
        users += self.env.ref('hr_payroll.group_hr_payroll_user').users
        ctx['email_from'] = self.env.user.partner_id.email or self.env.user.email or False
        ctx['email_to'] = ','.join([user.email for user in users if user.email])
        ctx['name'] = self.employee_id.name if self.employee_id else ''
        ctx[
            'old_contract'] = self.contract_id.payscale_id.name if self.contract_id and self.contract_id.payscale_id else ''
        ctx['old_contract_id'] = self.contract_id.id if self.contract_id else False
        ctx[
            'new_contract'] = self.new_contract_id.payscale_id.name if self.new_contract_id and self.new_contract_id.payscale_id else ''
        ctx['new_contract_id'] = self.new_contract_id.id if self.new_contract_id else False
        # template = mail_template.sudo().with_context(ctx)
        # template.send_mail(self.id, force_send=True)

        self.state = 'approve'
        activity_to_do = self.env.ref('employee_promotion.mail_act_employee_promotion').id
        activity_users = self.env.ref('employee_promotion.group_promotion_manager').users
        activity_id = self.env['mail.activity'].search(
            [('res_id', '=', self.id), ('user_id', 'in', activity_users.ids),
             ('activity_type_id', '=', activity_to_do)])
        activity_id.action_feedback(feedback='Approved')
        other_activity_ids = self.env['mail.activity'].search(
            [('res_id', '=', self.id),
             ('activity_type_id', '=', activity_to_do)])
        other_activity_ids.unlink()
        self._get_payscale_grade_values()

    def update_employee_profile(self):
        for rec in self:
            res = {}
            old_contract = rec.contract_status_old
            new_contract = rec.contract_status_new
            if old_contract and new_contract and old_contract != new_contract:
                res.update({'contract_status': new_contract})
                res.update({'payscale_id': rec.new_payscale_id.id})
                # rec.employee_id.with_context(updated_from_promotion=True).create_employee_event(rec.date_start, res)
            rec.contract_id.state = 'close'
            rec.new_contract_id.state = 'open'

    def get_url(self):
        self.ensure_one()
        if self.contract_id:
            get_url = str(self.env['ir.config_parameter'].sudo().search(
                [('key', '=', 'web.base.url')]).value) + '/web?#id=' + str(
                self.contract_id.id) + '&view_type=form&model=hr.contract&action=' + str(
                self.env.ref('hr_payroll.action_hr_contract_repository').id) + ' & menu_id = '
            return get_url

    def get_new_url(self):
        self.ensure_one()
        if self.new_contract_id:
            get_url = str(self.env['ir.config_parameter'].sudo().search(
                [('key', '=', 'web.base.url')]).value) + '/web?#id=' + str(
                self.new_contract_id.id) + '&view_type=form&model=hr.contract&action=' + str(
                self.env.ref('hr_payroll.action_hr_contract_repository').id) + ' & menu_id = '
            return get_url

    name = fields.Char(string='Promotion Name', required=True, copy=False, readonly=True, index=True,
                       default=lambda self: _('New'))

    # def get_employee_calendar(self):
    #     calender_id = self.env['resource.calendar']
    #     if self.employee_id.wassef_employee_type == 'perm_staff':
    #         calender_id = self.env['resource.calendar'].sudo().search([('default_work_calendar', '=', 'staff')],
    #                                                                   limit=1)
    #     elif self.employee_id.wassef_employee_type == 'perm_in_house':
    #         calender_id = self.env['resource.calendar'].sudo().search([('default_work_calendar', '=', 'in_house')],
    #                                                                   limit=1)
    #     elif self.employee_id.wassef_employee_type == 'temp':
    #         calender_id = self.env['resource.calendar'].sudo().search([('default_work_calendar', '=', 'temp')],
    #                                                                   limit=1)
    #     return calender_id

    def _default_employee(self):
        return self.env.context.get('default_employee_id') or self.env.user.employee_id

    def _default_company(self):
        return self.env.context.get('default_company_id') or self.env.user.company_id

    employee_id = fields.Many2one('hr.employee', tracking=True, string="Employee")
    contract_status_old = fields.Selection(selection=[
        ('single', 'Single'),
        ('married', 'Married')
    ],
        string="Current Contract Status")
    contract_status_new = fields.Selection(selection=[
        ('single', 'Single'),
        ('married', 'Married')
    ], string="Contract Status New")
    employee_number = fields.Char(related="employee_id.registration_number", string="Employee Number", readonly=True)
    company_id = fields.Many2one('res.company', string='Company', default=_default_company)
    description = fields.Text("Description")
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env['res.currency'].search(['|', ('name', '=', 'QAR'),
                                                              ('symbol', '=', 'QR')]).id,
        domain=['|', ('name', '=', 'QAR'), ('symbol', '=', 'QR')])
    is_expired_contract = fields.Boolean('Expired Old Contract', compute="_check_old_contract")
    adjustments = fields.Monetary('Adjustments')
    date_start = fields.Date('Effective Date',
                             default=lambda self: get_month(add(start_of(fields.Date.today(), 'month'), months=1))[0],
                             required=True, states={'approve': [('readonly', True)]})

    @api.depends('date_start')
    def _check_old_contract(self):
        for rec in self:
            if rec.date_start and rec.date_start < fields.Date.today():
                rec.is_expired_contract = True
            else:
                rec.is_expired_contract = False

    number_of_months_differance = fields.Integer("Number Of Difference Months",
                                                 compute="_get_number_of_differance_months")

    @api.depends('date_start')
    def _get_number_of_differance_months(self):
        today = fields.Date.today()
        for rec in self:
            if rec.date_start and today and rec.date_start < today:
                if rec.date_start.year == today.year:
                    rec.number_of_months_differance = (today.month - rec.date_start.month) \
                        if today.month > rec.date_start.month else 1
                else:
                    rec.number_of_months_differance = (today - rec.date_start).days // 30
            else:
                rec.number_of_months_differance = 1

    # related fields of employee
    manager_id = fields.Many2one("hr.employee", related="employee_id.parent_id", string="Manager")
    manager_user_id = fields.Many2one("res.users", compute="_get_employee_manager_user", store=True)
    department_id = fields.Many2one("hr.department", related="employee_id.department_id", string='Department')
    job_id = fields.Many2one("hr.job", related="employee_id.job_id", string='Job Position')
    registration_number = fields.Char(related="employee_id.registration_number", string="Employee Code")
    contract_id = fields.Many2one('hr.contract', string="Old Contract", store=True, readonly=True)
    new_contract_id = fields.Many2one('hr.contract', string="New Contract", readonly=True)
    payment_date = fields.Date(string="Payment Date")
    air_ticket_alw_old = fields.Selection(related="contract_id.air_ticket_alw")
    air_ticket_alw_new = fields.Selection(string="Annual Air Ticket Allowance ",
                                          selection=[('b', 'Business'), ('e', 'Economy')], )

    line_manager_id = fields.Many2one("hr.employee", related="employee_id.line_manager_id", string="Line 2 Manager")
    new_job_id = fields.Many2one("hr.job", string='New Job Position')

    @api.depends('employee_id')
    def _get_employee_manager_user(self):
        for rec in self:
            if rec.employee_id and rec.employee_id.parent_id.user_id:
                rec.manager_user_id = rec.employee_id.parent_id.user_id.id
            elif rec.employee_id and rec.employee_id.line_manager_id.user_id:
                rec.manager_user_id = rec.employee_id.line_manager_id.user_id.id
            else:
                rec.manager_user_id = None

    @api.onchange('contract_status_new')
    def _onchange_contract_status_new(self):
        for rec in self:
            if any((rec.contract_status_new, not rec.contract_status_new)):
                self.new_payscale_id = None

    wage_old = fields.Monetary(related="contract_id.wage")
    wage_new = fields.Monetary('Basic Salary', states={'submit': [('readonly', True)],
                                                       'confirm': [('readonly', True)],
                                                       'approve': [('readonly', True)]},
                               help="Employee's monthly gross wage.")
    wage_difference = fields.Monetary('Wage Difference', compute="_compute_wage_payroll_group_difference")

    @api.depends('wage_new', 'wage_old')
    def _compute_wage_payroll_group_difference(self):
        for rec in self:
            if rec.wage_new or rec.wage_old:
                rec.wage_difference = rec.wage_new - rec.wage_old
            else:
                rec.wage_difference = 0.0

    housing_old = fields.Monetary(related='contract_id.housing_alw')
    housing_new = fields.Monetary('Housing', states={'submit': [('readonly', True)],
                                                     'confirm': [('readonly', True)],
                                                     'approve': [('readonly', True)]},
                                  help="Employee's Housing.")

    housing_difference = fields.Monetary('Housing Difference',
                                         compute="_compute_accommodation_payroll_group_difference")

    @api.depends('housing_new', 'housing_old')
    def _compute_accommodation_payroll_group_difference(self):
        for rec in self:
            if rec.housing_new or rec.housing_old:
                rec.housing_difference = (rec.housing_new - rec.housing_old) if \
                    rec.housing_new > rec.housing_old else (rec.housing_old - rec.housing_new)
            else:
                rec.housing_difference = 0.0

    mobile_allowance_old = fields.Monetary(related='contract_id.mobile_alw', string='Mobile Allowance')
    mobile_allowance_new = fields.Monetary('Mobile Allowance', states={'submit': [('readonly', True)],
                                                                       'confirm': [('readonly', True)],
                                                                       'approve': [('readonly', True)]})
    mobile_allowance_difference = fields.Monetary('Mobile Allowance Difference',
                                                  compute="_compute_mobile_allowance_payroll_difference")

    @api.depends('mobile_allowance_new', 'mobile_allowance_old')
    def _compute_mobile_allowance_payroll_difference(self):
        for rec in self:
            if rec.mobile_allowance_new or rec.mobile_allowance_old:
                rec.mobile_allowance_difference = (rec.mobile_allowance_new - rec.mobile_allowance_old) if \
                    rec.mobile_allowance_new > rec.mobile_allowance_old else (
                        rec.mobile_allowance_old - rec.mobile_allowance_new)
            else:
                rec.mobile_allowance_difference = 0.0

    ticket_allowance_diff = fields.Monetary('Ticket Allowance Difference',
                                            compute="_compute_ticket_allowance_payroll_difference")

    def _get_working_days(self, start_date, end_date):
        if start_date and end_date:
            # get list of all days

            all_days = (start_date + timedelta(x) for x in range((end_date - start_date).days + 1))

            # filter business days
            # weekday from 0 to 4. 0 is monday adn 4 is friday
            # increase counter in each iteration if it is a weekday

            count = sum(1 for day in all_days if day.weekday() in [0, 1, 2, 3, 6])
            return count

    @api.depends('wage_difference')
    def _compute_ticket_allowance_payroll_difference(self):
        for rec in self:
            ticket_diff = 0
            if rec.employee_id.country_id and rec.employee_id.country_id.code == 'QA':
                last_date = date(rec.date_start.year, 12, 31)
                working_days = self._get_working_days(rec.date_start, last_date)
                amount = rec.wage_difference * working_days / 261
                if rec.date_start.month == 1 and rec.date_start.day == 1:
                    amount = rec.wage_difference
                if rec.employee_id.contract_status == 'married':
                    ticket_diff = amount * 2
                else:
                    ticket_diff = amount

            rec.ticket_allowance_diff = ticket_diff

    transport_allowance_old = fields.Monetary(related='contract_id.transport_alw', string='Transport Allowance')
    transport_allowance_new = fields.Monetary('Transport Allowance', states={'submit': [('readonly', True)],
                                                                             'confirm': [('readonly', True)],
                                                                             'approve': [('readonly', True)]})
    transport_allowance_difference = fields.Monetary('Transport Allowance Difference',
                                                     compute="_compute_transport_allowance_payroll_difference")

    @api.depends('transport_allowance_new')
    def _compute_transport_allowance_payroll_difference(self):
        for rec in self:
            if rec.transport_allowance_new or rec.transport_allowance_old:
                rec.transport_allowance_difference = (rec.transport_allowance_new - rec.transport_allowance_old) if \
                    rec.transport_allowance_new > rec.transport_allowance_old else (
                        rec.transport_allowance_old - rec.transport_allowance_new)
            else:
                rec.transport_allowance_difference = 0.0

    other_allowance_old = fields.Monetary(related="contract_id.other_alw", string='Other Allowance')
    other_allowance_new = fields.Monetary('Other Allowance', states={'submit': [('readonly', True)],
                                                                     'confirm': [('readonly', True)],
                                                                     'approve': [('readonly', True)]})

    other_allowance_difference = fields.Monetary('Other Allowance Difference',
                                                 compute="_compute_other_allowance_payroll_difference")

    @api.depends('other_allowance_new')
    def _compute_other_allowance_payroll_difference(self):
        for rec in self:
            if rec.other_allowance_new or rec.other_allowance_old:
                rec.other_allowance_difference = (rec.other_allowance_new - rec.other_allowance_old) if \
                    rec.other_allowance_new > rec.other_allowance_old else (
                        rec.other_allowance_old - rec.other_allowance_new)
            else:
                rec.other_allowance_difference = 0.0

    social_alw_old = fields.Monetary(related="contract_id.social_alw", string='Social Allowance')
    social_alw_new = fields.Monetary('Social Allowance', states={'submit': [('readonly', True)],
                                                                 'confirm': [('readonly', True)],
                                                                 'approve': [('readonly', True)]})

    social_alw_difference = fields.Monetary('Social Allowance Difference',
                                            compute="_compute_social_allowance_payroll_difference")

    @api.depends('social_alw_new')
    def _compute_social_allowance_payroll_difference(self):
        for rec in self:
            if rec.social_alw_old or rec.social_alw_new:
                rec.social_alw_difference = (rec.social_alw_new - rec.social_alw_old) if \
                    rec.social_alw_new > rec.social_alw_old else (
                        rec.social_alw_old - rec.social_alw_new)
            else:
                rec.social_alw_difference = 0.0

    car_alw_old = fields.Monetary(related="contract_id.car_alw", string='Car Allowance')
    car_alw_new = fields.Monetary('Car Allowance', states={'submit': [('readonly', True)],
                                                           'confirm': [('readonly', True)],
                                                           'approve': [('readonly', True)]})

    car_alw_difference = fields.Monetary('Car Allowance Difference',
                                         compute="_compute_car_allowance_payroll_difference")

    @api.depends('car_alw_new')
    def _compute_car_allowance_payroll_difference(self):
        for rec in self:
            if rec.car_alw_old or rec.car_alw_new:
                rec.car_alw_difference = (rec.car_alw_new - rec.car_alw_old) if \
                    rec.car_alw_new > rec.car_alw_old else (
                        rec.car_alw_old - rec.car_alw_new)
            else:
                rec.car_alw_difference = 0.0

    supervision_alw_old = fields.Monetary(related="contract_id.supervision_alw", string='Supervision Allowance')
    supervision_alw_new = fields.Monetary('Supervision Allowance', states={'submit': [('readonly', True)],
                                                                           'confirm': [('readonly', True)],
                                                                           'approve': [('readonly', True)]})

    supervision_alw_difference = fields.Monetary('Supervision Allowance Difference',
                                                 compute="_compute_supervision_allowance_payroll_difference")

    @api.depends('supervision_alw_new')
    def _compute_supervision_allowance_payroll_difference(self):
        for rec in self:
            if rec.supervision_alw_old or rec.supervision_alw_new:
                rec.supervision_alw_difference = (rec.supervision_alw_new - rec.supervision_alw_old) if \
                    rec.supervision_alw_new > rec.supervision_alw_old else (
                        rec.supervision_alw_old - rec.supervision_alw_new)
            else:
                rec.supervision_alw_difference = 0.0

    gross_salary_old = fields.Monetary(related="contract_id.gross")
    gross_salary_new = fields.Monetary('Gross Salary', compute='_compute_gross_salary',
                                       help="Employee's monthly gross wage.")

    total_salary_differance = fields.Monetary(string="Total Salary Difference",
                                              compute="_calc_total_salary_differance")

    @api.depends('wage_difference', 'housing_difference', 'transport_allowance_difference',
                 'mobile_allowance_difference', 'other_allowance_difference', 'supervision_alw_difference',
                 'car_alw_difference', 'social_alw_difference', 'number_of_months_differance')
    def _calc_total_salary_differance(self):
        for rec in self:
            if rec.is_expired_contract:
                rec.total_salary_differance = rec.wage_difference + rec.housing_difference + \
                                              rec.transport_allowance_difference + rec.mobile_allowance_difference + \
                                              rec.other_allowance_difference + rec.supervision_alw_difference + \
                                              rec.social_alw_difference + rec.car_alw_difference
                rec.total_salary_differance *= rec.number_of_months_differance
            else:
                rec.total_salary_differance = 0.0

    net_in_house_salary = fields.Monetary('Net Salary', compute="_calc_net_salary",
                                          store=True)

    @api.depends('adjustments', 'total_salary_differance')
    def _calc_net_salary(self):
        for rec in self:
            if rec.is_expired_contract and rec.adjustments and rec.total_salary_differance:
                rec.net_in_house_salary = rec.total_salary_differance - rec.adjustments
            else:
                rec.net_in_house_salary = rec.total_salary_differance

    @api.depends('wage_new', 'housing_new', 'transport_allowance_new', 'mobile_allowance_new', 'supervision_alw_new',
                 'car_alw_new', 'social_alw_new', 'other_allowance_new'
                 )
    def _compute_gross_salary(self):
        for record in self:
            record.gross_salary_new = record.wage_new \
                                      + record.transport_allowance_new \
                                      + record.housing_new \
                                      + record.car_alw_new \
                                      + record.mobile_allowance_new \
                                      + record.social_alw_new \
                                      + record.other_allowance_new \
                                      + record.supervision_alw_new

    ticket_type_alw_old = fields.Selection(related="contract_id.ticket_type_alw")

    ticket_type_alw_new = fields.Selection([
        ('ticket_ALW', 'Ticket Allowance'),
        ('onceayear', 'Company ticket once/year'),
        ('once2year', 'Company ticket once/2 years')
    ],
        string='Ticket Type',
        default='ticket_ALW', help="Select the ticket type", states={'submit': [('readonly', True)],
                                                                     'confirm': [('readonly', True)],
                                                                     'approve': [('readonly', True)]})

    ticket_allowance_old = fields.Monetary(related="contract_id.ticket_allowance")
    ticket_allowance_new = fields.Monetary(string='Ticket Allowance', compute='_compute_ticket_allowance')

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_("You can not delete a record which is not in draft state"))
        return super().unlink()

    def _compute_ticket_allowance(self):
        for rec in self:
            rec.ticket_allowance_new = 0.0

    adult_fare_old = fields.Monetary(related="contract_id.adult_fare")
    adult_fare_new = fields.Monetary(string='Adult Fare', compute='_get_fares_adult')

    def _get_fares_adult(self):
        for rec in self:
            rec.adult_fare_new = 0.0

    child_fare_old = fields.Monetary(related="contract_id.child_fare")
    child_fare_new = fields.Monetary(string='Child Fare', compute='_get_fares_child')

    def _get_fares_child(self):
        for rec in self:
            rec.child_fare_new = 0.0

    infant_fare_old = fields.Monetary(related="contract_id.infant_fare")
    infant_fare_new = fields.Monetary(string='Infant Fare', compute='_get_fares_infant')

    def _get_fares_infant(self):
        for rec in self:
            rec.infant_fare_new = 0.0

    number_of_children_allowed_old = fields.Integer(related="contract_id.number_of_children_allowed")
    number_of_children_allowed_new = fields.Integer(string="Number of allowed dependents",
                                                    states={'submit': [('readonly', True)],
                                                            'confirm': [('readonly', True)],
                                                            'approve': [('readonly', True)]}, default=0, required=False)

    old_payscale_id = fields.Many2one("employee.payscale", readonly=True)
    new_payscale_id = fields.Many2one(comodel_name="employee.payscale",
                                      string="New Pay Scale",
                                      tracking=True,
                                      states={'submit': [('readonly', True)],
                                              'confirm': [('readonly', True)],
                                              'approve': [('readonly', True)]}, required=False)

    @api.onchange('employee_id')
    def onchange_employee_contract(self):
        for rec in self:
            if rec.employee_id:
                contract_id = rec.env['hr.contract'].search([
                    ('employee_id', '=', rec.employee_id.id),
                    ('state', '=', 'open')],
                    limit=1, order="id DESC")

                rec.contract_id = rec.employee_id.contract_id.id if rec.employee_id.contract_id.state == 'open' else contract_id.id
                rec.old_payscale_id = contract_id.payscale_id
                rec.contract_status_old = rec.employee_id.contract_status
                rec.contract_status_new = rec.employee_id.contract_status

    # @api.depends('is_expired_contract', 'wassef_employee_type')
    # def _is_perm_staff(self):
    #     for rec in self:
    #         if rec.wassef_employee_type == 'perm_staff' and rec.is_expired_contract:
    #             rec.is_perm_staff = True
    #         else:
    #             rec.is_perm_staff = False

    @api.onchange('new_payscale_id')
    def _get_payscale_grade_values(self):
        res = {}
        if self.new_payscale_id:
            job_id = self.contract_id.job_id
            payscale_id = self.new_payscale_id
            # self.wage_new = payscale_id.basic_from
            res.update({
                'social_alw_new': payscale_id.social_allowance,
                'housing_new': payscale_id.housing_allowance,
                'transport_allowance_new': payscale_id.transport_allowance,
            })
            # self.social_alw_new = payscale_id.social_allowance
            # self.housing_new = payscale_id.housing_allowance
            # self.transport_allowance_new = payscale_id.transport_allowance
            if job_id and job_id.level == 'director':
                res.update({
                    'mobile_allowance_new': payscale_id.mob_department_director,
                    'car_alw_new': payscale_id.car_alw_dept_director,
                    'supervision_alw_new': payscale_id.supervision_unit_director,
                })
            elif job_id and job_id.level == 'manager':
                res.update({
                    'mobile_allowance_new': payscale_id.mob_department_manager,
                    'car_alw_new': payscale_id.car_alw_dept_manager,
                    'supervision_alw_new': payscale_id.supervision_department_manager,
                })
            elif job_id and job_id.level == 'assistant_manager':
                res.update({
                    'mobile_allowance_new': payscale_id.mob_other,
                    'car_alw_new': payscale_id.car_alw_other,
                    'supervision_alw_new': payscale_id.supervision_department_manager_ass,
                })
            elif job_id and job_id.level == 'others':
                res.update({
                    'mobile_allowance_new': payscale_id.mob_other,
                    'car_alw_new': payscale_id.car_alw_other,
                    'supervision_alw_new': 0,
                })
            else:
                res.update({
                    'mobile_allowance_new': 0,
                    'car_alw_new': 0,
                    'supervision_alw_new': 0,
                })
                # self.mobile_allowance_new = 0
                # self.car_alw_new = 0
                # self.supervision_alw_new = 0
                res.update({
                    'mobilisation_allowance': payscale_id.mobilisation_allowance,
                    'furniture_allowance': payscale_id.furniture_allowance,
                    'education_allowance': payscale_id.education_allowance,
                    'business_allowance': payscale_id.business_allowance,
                    'gross_salary_new': payscale_id.total_salary_from,
                    'car_loan': payscale_id.car_loan,
                    'marriage_loan_for_permanent_staff_new': payscale_id.marriage_loan,
                })

            # self.mobilisation_allowance = payscale_id.mobilisation_allowance
            # self.furniture_allowance = payscale_id.furniture_allowance
            # self.education_allowance = payscale_id.education_allowance
            # self.business_allowance = payscale_id.business_allowance
            # self.gross_salary_new = payscale_id.total_salary_from
            # self.car_loan = payscale_id.car_loan
            # self.marriage_loan_for_permanent_staff_new = payscale_id.marriage_loan
        else:
            res.update({
                'wage_new': 0.0,
                'social_alw_new': 0.0,
                'housing_new': 0.0,
                'transport_allowance_new': 0.0,
                'mobile_allowance_new': 0.0,
                'mobilisation_allowance': 0.0,
                'car_alw_new': 0.0,
                'supervision_alw_new': 0.0,
                'furniture_allowance': 0.0,
                'car_loan': 0.0,
                'education_allowance': 0.0,
                'business_allowance': 0.0,
                'marriage_loan_for_permanent_staff_new': 0.0,
            })
        self.write(res)

    mobilisation_allowance_for_permanent_staff_old = fields.Monetary(
        related="contract_id.mobilisation_alw")
    mobilisation_allowance = fields.Monetary(
        string="Mobilisation/ Repatriation/Shipping Allowance", states={'submit': [('readonly', True)],
                                                                        'confirm': [('readonly', True)],
                                                                        'approve': [('readonly', True)]})

    mobilisation_allowance_for_permanent_staff_differance = fields.Monetary("Mobilisation Allowance Difference",
                                                                            compute="_calc_mobilisation_allowance_differance")

    @api.depends('mobilisation_allowance')
    def _calc_mobilisation_allowance_differance(self):
        for rec in self:
            if rec.is_expired_contract and rec.mobilisation_allowance:
                rec.mobilisation_allowance_for_permanent_staff_differance = \
                    rec.mobilisation_allowance - \
                    rec.mobilisation_allowance_for_permanent_staff_old
            else:
                rec.mobilisation_allowance_for_permanent_staff_differance = 0.0

    car_loan_for_permanent_staff_old = fields.Monetary(
        related="contract_id.car_loan")
    car_loan = fields.Monetary(string="Car Loan", states={'submit': [('readonly', True)],
                                                          'confirm': [('readonly', True)],
                                                          'approve': [('readonly', True)]})

    car_loan_for_permanent_staff_differance = fields.Monetary("Car Loan Difference",
                                                              compute="_calc_car_loan_differance")

    @api.depends('car_loan')
    def _calc_car_loan_differance(self):
        for rec in self:
            if rec.is_expired_contract and rec.car_loan:
                rec.car_loan_for_permanent_staff_differance = rec.car_loan - \
                                                              rec.car_loan_for_permanent_staff_old
            else:
                rec.car_loan_for_permanent_staff_differance = 0.0

    marriage_loan_for_permanent_staff_old = fields.Monetary(
        related="contract_id.marriage_loan")
    marriage_loan_for_permanent_staff_new = fields.Monetary(string="Marriage Loan",
                                                            states={'submit': [('readonly', True)],
                                                                    'confirm': [
                                                                        ('readonly', True)],
                                                                    'approve': [
                                                                        ('readonly', True)]})

    marriage_for_permanent_staff_differance = fields.Monetary("Marriage Loan Difference",
                                                              compute="_calc_marriage_loan_differance")

    @api.depends('marriage_loan_for_permanent_staff_new')
    def _calc_marriage_loan_differance(self):
        for rec in self:
            if rec.is_expired_contract and rec.marriage_loan_for_permanent_staff_new:
                rec.marriage_for_permanent_staff_differance = rec.marriage_loan_for_permanent_staff_new - \
                                                              rec.marriage_loan_for_permanent_staff_old
            else:
                rec.marriage_for_permanent_staff_differance = 0.0

    furniture_allowance_for_permanent_staff_old = fields.Monetary(
        related="contract_id.furniture_alw")
    furniture_allowance = fields.Monetary(string="Furniture Allowance",
                                          states={'submit': [('readonly', True)],
                                                  'confirm': [('readonly', True)],
                                                  'approve': [('readonly', True)]})

    furniture_allowance_for_permanent_staff_differance = fields.Monetary("Furniture Allowance Difference",
                                                                         compute="_calc_furniture_allowance_differance")

    @api.depends('furniture_allowance')
    def _calc_furniture_allowance_differance(self):
        for rec in self:
            if rec.is_expired_contract and rec.furniture_allowance:
                rec.furniture_allowance_for_permanent_staff_differance = rec.furniture_allowance - \
                                                                         rec.furniture_allowance_for_permanent_staff_old
            else:
                rec.furniture_allowance_for_permanent_staff_differance = 0.0

    education_allowance_for_permanent_staff_old = fields.Monetary(
        related="contract_id.education_alw")
    education_allowance = fields.Monetary(string="Education Allowance",
                                          states={'submit': [('readonly', True)],
                                                  'confirm': [('readonly', True)],
                                                  'approve': [('readonly', True)]})

    education_allowance_for_permanent_staff_differance = fields.Monetary("Education Allowance Difference",
                                                                         compute="_calc_education_allowance_differance")

    @api.depends('education_allowance')
    def _calc_education_allowance_differance(self):
        for rec in self:
            if rec.is_expired_contract and rec.education_allowance:
                rec.education_allowance_for_permanent_staff_differance = rec.education_allowance - \
                                                                         rec.education_allowance_for_permanent_staff_old
            else:
                rec.education_allowance_for_permanent_staff_differance = 0.0

    business_allowance_non_gulf_old = fields.Monetary(
        related="contract_id.business_alw")
    business_allowance = fields.Monetary(string="BUSINESS/TRAINING TRIP GCC",
                                         states={'submit': [('readonly', True)],
                                                 'confirm': [('readonly', True)],
                                                 'approve': [('readonly', True)]})

    business_allowance_non_gulf_differance = fields.Monetary("BUSINESS/TRAINING TRIP GCC Difference",
                                                             compute="_calc_business_allowance_non_gulf_differance")

    import_from_file = fields.Boolean(string="Import From File", default=False)

    @api.depends('business_allowance')
    def _calc_business_allowance_non_gulf_differance(self):
        for rec in self:
            if rec.is_expired_contract and rec.business_allowance:
                rec.business_allowance_non_gulf_differance = rec.business_allowance - \
                                                             rec.business_allowance_non_gulf_old
            else:
                rec.business_allowance_non_gulf_differance = 0.0

    is_married = fields.Boolean(string="Married ?", compute="_check_is_married", default=False)
    is_qatari = fields.Boolean(string="Qatari ?", compute="_check_is_qatari", default=False)
    is_gcc_country = fields.Boolean(string="GCC ?", compute="_check_is_gcc", default=False)

    @api.depends('contract_status_new')
    def _check_is_married(self):
        for rec in self:
            if rec.contract_status_new == "married":
                rec.is_married = True
            else:
                rec.is_married = False

    @api.depends('employee_id.country_id')
    def _check_is_gcc(self):
        for rec in self:
            if rec.employee_id.country_id.code in GCC_COUNTRIES_CODES:
                rec.is_gcc_country = True
            else:
                rec.is_gcc_country = False

    @api.depends('employee_id.country_id')
    def _check_is_qatari(self):
        for rec in self:
            if rec.employee_id.country_id.code == "QA":
                rec.is_qatari = True
            else:
                rec.is_qatari = False

    payscale_id_domain = fields.Char(
        compute="_compute_payscale_id_domain",
        readonly=True
    )

    # employee_id_domain = fields.Char(compute="_compute_employee_domain", readonly=True)

    # @api.depends('employee_id')
    # def _compute_employee_domain(self):
    #     for rec in self:
    #         if self.env.user.has_group('ebs_hr_custom.group_user_manage_classified_employee'):
    #             rec.employee_id_domain = json.dumps([])
    #         else:
    #             rec.employee_id_domain = json.dumps([('is_classified', '=', False)])

    @api.depends('is_married', 'is_qatari', 'employee_id.country_id')
    def _compute_payscale_id_domain(self):
        for rec in self:
            rec.payscale_id_domain = json.dumps(
                [('is_married', '=', rec.is_married), ('is_qatari', '=', rec.is_qatari)]
            )

    def name_get(self):
        result = []
        for record in self:
            rec_name = f"Pro/{record.registration_number} / {record.name}"
            result.append((record.id, "%s" % rec_name))
        return result

    @api.model_create_multi
    def create(self, vals_list):
        for val in vals_list:
            val['name'] = self.env['ir.sequence'].next_by_code('employee.promotion') or _('New')

        return super(EmployeePromotion, self).create(vals_list)

    # def create_furniture_allowance(self):
    #     for rec in self:
    #         pass
    # if rec.employee_id.wassef_employee_type == 'perm_staff':
    #     maintenance_type_id = self.env['allowance.type'].search([('code', '=', 'maintenance')], limit=1)
    #     allowance = self.env['allowance.request']
    #     create_obj = {
    #         'employee_id': rec.employee_id.id,
    #         'allowance_type': maintenance_type_id.id,
    #         'requested_amount': rec.furniture_allowance_for_permanent_staff_differance,
    #         'eligible_amount': rec.furniture_allowance_for_permanent_staff_differance,
    #         'furniture_difference': rec.furniture_allowance_for_permanent_staff_differance,
    #         'payment_date': rec.date_start,
    #         'effective_date': rec.date_start,
    #         'note': 'Furniture Allowance Difference'
    #     }
    #     fur_allowance = allowance.create(create_obj)

    annual_leave_diff = fields.Float(string="Annual Leave Difference", compute="get_annual_leave_diff")
    old_annual_leave = fields.Float(string="Annual Leave", compute="get_annual_leave_of_contract")
    new_annual_leave = fields.Float(string="Annual Leave", compute="get_annual_leave_of_contract")

    # adjustments
    adj_wage = fields.Monetary(string="Wage Adjustment", compute="get_adjustment_amounts")
    adj_social_allowance = fields.Monetary(string="Social Allowance Adjustment", compute="get_adjustment_amounts")
    adj_housing_allowance = fields.Monetary(string="Housing Allowance Adjustment", compute="get_adjustment_amounts")
    adj_trans_allowance = fields.Monetary(string="Transport Allowance Adjustment", compute="get_adjustment_amounts")
    adj_mobile_allowance = fields.Monetary(string="Mobile Allowance Adjustment", compute="get_adjustment_amounts")
    adj_furniture_allowance = fields.Monetary(string="Furniture Allowance Adjustment", compute="get_adjustment_amounts")
    adj_edu_allowance = fields.Monetary(string="Education Allowance Adjustment", compute="get_adjustment_amounts")
    adj_total = fields.Monetary(string="Total Adjustment", compute="get_adjustment_amounts")
    days_differance = fields.Char(string='Days Differance')
    is_get_adjustment = fields.Boolean(default=False)

    # def allocate_annual_leave(self):
    #     for rec in self:
    #         if rec.annual_leave_diff and rec.date_start:
    #             end_date = rec.date_start.replace(month=12, day=31)
    #             working_days = self._get_working_days(rec.date_start, end_date)
    #             leave_days = rec.annual_leave_diff * working_days / 261
    #             holiday_status_id = self.env['hr.leave.type'].sudo().search([('code', '=', 'ANNUAL')])
    #             if leave_days >= 1:
    #                 res = self.env['hr.leave.allocation'].sudo().create({
    #                     'state': 'validate',
    #                     'holiday_status_id': holiday_status_id.id,
    #                     'employee_id': rec.employee_id.id,
    #                     'date_from': rec.date_start,
    #                     'date_to': end_date,
    #                     'number_of_days': round(leave_days),
    #
    #                 })

    @api.depends('old_payscale_id', 'new_payscale_id')
    def get_annual_leave_of_contract(self):
        for rec in self:
            rec.old_annual_leave = 0
            rec.new_annual_leave = 0
            if rec.old_payscale_id:
                for leave in rec.old_payscale_id.leave_type_ids:
                    if leave.leave_type.code == 'ANNUAL':
                        rec.old_annual_leave = leave.days
            if rec.new_payscale_id:
                for leave in rec.new_payscale_id.leave_type_ids:
                    if leave.leave_type.code == 'ANNUAL':
                        rec.new_annual_leave = leave.days
            else:
                rec.old_annual_leave = 0
                rec.new_annual_leave = 0

    @api.depends('old_payscale_id', 'new_payscale_id')
    def get_annual_leave_diff(self):
        for rec in self:
            if rec.old_payscale_id and rec.new_payscale_id:
                old_leave = 0
                new_leave = 0
                for leave in rec.old_payscale_id.leave_type_ids:
                    if leave.leave_type.code == 'ANNUAL':
                        old_leave = leave.days
                for leave in rec.new_payscale_id.leave_type_ids:
                    if leave.leave_type.code == 'ANNUAL':
                        new_leave = leave.days
                rec.annual_leave_diff = new_leave - old_leave
            else:
                rec.annual_leave_diff = 0

    def create_additional_elements(self):
        for rec in self:
            if rec.payment_date and rec.date_start:
                ticket = self.env['ir.config_parameter'].sudo().get_param('employee_promotion.ticket_allowance')
                additional_obj = self.env['ebspayroll.additional.elements']
                additional_line_obj = self.env['ebspayroll.additional.element.lines']
                if rec.wassef_employee_type == 'perm_staff' and rec.employee_id.country_id and rec.employee_id.country_id.code == 'QA':
                    if ticket and rec.ticket_allowance_diff > 0:
                        res = additional_obj.sudo().create({'type': int(ticket), 'payment_date': rec.payment_date})
                        additional_line_obj.sudo().create(
                            {'additional_element_id': res.id, 'employee': rec.employee_id.id,
                             'amount': rec.ticket_allowance_diff, })
                if rec.payment_date.month == rec.date_start.month == date.today().month:

                    pass
                elif rec.date_start.month < date.today().month:
                    basic = self.env['ir.config_parameter'].sudo().get_param('employee_promotion.basic')
                    social = self.env['ir.config_parameter'].sudo().get_param('employee_promotion.social')
                    housing = self.env['ir.config_parameter'].sudo().get_param('employee_promotion.housing')
                    transport = self.env['ir.config_parameter'].sudo().get_param('employee_promotion.transportation')
                    mobile = self.env['ir.config_parameter'].sudo().get_param('employee_promotion.mobile')
                    furniture = self.env['ir.config_parameter'].sudo().get_param(
                        'employee_promotion.furniture_allowance')

                    additional_obj = self.env['ebspayroll.additional.elements']
                    additional_line_obj = self.env['ebspayroll.additional.element.lines']
                    if basic and rec.adj_wage != 0:
                        res = additional_obj.sudo().create({
                            'type': int(basic),
                            'payment_date': rec.payment_date,
                        })
                        additional_line_obj.sudo().create({
                            'additional_element_id': res.id,
                            'employee': rec.employee_id.id,
                            'amount': rec.adj_wage,
                        })

                    if social and rec.adj_social_allowance != 0:
                        res = additional_obj.sudo().create({
                            'type': int(social),
                            'payment_date': rec.payment_date,
                        })
                        additional_line_obj.sudo().create({
                            'additional_element_id': res.id,
                            'employee': rec.employee_id.id,
                            'amount': rec.adj_social_allowance,
                        })

                    if housing and rec.adj_housing_allowance != 0:
                        res = additional_obj.sudo().create({
                            'type': int(housing),
                            'payment_date': rec.payment_date,
                        })
                        additional_line_obj.sudo().create({
                            'additional_element_id': res.id,
                            'employee': rec.employee_id.id,
                            'amount': rec.adj_housing_allowance,
                        })

                    if transport and rec.adj_trans_allowance != 0:
                        res = additional_obj.sudo().create({
                            'type': int(transport),
                            'payment_date': rec.payment_date,
                        })
                        additional_line_obj.sudo().create({
                            'additional_element_id': res.id,
                            'employee': rec.employee_id.id,
                            'amount': rec.adj_trans_allowance,
                        })

                    if mobile and rec.adj_mobile_allowance != 0:
                        res = additional_obj.sudo().create({
                            'type': int(mobile),
                            'payment_date': rec.payment_date,
                        })
                        additional_line_obj.sudo().create({
                            'additional_element_id': res.id,
                            'employee': rec.employee_id.id,
                            'amount': rec.adj_mobile_allowance,
                        })

                    if furniture and rec.adj_furniture_allowance != 0:
                        res = additional_obj.sudo().create({
                            'type': int(furniture),
                            'payment_date': rec.payment_date,
                        })
                        additional_line_obj.sudo().create({
                            'additional_element_id': res.id,
                            'employee': rec.employee_id.id,
                            'amount': rec.adj_furniture_allowance,
                        })

    # @api.constrains('date_start', 'payment_date')
    # def check_effective_date(self):
    #     for rec in self:
    #         effective_date = rec.date_start
    #         print(effective_date == effective_date.replace(day=1))
    #         if effective_date == effective_date.replace(day=1):
    #             pass
    #         else:
    #             raise ValidationError('Effective date must be first day of month.')

    @api.constrains('payment_date', 'date_start')
    def check_date(self):
        for rec in self:
            if rec.payment_date and rec.date_start:
                payment_date = datetime.strptime(str(rec.payment_date), "%Y-%m-%d")
                effective_date = datetime.strptime(str(rec.date_start), "%Y-%m-%d")
                if payment_date < effective_date:
                    raise ValidationError('Payment date must be greater than Effective date.')

    @api.depends('payment_date', 'date_start', 'wage_old', 'wage_new', 'new_payscale_id',
                 'housing_new', 'mobile_allowance_new')
    def get_adjustment_amounts(self):
        for rec in self:
            if rec.payment_date and rec.date_start and rec.wage_old and rec.wage_new:
                payment_date = datetime.strptime(str(rec.payment_date), "%Y-%m-%d")
                effective_date = datetime.strptime(str(rec.date_start), "%Y-%m-%d")
                final_payment_date = payment_date + timedelta(days=1)
                delta = relativedelta.relativedelta(final_payment_date, effective_date)
                # attendance_date = self.env['hr.attendance'].sudo().search([('employee_id', '=', rec.employee_id.id)],
                #                                                           order='check_in DESC', limit=1).check_in
                # last_attendance_date = attendance_date and datetime.strptime(str(attendance_date.date()), "%Y-%m-%d")
                if rec.payment_date.month == rec.date_start.month == date.today().month:
                    rec.is_get_adjustment = False
                    rec.adj_wage = 0.0
                    rec.adj_social_allowance = 0.0
                    rec.adj_housing_allowance = 0.0
                    rec.adj_trans_allowance = 0.0
                    rec.adj_mobile_allowance = 0.0
                    rec.adj_furniture_allowance = 0.0
                    rec.adj_edu_allowance = 0.0
                    rec.adj_total = 0.0
                elif effective_date < payment_date and rec.date_start < date.today():
                    rec.is_get_adjustment = True
                    if rec.wassef_employee_type == 'perm_staff':
                        wage_difference = rec.wage_new - rec.wage_old
                        social_diff = rec.social_allowance - rec.social_allowance_old
                        housing_diff = rec.housing_allowance - rec.housing_allowance_for_permanent_staff_old
                        transport_diff = rec.transport_allowance_new - rec.transport_allowance_old
                        mobile_diff = rec.mobile_allowance_new - rec.mobile_allowance_old
                        furniture_diff = rec.furniture_allowance - rec.furniture_allowance_for_permanent_staff_old
                        edu_diff = rec.education_allowance - rec.education_allowance_for_permanent_staff_old

                        rec.adj_wage = (delta.months * wage_difference)
                        rec.adj_social_allowance = (delta.months * social_diff)
                        rec.adj_housing_allowance = (delta.months * housing_diff)
                        rec.adj_trans_allowance = (delta.months * transport_diff)
                        rec.adj_mobile_allowance = (delta.months * mobile_diff)
                        rec.adj_furniture_allowance = (delta.months * furniture_diff)
                        rec.adj_edu_allowance = (delta.months * edu_diff)
                        print('111', rec.adj_wage, rec.adj_social_allowance, rec.adj_housing_allowance)

                    rec.adj_total = rec.adj_wage + rec.adj_social_allowance + rec.adj_housing_allowance + \
                                    rec.adj_trans_allowance + rec.adj_mobile_allowance + rec.adj_furniture_allowance + rec.adj_edu_allowance
                else:
                    rec.is_get_adjustment = False
                    rec.adj_wage = 0.0
                    rec.adj_social_allowance = 0.0
                    rec.adj_housing_allowance = 0.0
                    rec.adj_trans_allowance = 0.0
                    rec.adj_mobile_allowance = 0.0
                    rec.adj_furniture_allowance = 0.0
                    rec.adj_edu_allowance = 0.0
                    rec.adj_total = 0.0
            else:
                rec.is_get_adjustment = False
                rec.adj_wage = 0.0
                rec.adj_social_allowance = 0.0
                rec.adj_housing_allowance = 0.0
                rec.adj_trans_allowance = 0.0
                rec.adj_mobile_allowance = 0.0
                rec.adj_furniture_allowance = 0.0
                rec.adj_edu_allowance = 0.0
                rec.adj_total = 0.0

    @api.constrains('employee_id', 'old_payscale_id', 'new_payscale_id', 'contract_status_new', 'exceptional_promotion')
    def validate_promotion_rules(self):
        for record in self:
            promotion_rules = []
            domain = []
            if record.old_payscale_id:
                domain.append(('from_grade_id', '=', record.old_payscale_id.id))
            if record.employee_id.degree_id:
                domain.append(('degree_id', '=', record.employee_id.degree_id.id))
            if record.employee_id.actual_duty:
                domain.append(('number_of_actual_work_days', '<=', record.employee_id.actual_duty))
            if record.new_payscale_id:
                domain.append(('to_grade_id', '=', record.new_payscale_id.id))
            if record.contract_status_new:
                domain.append(('contract_marital_status', '=', record.contract_status_new))
            if not record.exceptional_promotion and not (
                    record.promotion_rule_id or record.payscale_scheduled_raise_id):
                promotion_rules = self.env['promotion.rules'].search(domain, limit=1)
                if not promotion_rules:
                    raise ValidationError('No Rules Founded!!')
