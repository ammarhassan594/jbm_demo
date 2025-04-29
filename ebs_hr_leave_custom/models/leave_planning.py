import json
from odoo import fields, api, models, _
from datetime import datetime, date
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class HRLeavePlanning(models.Model):
    _name = "hr.leave.planning"
    _description = "HR Leave Planning"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _default_employee(self):
        return self.env.context.get('default_employee_id') or self.env.user.employee_id

    def _default_company(self):
        return self.env.context.get('default_company_id') or self.env.user.company_id

    employee_id = fields.Many2one(
        'hr.employee', string='Employee', ondelete="cascade", default=_default_employee,
        states={'approve': [('readonly', True)]})
    employee_number = fields.Char(related='employee_id.registration_number', string='Employee Number')
    # calc domain using web domain field
    employee_id_domain = fields.Char(
        compute="_compute_employee_id_domain",
        readonly=True,
        store=False,
    )
    type_leave = fields.Selection(
        [('working_days', 'Working Days'),
         ('calendar_days', 'Calendar Days')],
        string="Type Of Leave",
    )
    # allocation_count = fields.Float(related="employee_id.allocation_count", string="Allocation Count", store=True)
    total_allocation_days = fields.Float(string="Allocation Count", readonly=True)

    manager_id = fields.Many2one(related="employee_id.parent_id", string="Manager", readonly=True)

    department_id = fields.Many2one(related="employee_id.department_id", string='Department', readonly=True)

    company_id = fields.Many2one('res.company', string='Company', default=_default_company)
    job_id = fields.Many2one(related="employee_id.job_id", string='Job Position')

    planning_lines_ids = fields.One2many("hr.planning.leave.line", "leave_planning_id",
                                         states={'approve': [('readonly', True)]})
    # catch leaves request
    count_leaves_request = fields.Integer("Leaves", readonly=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('approve', 'Approved')
    ], string='Status', readonly=True,  copy=False, default='draft')

    total_of_working_days = fields.Float("Working Days Total", compute="_compute_total_working_days")
    total_of_calendar_days = fields.Float("Calendar Days Total", compute="_compute_total_calendar_days")
    available_number_days = fields.Text("Available Days")

    # Compute Functions
    @api.depends('employee_id')
    def _compute_employee_id_domain(self):
        """Apply dynamic domain on employee"""
        for rec in self:
            current_user = self.env.user
            is_admin_user = True if current_user.has_group('hr.group_hr_manager') or \
                                    current_user.has_group('hr_holidays.group_hr_holidays_manager') else False
            if is_admin_user:
                rec.employee_id_domain = json.dumps([])
            else:
                rec.employee_id_domain = json.dumps(['|', ('parent_id', '=', current_user.employee_id.id),
                                                     ('id', '=', current_user.employee_id.id)])

    @api.onchange('employee_id')
    def _get_leaves_of_employees(self):
        """Get all available leave type based on allocations on current year"""
        today_tz = fields.Datetime.context_timestamp(self.with_context(tz=self.employee_id.tz or 'UTC'), datetime.now())
        if self.employee_id:
            contract = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id),
                                                       ('state', '=', 'open')],
                                                      limit=1)
            self.type_leave = contract.type_leave
            allocations = self.env['hr.leave.allocation'].search(
                [('employee_id', '=', self.employee_id.id),
                 ('state', '=', 'validate'),
                 ('holiday_status_id.request_unit', '=', 'day'),
                 ('holiday_status_id.is_annual', '=', True),
                 ('holiday_status_id', '!=', False),
                 ('year', '=', today_tz.year)])
            lines = [(5, 0, 0)]
            available_number_days_total = 0
            leave_types = set(allocations.mapped('holiday_status_id'))
            available_number_days = ''
            for leave_type in leave_types:
                leave_type_id = self.env['hr.leave.type'].sudo().browse(int(leave_type))
                data_days = leave_type_id.get_employees_days([self.employee_id.id])[self.employee_id.id]
                result = data_days.get(leave_type_id.id, {})
                # max_leaves = result.get('max_leaves', 0)
                # leaves_taken = result.get('leaves_taken', 0)
                # remaining_leaves = result.get('remaining_leaves', 0)
                virtual_remaining_leaves = result.get('virtual_remaining_leaves', 0)
                vals = {
                    'leave_type_id': leave_type_id.id,
                    'leave_planning_id': self.id
                }
                lines.append((0, 0, vals))
                available_number_days_total += round(virtual_remaining_leaves, 2)
                available_number_days += f'Available days {round(virtual_remaining_leaves, 2)} on {leave_type_id.name}\n'
            self.available_number_days = available_number_days
            self.total_allocation_days = available_number_days_total
            self.planning_lines_ids = lines
        else:
            self.type_leave = False
            self.available_number_days = ''
            self.total_allocation_days = 0
            self.planning_lines_ids = False

    @api.depends('planning_lines_ids.working_days')
    def _compute_total_working_days(self):
        for rec in self:
            total_days = 0.0
            for line in rec.planning_lines_ids:
                if line.working_days:
                    total_days += line.working_days
            rec.total_of_working_days = total_days

    @api.depends('planning_lines_ids.calendar_days')
    def _compute_total_calendar_days(self):
        for rec in self:
            total_days = 0.0
            for line in rec.planning_lines_ids:
                if line.calendar_days:
                    total_days += line.calendar_days
            rec.total_of_calendar_days = total_days

    def _check_total_number_of_days(self):
        for rec in self:
            is_working_days = rec.type_leave == 'working_days'
            is_calendar_days = rec.type_leave == 'calendar_days'
            if is_calendar_days and rec.total_of_calendar_days > rec.total_allocation_days:
                raise ValidationError(_('Not allowed leave planning, '
                                        f'because number of total calender days {rec.total_of_calendar_days}  '
                                        f'bigger than number of {rec.total_allocation_days} total available'))
            if is_working_days and rec.total_of_working_days > rec.total_allocation_days:
                raise ValidationError(_('Not allowed leave planning, '
                                        f'because number of total working days {rec.total_of_working_days} '
                                        f'bigger than number of {rec.total_allocation_days} total available'
                                        ))

    # calc count of leaves for smart button
    def _get_count_leaves_request(self):
        """Count number of leaves for smart button"""
        leaves = self._get_related_leaves()
        self.count_leaves_request = len(leaves)

    def _get_related_leaves(self):
        return self.env['hr.leave'].sudo().search([
            ('leave_planning_id', '=', self.id)
        ])

    # Action Buttons
    def action_confirm(self):
        # check calendar and working days total
        self._check_total_number_of_days()
        # check if has leave on same period
        self._check_leaves_on_same_period()
        self.state = 'confirm'
        manager = self.employee_id.parent_id and self.employee_id.parent_id.user_id or \
                  self.employee_id.line_manager_id and self.employee_id.line_manager_id.user_id
        if self.env.user != manager:
            if self.activity_ids:
                self.sudo().activity_ids.action_done()
            all_users = manager
            self._create_activity(all_users)

    def action_approve(self):
        current_user = self.env.user
        if current_user.employee_id:
            is_admin_user = True if current_user.has_group('hr.group_hr_manager') or \
                                    current_user.has_group('hr_holidays.group_hr_holidays_manager') else False
            if not (self.manager_id == current_user.employee_id or is_admin_user):
                raise ValidationError(
                    _(f'Can not approve because you are not manager of this employee {self.employee_id.name}'))
        else:
            raise ValidationError(
                _(f'Can not approve because you are not manager of this employee {self.employee_id.name}'))
        for line in self.planning_lines_ids:
            if not line.employee_replacement_id:
                raise UserError(_('Please enter employee replacement'))
            if line.leave_type_id and line.date_from and line.date_to and line.employee_replacement_id:
                try:
                    leave = self.env['hr.leave'].sudo().new({
                        'name': f'{self.employee_id.name} {line.leave_type_id.name}',
                        'holiday_status_id': line.leave_type_id.id,
                        'department_id': self.department_id.id,
                        'employee_id': self.employee_id.id,
                        'employee_id_2': self.employee_id.id,
                        'request_date_from': line.date_from,
                        'request_date_to': line.date_to,
                        'replacement_employee_resource_id': self.employee_id.resource_id.id,
                        'leave_planning_id': self.id,
                    })
                    # leave.sudo()._onchange_request_parameters()
                    leave.sudo()._compute_number_of_days_display()
                    leave.sudo()._compute_number_of_hours_display()
                    leave.sudo()._compute_duration_display()
                    leave_vals = leave._convert_to_write(leave._cache)
                    self.env['hr.leave'].sudo().with_context(from_hr_planning=True).create(leave_vals)
                except Exception as e:
                    _logger.info('error {}'.format(e))
                    raise UserError(_(f'Error {e}'))

        self.state = 'approve'
        # count leaves
        self._get_count_leaves_request()
        # delete all activities on leave record
        self.sudo().activity_ids.action_done()
        # send email for employee manager
        if self.manager_id:
            base = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            leave_planning_object = base + "/web" + "/#id=%s&view_type=form&model=hr.leave.planning" % (self.id)
            employee_object = base + "/web" + "/#id=%s&view_type=form&model=hr.employee" % self.employee_id.id
            ctx = {
                'email_to': self.manager_id.work_email,
                'email_from': self.env.user.company_id.email,
                'send_email': True,
                'leave_planning_obj': leave_planning_object,
                'employee_obj': employee_object,
            }
            template = self.env.ref('ebs_hr_leave_custom.leave_planning_send_approve_managers')
            template.with_context(ctx).send_mail(self.id, force_send=True, raise_exception=False)

        else:
            raise ValidationError(_('Check leave line type, employee replacement, date from and date to'))

    def return_to_draft(self):
        current_user = self.env.user
        is_admin_user = True if current_user.has_group('hr.group_hr_manager') \
                                or current_user.has_group('hr_holidays.group_hr_holidays_manager') \
                                or self.env.user == self.employee_id.parent_id.user_id else False
        if is_admin_user:
            if self.state in ['confirm']:
                # delete all activities on leave record
                if self.activity_ids:
                    self.sudo().activity_ids.action_done()
                user = self.employee_id.user_id
                self._create_activity(user)
                self.state = 'draft'
        else:
            raise ValidationError(_('You not have permission to return request'))

    # fetch only leaves request
    def leaves_request_action(self):
        leaves = self._get_related_leaves()
        return {
            'name': _("leaves Request"),
            'domain': [('id', 'in', leaves.ids)],
            'context': {'create': False, 'edit': False, 'delete': False},
            'view_type': 'form',
            'res_model': 'hr.leave',
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window'
        }

    def name_get(self):
        result = []
        for record in self:
            rec_name = f"Planning leave of {record.employee_id.name}"
            result.append((record.id, rec_name))
        return result

    def unlink(self):
        for rec in self:
            if rec.state in ['approve']:
                raise ValidationError(_('You cannot delete approved request'))
            if rec.planning_lines_ids:
                rec.planning_lines_ids.unlink()
        return super(HRLeavePlanning, self).unlink()

    def _create_activity(self, all_users):
        all_users = all_users.sudo()
        activity_to_do = self.env.ref('ebs_hr_leave_custom.mail_act_hr_leave_planning_approval').id
        model_id = self.env['ir.model']._get('hr.leave.planning').id
        activity = self.env['mail.activity']
        for user in all_users:
            if user:
                act_dct = {
                    'activity_type_id': activity_to_do,
                    'note': "kindly check this leave planning Approval Request, it's awaiting your approval",
                    'user_id': user.sudo().employee_id.sudo().user_id.id,
                    'res_id': self.id,
                    'res_model_id': model_id,
                    'date_deadline': datetime.today().date()
                }
                activity.sudo().create(act_dct)

    def _send_email_employees(self):
        today_date = date.today()
        if today_date and today_date.day == 20 and today_date.month == 12:
            _logger.info('Run cron job for leave planning on %s', today_date)
            all_employees = self.env["hr.employee"].search([('active', '=', True)])
            all_emails = [emp.work_email for emp in all_employees if emp.work_email]
            ctx = {}
            if all_employees:
                ctx['email_to'] = ','.join(all_emails)
                ctx['email_from'] = self.env.user.company_id.email
                ctx['send_email'] = True
                template = self.env.ref('ebs_hr_leave_custom.send_leave_planning_email_template')
                template.with_context(ctx).send_mail(self.id, force_send=True, raise_exception=False)
        else:
            _logger.info('Can not run cron job for leave planning on %s', today_date)

    def _check_leaves_on_same_period(self):
        if self.planning_lines_ids:
            for line in self.planning_lines_ids:
                conflicting_leaves = self.env['hr.leave'].sudo().with_context(
                    tracking_disable=True,
                    mail_activity_automation_skip=True,
                    leave_fast_create=True
                ).search([
                    ('date_from', '<=', line.date_to),
                    ('date_to', '>=', line.date_from),
                    ('state', 'not in', ['cancel', 'refuse']),
                    ('holiday_type', '=', 'employee'),
                    ('employee_id', 'in', self.employee_id.ids)])
                print('conflicting_leaves ', conflicting_leaves)
                if conflicting_leaves:
                    raise ValidationError(_('You can not have 2 leaves that overlaps on the same day.'))


class HrPlanningLeaveLine(models.Model):
    _name = 'hr.planning.leave.line'
    _rec_name = 'leave_type_id'

    leave_type_id = fields.Many2one('hr.leave.type', string="Leave", required=True)
    date_from = fields.Date("Date From", required=True)
    date_to = fields.Date("Date To", required=True)
    working_days = fields.Float("Working Days", compute="_compute_get_working_days")
    calendar_days = fields.Float("Calendar Days", compute="_compute_get_calendar_days")
    leave_planning_id = fields.Many2one("hr.leave.planning")
    state = fields.Selection(related="leave_planning_id.state")
    employee_replacement_id = fields.Many2one('hr.employee', string="Employee Replacement")
    leave_id_domain = fields.Char(
        compute="_compute_leave_id_domain",
        readonly=True,
        store=False,
    )

    @api.depends('leave_type_id')
    def _compute_leave_id_domain(self):
        for rec in self:
            today_tz = fields.Datetime.context_timestamp(
                self.with_context(tz=rec.leave_planning_id.employee_id.tz or 'UTC'),
                datetime.now())
            print("compute leave id TZ ", today_tz)
            if rec.leave_planning_id.employee_id:
                allocations = self.env['hr.leave.allocation'].search(
                    [('employee_id', '=', rec.leave_planning_id.employee_id.id),
                     ('state', '=', 'validate'),
                     ('holiday_status_id.request_unit', '=', 'day'),
                     ('holiday_status_id.is_annual', '=', True),
                     ('year', '=', today_tz.year)])
                list_leaves = [allocation.holiday_status_id.id for allocation in allocations]
                if allocations:
                    rec.leave_id_domain = json.dumps(
                        [('id', 'in', list_leaves), ('request_unit', '=', 'day')]
                    )
                else:
                    rec.leave_id_domain = json.dumps([('id', 'in', list_leaves), ('request_unit', '=', 'day')])
            else:
                rec.leave_id_domain = json.dumps([('id', '=', False)])

    @api.depends('leave_type_id', 'date_from', 'date_to')
    def _compute_get_working_days(self):
        for rec in self:
            if rec.leave_type_id and rec.date_from and rec.date_to:
                if rec.leave_planning_id.employee_id:
                    date_from = datetime.combine(rec.date_from, datetime.min.time())
                    date_to = datetime.combine(rec.date_to, datetime.max.time())
                    employee = rec.leave_planning_id.employee_id
                    days = employee.resource_calendar_id.sudo().get_working_days(date_from, date_to)
                    rec.working_days = days
                else:
                    rec.working_days = 0.0
            else:
                rec.working_days = 0.0

    @api.depends('leave_type_id', 'date_from', 'date_to')
    def _compute_get_calendar_days(self):
        for rec in self:
            if rec.leave_planning_id and rec.date_from and rec.date_to:
                days = (rec.date_to - rec.date_from).days + 1
                rec.calendar_days = days
            else:
                rec.calendar_days = 0.0

    @api.onchange('date_from', 'date_to')
    def _check_date(self):
        for rec in self:
            if rec.date_to and rec.date_from and rec.date_to < rec.date_from:
                raise ValidationError(_('Error date to less than date from'))
            elif rec.date_from and rec.date_to and rec.date_from > rec.date_to:
                raise ValidationError(_('Error date from bigger than date to'))
