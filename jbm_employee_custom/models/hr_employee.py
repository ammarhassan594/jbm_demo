import logging
import itertools
from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
from dateutil import relativedelta
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class InheritHrEmployee(models.Model):
    _inherit = 'hr.employee'

    def _get_martial_status(self):
        if self.env.context.get('lang') == 'ar_001':

            return [
                ('single', 'اعزب'),
                ('married', 'متزوج'),
                ('widower', 'ارمل'),
                ('divorced', 'مطلق'),
            ]
        else:
            return [
                ('single', 'Single'),
                ('married', 'Married'),
                ('widower', 'Widower'),
                ('divorced', 'Divorced'),]

    registration_number = fields.Char('Employee no')
    contract_status = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married')
    ], string="Contract Status", default='single', groups="base.group_user", tracking=True)

    partner_parent_id_fos = fields.Many2one('res.partner', string='FOS Client/ FOS Company', required=False,
                                            readonly=False)

    joining_date = fields.Date(string='Joining Date')
    sponsorship_type = fields.Selection([('on the company', 'On the company'), ('on the familly', 'On the familly')],
                                        string='Sponsorship Type')
    contract_duration = fields.Selection(
        [('one', 'One'), ('two', 'Two'), ('three', 'Three'), ('four', 'Four'), ('five', 'Five'),
         ('open-ended', 'Unlimited')], string='Contract Duration', default='open-ended')

    probation = fields.Selection([('0d', '0 Months'), ('90d', '3 Months'), ('180d', '6 Months')], string="Probation",
                                 default='180d')
    probation_date = fields.Date("Probation Date", compute='_get_probation_date')

    is_end_probation_period = fields.Boolean(string='End Probation Period')
    number_of_years_work = fields.Char("Yrs w/ JBM", compute="_get_number_of_days_work")
    sponsor = fields.Many2one(comodel_name="hr.employee.sponsor", string="Sponsor")
    line_manager_id = fields.Many2one('hr.employee', string='Line 2 Manager',
                                      domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    status = fields.Selection(
        [('active', 'Active'), ('on vacation', 'On Vacation'), ('suspended', 'Suspended'),
         ('terminated', 'Terminated'), ('terminated_w_reason', 'Terminated with Reason'), ('resigned', 'Resigned')],
        string='Status')

    emp_children_ids = fields.One2many(comodel_name='hr.emp.child', inverse_name='emp_id', string="Children's")
    supervisor = fields.Many2one(
        comodel_name='hr.employee',
        string='Supervisor')

    marital = fields.Selection(selection=_get_martial_status, string="Marital Status")
    actual_duty_manual = fields.Integer(string="Previous Actual Duty", default=0)
    last_updated_actual_duty = fields.Integer(string="Last Actual Duty", default=0)
    actual_duty = fields.Integer(string="Actual Duty", default=0, readonly=True)
    out_of_attendance = fields.Boolean(string="Out Of Attendance")

    @api.onchange('department_id')
    def _onchange_department(self):
        if self.department_id.manager_id:
            self.parent_id = self.department_id.manager_id.id
        if self.department_id.line_manager_id:
            self.line_manager_id = self.department_id.line_manager_id.id

    @api.onchange('department_id')
    def _onchange_department(self):
        if self.department_id and self.department_id.manager_id:
            self.parent_id = self.department_id.manager_id.id
            self.leave_manager_id = self.department_id.manager_id.id
        if self.department_id and self.department_id.line_manager_id:
            self.line_manager_id = self.department_id.line_manager_id.id

    @api.depends('joining_date')
    def _get_number_of_days_work(self):
        today = fields.Date.today()
        for rec in self:
            if rec.joining_date and today > rec.joining_date:
                diff = relativedelta.relativedelta(today, rec.joining_date)
                rec.number_of_years_work = f'{diff.years} y, {diff.months} m'
            else:
                rec.number_of_years_work = 0

    @api.onchange('joining_date', 'probation')
    def _get_probation_date(self):
        for rec in self:
            pro_date = 0
            if rec.probation == '0d' and rec.joining_date:
                pro_date = rec.joining_date
            elif rec.probation == '90d' and rec.joining_date:
                pro_date = rec.joining_date + relativedelta.relativedelta(days=+90)
            elif rec.probation == '180d' and rec.joining_date:
                pro_date = rec.joining_date + relativedelta.relativedelta(days=+180)
            rec.probation_date = pro_date

    @api.onchange('actual_duty_manual')
    def _onchange_actual_duty_manual(self):
        for rec in self:
            rec.write({'actual_duty': rec.last_updated_actual_duty + rec.actual_duty_manual})

    @api.model
    def get_actual_duty(self):
        applied_on_date = self.env.company.applied_on_date
        today = date.today()
        if not applied_on_date:
            raise ValidationError(_('Please assign Applied on date in employee setting to proceed'))
        employees = self.search([])
        for employee in employees:
            if employee.joining_date:
                applied_on_date = applied_on_date if employee.joining_date < applied_on_date else employee.joining_date
            actual_days = (today - applied_on_date).days + 1
            unpaid_leaves, deducted_days, absences = self.get_current_year_deducted_leaves(employee, applied_on_date)
            _logger.info(f'unpaid_leaves {unpaid_leaves},'
                         f' deducted_days {deducted_days}, absences {absences}')
            actual_days -= (unpaid_leaves + deducted_days + absences)
            if any((actual_days, employee.actual_duty_manual)):
                total = actual_days + employee.actual_duty_manual
                employee.write({'actual_duty': total, 'last_updated_actual_duty': total})

    @staticmethod
    def count_employee_absences_days(employee, days, leaves_days, attendances_days):
        absences = 0
        for day in days:
            contract = employee.contract_ids.filtered(
                lambda contract:
                (contract.date_end and contract.date_start <= day <= contract.date_end)
                or (not contract.date_end and contract.date_start <= day)
            )
            weekend = str(day.weekday()) not in set(
                contract.resource_calendar_id.attendance_ids.mapped('dayofweek'))
            if weekend:
                continue

            public_holiday = contract.resource_calendar_id.global_leave_ids.filtered(
                lambda x: x.date_from.date() <= day <= x.date_to.date())
            if public_holiday:
                continue

            # leaves = self.env['hr.leave'].search([('employee_id', '=', employee.id),
            # ('request_date_from', '<=', today),
            #                                       ('request_date_to', '>=', today),
            #                                       ('state', '=', 'validate')],
            #                                      limit=1)
            if day in leaves_days or day in attendances_days:
                continue
            absences += 1
        return absences

    def get_current_year_deducted_leaves(self, employee, applied_on_date):
        leaves_dict = {}
        days_lst = []
        count = 0
        today = fields.Date.context_today(employee)
        if employee.joining_date:
            applied_on_date = applied_on_date if employee.joining_date < applied_on_date else employee.joining_date
        all_deducted_leaves = self.env['hr.leave'].search(
            [('employee_id', '=', employee.id),
             ('request_date_from', '>=', applied_on_date),
             ('request_date_to', '<=', today),
             ('state', '=', 'validate'), '|',
             ('holiday_status_id.is_unpaid', '=', True), ('holiday_status_id.actual_days_calculated', '=', True)],
            order='request_date_from')
        unpaid_days = sum(all_deducted_leaves.filtered(lambda x: x.holiday_status_id.is_unpaid).mapped(
            'number_of_days')) if all_deducted_leaves else 0
        deducted_legal_leaves = all_deducted_leaves.filtered(lambda x: not x.holiday_status_id.is_unpaid)
        all_days = [(applied_on_date + timedelta(days=x)) for x in range((today - applied_on_date).days + 1)]
        attendances = self.env['hr.attendance'].search([
            ('employee_id', '=', employee.id)
        ]).filtered(lambda a: applied_on_date <= a.check_in.date() <= today)
        attendances_days = set(attend.date() for attend in attendances.mapped('check_in'))
        leave_days = []
        for leave in deducted_legal_leaves:
            leave_days.extend(
                [(leave.request_date_from + timedelta(days=x)) for x in
                 range((leave.request_date_to - leave.request_date_from).days + 1)]
            )
        absences_days = self.count_employee_absences_days(employee, all_days, leave_days, attendances_days)
        for l in deducted_legal_leaves:
            if leaves_dict.get(f'{l.holiday_status_id.name}'):
                leaves_dict.get(f'{l.holiday_status_id.name}').append(
                    (l.request_date_from, l.request_date_to, l.holiday_status_id.max_allowed_days))
            else:
                leaves_dict.update({f'{l.holiday_status_id.name}': [
                    (l.request_date_from, l.request_date_to, l.holiday_status_id.max_allowed_days)]})
        for k, v in leaves_dict.items():
            result = []
            max_number = v[0][-1]
            if max_number == 0:
                continue
            for element in v:
                days_lst.extend(employee.deducted_days(element[0], element[1]))
            if days_lst:
                iterator = itertools.groupby(days_lst, lambda x: x.year)
                for element, group in iterator:
                    # appending the group by converting it into a list
                    item = list(group)
                    result.append(item)
                for res in result:
                    length = len(res)
                    if length > max_number:
                        count += length - max_number

        return unpaid_days, count, absences_days

    def deducted_days(self, date_from, date_to):
        lst = []
        work_days = self.get_working_days_of_the_week()
        public_holiday = self.resource_calendar_id.global_leave_ids
        for x in range((date_to - date_from).days + 1):
            day = date_from + timedelta(days=x)
            if str(day.weekday()) in work_days and not public_holiday.filtered(
                    lambda x: x.date_from.date() <= day <= date_to):
                lst.append(day)
        return lst

    def get_working_days_of_the_week(self):
        for rec in self:
            return set(
                [workday.dayofweek for workday in rec.resource_calendar_id.attendance_ids])
