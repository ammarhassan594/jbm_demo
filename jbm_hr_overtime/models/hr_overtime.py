from dateutil import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class Overtime(models.Model):
    _name = 'hr.overtime'
    _description = "HR Overtime"
    _inherit = ['mail.thread']

    def _get_employee_domain(self):
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.user.id)], limit=1)
        domain = [('id', '=', employee.id)]
        if self.env.user.has_group('hr.group_hr_user'):
            domain = []
        return domain

    def _default_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    @api.onchange('total_hours')
    def _onchange_number_of_days(self):
        self.days_no = self.total_hours

    name = fields.Char('Name', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  domain=_get_employee_domain, default=lambda self: self.env.user.employee_id.id,
                                  required=True)
    department_id = fields.Many2one('hr.department', string="Department",
                                    related="employee_id.department_id")
    job_id = fields.Many2one('hr.job', string="Job", related="employee_id.job_id")
    manager_id = fields.Many2one('res.users', string="Manager",
                                 related="employee_id.parent_id.user_id", store=True)
    contract_id = fields.Many2one('hr.contract', string="Contract",
                                  related="employee_id.contract_id",
                                  )
    date_from = fields.Date('Date From', readonly=True)
    date_to = fields.Date('Date to', readonly=True)
    total_hours = fields.Float('Hours',)
    days_no = fields.Float('No. of Days')
    description = fields.Text('Description')
    state = fields.Selection([('draft', 'Draft'),
                              ('confirmed', 'Waiting'),
                              ('approved', 'Approved'),
                              ('refused', 'Refused')], string="state",
                             default="draft")
    leave_id = fields.Many2one('hr.leave.allocation',
                               string="Leave")
    attached_file = fields.Binary('Attached File')
    attached_file_name = fields.Char('File Name')
    type = fields.Selection([('cash', 'Cash'), ('leave', 'Leave')], default="cash", required=True, string="Type")
    duration_type = fields.Selection([('hours', 'Hours'), ('days', 'Days')], string="Duration Type", default="hours",
                                     required=True, readonly=True)
    cash_hrs_amount = fields.Float(string='Overtime Amount', readonly=True)
    cash_day_amount = fields.Float(string='Overtime Amount', readonly=True)
    payslip_paid = fields.Boolean('Paid in Payslip', readonly=True)

    employee_number = fields.Char(related="employee_id.registration_number", stored=True)
    ot_line_ids = fields.One2many('hr.overtime.line', 'overtime_id', string="Overtime Line")
    t_normal_hours = fields.Float('Normal Hours', compute="_get_total_normal_hours", store=True)
    t_special_hours = fields.Float('Special Hours', compute="_get_total_special_hours", store=True)

    @api.onchange('employee_id')
    def _get_defaults(self):
        for sheet in self:
            if sheet.employee_id:
                sheet.update({
                    'department_id': sheet.employee_id.department_id.id,
                    'job_id': sheet.employee_id.job_id.id,
                    'manager_id': sheet.sudo().employee_id.parent_id.user_id.id,
                })
    
    def action_confirm(self):
        # recipient_partners = [(4, self.current_user.partner_id.id)]
        # body = "Your OverTime Request Waiting Finance Approve .."
        # msg = _(body)
        # 
        # # notification to finance :
        # group = self.env.ref('account.group_account_invoice', False)
        # recipient_partners = []
        # 
        # body = "You Get New Time in Lieu Request From Employee : " + str(
        #     self.employee_id.name)
        # msg = _(body)
        return self.sudo().write({
            'state': 'confirmed'
        })
    
    def action_approve(self):
        # if self.overtime_type_id.type == 'leave':
        #     if self.duration_type == 'days':
        #         holiday_vals = {
        #             'name': 'Overtime',
        #             'holiday_status_id': self.overtime_type_id.leave_type.id,
        #             'number_of_days': self.total_hours,
        #             'notes': self.description,
        #             'holiday_type': 'employee',
        #             'employee_id': self.employee_id.id,
        #             'state': 'validate',
        #         }
        #     else:
        #         day_hour = self.total_hours / HOURS_PER_DAY
        #         holiday_vals = {
        #             'name': 'Overtime',
        #             'holiday_status_id': self.overtime_type_id.leave_type.id,
        #             'number_of_days': day_hour,
        #             'notes': self.description,
        #             'holiday_type': 'employee',
        #             'employee_id': self.employee_id.id,
        #             'state': 'validate',
        #         }
        #     holiday = self.env['hr.leave.allocation'].sudo().create(
        #         holiday_vals)
        #     self.leave_id = holiday.id
        #
        # # notification to employee :
        # recipient_partners = [(4, self.current_user.partner_id.id)]
        # body = "Your Time In Lieu Request Has been Approved ..."
        # msg = _(body)
        return self.sudo().write({
            'state': 'approved',

        })

    def action_reject(self):
        self.state = 'refused'

    @api.constrains('date_from', 'date_to')
    def _check_date(self):
        for rec in self:
            domain = [
                ('date_from', '<=', rec.date_to),
                ('date_to', '>=', rec.date_from),
                ('employee_id', '=', rec.employee_id.id),
                ('id', '!=', rec.id),
                ('state', 'not in', ['refused']),
            ]
            nholidays = self.search_count(domain)
            if nholidays:
                raise ValidationError(_(
                    'You can not have 2 Overtime requests that overlaps on same day!'))
    
    @api.model
    def create(self, values):
        seq = self.env['ir.sequence'].next_by_code('hr.overtime') or '/'
        values['name'] = seq
        return super(Overtime, self.sudo()).create(values)

    def unlink(self):
        for overtime in self.filtered(
                lambda overtime: overtime.state != 'draft'):
            raise UserError(
                _('You cannot delete TIL request which is not in draft state.'))
        return super(Overtime, self).unlink()

    @api.onchange('ot_line_ids', 'ot_line_ids.date')
    def _onchange_line_date(self):
        for rec in self:
            dates = rec.ot_line_ids.sorted(key=lambda x: x.date).mapped('date')
            if dates:
                rec.date_from = dates[0]
                rec.date_to = dates[-1]

    @api.depends('ot_line_ids')
    def _get_total_normal_hours(self):
        for rec in self:
            total_normal = 0.0
            if rec.ot_line_ids:
                for line in rec.ot_line_ids:
                    if line.paid and line.overtime_type == 'normal':
                        total_normal += line.hours
                rec.t_normal_hours = total_normal

    @api.depends('ot_line_ids')
    def _get_total_special_hours(self):
        for rec in self:
            total_special = 0.0
            if rec.ot_line_ids:
                for line in rec.ot_line_ids:
                    if line.paid and line.overtime_type == 'special':
                        total_special += line.hours
                rec.t_special_hours = total_special

    @api.depends('ot_line_ids')
    def _get_total_hours(self):
        for rec in self:
            total_hours = 0.0
            if rec.ot_line_ids:
                for line in rec.ot_line_ids:
                    if line.paid:
                        total_hours += line.hours
                rec.total_hours = total_hours



