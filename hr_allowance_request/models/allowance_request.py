# -*- coding: utf-8 -*-
import math
from datetime import datetime, date, timedelta
import datetime as d
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import json
import logging
from pytz import timezone

GCC_COUNTRIES_CODES = ['QA', 'BH', 'OM', 'AE', 'KW', 'SA']
_logger = logging.getLogger(__name__)


class AllowanceRequest(models.Model):
    _name = 'allowance.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Allowance Request"

    @api.model
    def default_get(self, field_list):
        result = super(AllowanceRequest, self).default_get(field_list)
        if result.get('user_id'):
            ts_user_id = result['user_id']
        else:
            ts_user_id = self.env.context.get('user_id', self.env.user.id)
        if not self._context.get('default_parent'):
            result['employee_id'] = self.env['hr.employee'].search([('user_id', '=', ts_user_id)], limit=1).id
        return result

    # allowance_type = fields.Selection([('education', 'Education Allowance'),('furniture', 'Furniture Allowance'),
    #     ('ticket', 'Ticket Allowance'),
    #     ('mobilization', 'Mobilization Allowance'),
    #     ('trip', 'BUSINESS/TRAINING Trip allowance'),
    # ], string="Allowance Type", default='education', track_visibility='onchange', copy=False)

    allowance_type = fields.Many2one(comodel_name='allowance.type', string='Allowance Type', required=True, copy=False,
                                     states={
                                         'approved': [('readonly', True)],
                                         'confirmed': [('readonly', True)],
                                         'refused': [('readonly', True)],
                                         'canceled': [('readonly', True)],
                                         'paid': [('readonly', True)],
                                     }
                                     )
    code = fields.Char(string='', related='allowance_type.code', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('first_approved', 'First Approval'),
        ('approved', 'Second Approval'),
        ('paid', 'Paid'),
        ('refused', 'Refused'),
        ('canceled', 'Cancelled'),
    ], string="State", default='draft', track_visibility='onchange', copy=False, )

    name = fields.Char(string="Name", default="/", readonly=True)

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, help="Employee",
                                  states={
                                      'approved': [('readonly', True)],
                                      'confirmed': [('readonly', True)],
                                      'refused': [('readonly', True)],
                                      'canceled': [('readonly', True)],
                                      'paid': [('readonly', True)],
                                  }
                                  )
    employee_number = fields.Char(related="employee_id.registration_number")
    # employee_id_domain = fields.Char(string="Employee Domain", compute="_get_employee_domain")
    user_id = fields.Many2one('res.users', string="User", compute="_get_current_user")
    country_id = fields.Many2one('res.country', string="Nationality", related='employee_id.country_id')
    marital = fields.Selection(string="Marital Status", related='employee_id.contract_status')
    gender = fields.Selection(string="Gender", related='employee_id.gender')
    date = fields.Date(string="Request Date", default=fields.Date.today(), help="Date")
    # qatari_doc_holder = fields.Boolean(string='Qatari Document Holder', required=False,
    #                                    states={
    #                                        'approved': [('readonly', True)],
    #                                        'refused': [('readonly', True)],
    #                                        'canceled': [('readonly', True)],
    #                                    }
    #                                    )
    academic_id = fields.Many2one(comodel_name='academic.year', string='Academic Year', required=False,
                                  states={
                                      'approved': [('readonly', True)],
                                      'confirmed': [('readonly', True)],
                                      'refused': [('readonly', True)],
                                      'canceled': [('readonly', True)],
                                      'paid': [('readonly', True)],
                                  }
                                  )
    start_date = fields.Date(string="Start Time", default=fields.Date.today(),
                             states={
                                 'approved': [('readonly', True)],
                                 'confirmed': [('readonly', True)],
                                 'refused': [('readonly', True)],
                                 'canceled': [('readonly', True)],
                                 'paid': [('readonly', True)],
                             }
                             )
    end_date = fields.Date(string="End Time",
                           default=lambda self: fields.Date.to_string((datetime.now() + relativedelta(days=+1)).date()),
                           states={
                               'approved': [('readonly', True)],
                               'confirmed': [('readonly', True)],
                               'refused': [('readonly', True)],
                               'canceled': [('readonly', True)],
                               'paid': [('readonly', True)],
                           }
                           )
    destination = fields.Many2one('res.country', string="Destination",
                                  states={
                                      'approved': [('readonly', True)],
                                      'confirmed': [('readonly', True)],
                                      'refused': [('readonly', True)],
                                      'canceled': [('readonly', True)],
                                      'paid': [('readonly', True)],
                                  }
                                  )
    eligible_amount = fields.Float(string="Eligible Amount", compute='_get_eligible_amount', store=True)
    requested_amount = fields.Float(string="Requested Amount", required=True,
                                    states={
                                        'approved': [('readonly', True)],
                                        'confirmed': [('readonly', True)],
                                        'refused': [('readonly', True)],
                                        'canceled': [('readonly', True)],
                                        'paid': [('readonly', True)],
                                    }, default=0.0
                                    )
    approved_amount = fields.Float(string="Approved Amount",
                                   states={
                                       'approved': [('readonly', True)],
                                       'confirmed': [('readonly', True)],
                                       'refused': [('readonly', True)],
                                       'canceled': [('readonly', True)],
                                       'paid': [('readonly', True)],
                                   }
                                   )
    note = fields.Text(string="Note",
                       states={
                           'approved': [('readonly', True)],
                           'confirmed': [('readonly', True)],
                           'refused': [('readonly', True)],
                           'canceled': [('readonly', True)],
                           'paid': [('readonly', True)],
                       }
                       )

    company_id = fields.Many2one('res.company', 'Company', readonly=True, help="Company",
                                 default=lambda self: self.env.user.company_id,
                                 states={'draft': [('readonly', False)]})
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, help="Currency",
                                  default=lambda self: self.env.user.company_id.currency_id,
                                  states={
                                      'approved': [('readonly', True)],
                                      'confirmed': [('readonly', True)],
                                      'refused': [('readonly', True)],
                                      'canceled': [('readonly', True)],
                                      'paid': [('readonly', True)],
                                  }
                                  )
    total_dependent = fields.Integer(string='Total Dependent', compute='get_employee_dependants')
    eligible_dependent = fields.Integer(string='Eligible Dependent', compute='get_employee_dependants')
    education_allowance_ids = fields.One2many('education.allowance.line', 'allowance_request_id',
                                              states={
                                                  'approved': [('readonly', True)],
                                                  'confirmed': [('readonly', True)],
                                                  'refused': [('readonly', True)],
                                                  'canceled': [('readonly', True)],
                                                  'paid': [('readonly', True)],
                                              }
                                              )
    # total_education_requested_amount = fields.Float('Education Requested Amount', compute="_get_education_allowance")

    allowance_line = fields.One2many(comodel_name='allowance.request.line', inverse_name='allowance_id',
                                     string='Allowance line', required=False,
                                     states={
                                         'confirmed': [('readonly', True)],
                                         'refused': [('readonly', True)],
                                         'canceled': [('readonly', True)],
                                         'paid': [('readonly', True)],
                                     }
                                     )
    depreciation_line = fields.One2many(comodel_name='allowance.depreciation', inverse_name='allowance_id',
                                        string='Amortization', readonly=True)

    remaining_unamortized_balance = fields.Float(compute="_get_remaining_unamortized_balance",
                                                 string="Remaining Unamortized Balance")
    amortized_balance = fields.Float(compute="_get_amortized_balance", string="Amortized Balance")

    airport_id = fields.Many2one(related='employee_id.contract_id.airport_id', required=False,
                                 states={
                                     'approved': [('readonly', True)],
                                     'refused': [('readonly', True)],
                                     'canceled': [('readonly', True)],
                                     'paid': [('readonly', True)],
                                 }
                                 )
    adult_fare = fields.Monetary(string='Adult Fare', compute='_get_fares')

    child_fare = fields.Monetary(string='Child Fare', compute='_get_fares')
    infant_fare = fields.Monetary(string='Infant Fare', compute='_get_fares')
    total_collected = fields.Monetary(string='Total Collected', compute='_get_total_allowance_line')
    final_approve_date = fields.Date(string='Final Approve Date',
                                     states={
                                         'approved': [('readonly', True)],
                                         'refused': [('readonly', True)],
                                         'confirmed': [('readonly', True)],
                                         'canceled': [('readonly', True)],
                                         'paid': [('readonly', True)],
                                     }
                                     )
    payment_date = fields.Date(string='Payment Date',
                               states={
                                   'approved': [('readonly', False)],
                                   'confirmed': [('readonly', True)],
                                   'refused': [('readonly', True)],
                                   'canceled': [('readonly', True)],
                                   'paid': [('readonly', True)],
                               }
                               )
    effective_date = fields.Date(string='Effective Date',
                                 states={
                                     'approved': [('readonly', True)],
                                     'confirmed': [('readonly', True)],
                                     'refused': [('readonly', True)],
                                     'canceled': [('readonly', True)],
                                     'paid': [('readonly', True)],
                                 }
                                 )

    remaining_amount = fields.Float(string='Remaining Amount', readonly=True, states={
        'approved': [('readonly', True)],
        'confirmed': [('readonly', True)],
        'refused': [('readonly', True)],
        'canceled': [('readonly', True)],
        'paid': [('readonly', True)],
    })

    air_ticket_allowance = fields.Selection(related="employee_id.contract_id.payscale_id.air_ticket_allowance")

    total_balance = fields.Float('Total Balance', compute="_get_total_balance")
    total_requested_amount = fields.Float('Total Requested Amount', compute="_get_total_requested")

    display_airport_info = fields.Boolean('Display Airports Info')
    created_automatically = fields.Boolean()
    is_created_by_script = fields.Boolean()

    count_dependants_note = fields.Text(string="Dependants", readonly=True)

    furniture_difference = fields.Float()

    is_imported = fields.Boolean(default=False)

    parent = fields.Many2one(comodel_name="allowance.request", string="Parent", required=False, )
    dependent_id = fields.Many2one(comodel_name='hr.emp.child', domain="[('emp_id', '=', employee_id)]", store=True)
    emp_child = fields.One2many(
        comodel_name='allowance.dependent',
        inverse_name='allowance_id',
        string="Dependents")
    children_count = fields.Integer(compute='_compute_children_count')
    no_dependent = fields.Boolean(default=False)
    active = fields.Boolean(default=True)
    automatic_leave_allowance = fields.Boolean('Automatic Leave Allowance')
    ticket_leave_id = fields.Many2one('hr.leave')

    def _create_activity(self, all_users):
        all_users = all_users.sudo()
        activity_to_do = self.env.ref('mail.mail_activity_data_todo').id
        model_id = self.env['ir.model']._get('allowance.request').id
        activity = self.env['mail.activity']
        for user in all_users:
            if user:
                act_dct = {
                    'activity_type_id': activity_to_do,
                    'note': "kindly check this allowance request edite's!",
                    'user_id': user.id,
                    'res_id': self.id,
                    'res_model_id': model_id,
                    'date_deadline': datetime.today().date()
                }
                activity.sudo().create(act_dct)

    # def write(self, vals):
    #     object = super(AllowanceRequest, self).write(vals)
    #     if vals:
    #         users = self.env['res.users'].search([])
    #         if users:
    #             for user in users:
    #                 if user.has_group("jbm_group_access_right_extended.custom_group_shared_service_manager"):
    #                     self._create_activity(user)
    #     return object

    def _compute_children_count(self):
        for allowance in self:
            children = len(
                self.env['allowance.request'].search([('parent', '=', self.id)]))
            allowance.children_count = children

    @api.depends('depreciation_line')
    def _get_remaining_unamortized_balance(self):
        for allowance in self:
            if allowance.depreciation_line:
                remaining_unamortized_balance_lines = allowance.depreciation_line.filtered(
                    lambda line: date.today() < line.date)
                allowance.remaining_unamortized_balance = sum(remaining_unamortized_balance_lines.mapped('amount'))
            else:
                allowance.remaining_unamortized_balance = 0

    @api.depends('depreciation_line')
    def _get_amortized_balance(self):
        for allowance in self:
            if allowance.depreciation_line:
                amortized_balance_lines = allowance.depreciation_line.filtered(lambda line: date.today() > line.date)
                allowance.amortized_balance = sum(amortized_balance_lines.mapped('amount'))
            else:
                allowance.amortized_balance = 0

    @api.onchange('employee_id', 'country_id', 'code')
    def check_airport_info(self):
        for rec in self:
            if rec.code and rec.code in ['ticket', 'leave'] and (rec.sudo().employee_id.country_id.code in ['QA', 'QD']):
                rec.display_airport_info = False
            elif rec.code and rec.code == 'ticket':
                rec.display_airport_info = True
            else:
                rec.display_airport_info = False

    @api.depends('education_allowance_ids')
    def _get_total_requested(self):
        for allowance in self:
            total_requested_amount = 0
            if allowance.education_allowance_ids:
                for dep in allowance.education_allowance_ids:
                    if dep.requested_amount:
                        total_requested_amount += dep.requested_amount
            allowance.total_requested_amount = total_requested_amount

    @api.depends('education_allowance_ids')
    def _get_total_balance(self):
        for allowance in self:
            total_balance = 0
            if allowance.education_allowance_ids:
                for dep in allowance.education_allowance_ids:
                    if dep.balance:
                        total_balance += dep.balance
            allowance.total_balance = total_balance

    @api.constrains('education_allowance_ids')
    def _check_balance_education_allowance(self):
        if self.education_allowance_ids and self.sudo().employee_id:
            for line in self.education_allowance_ids:
                if line.requested_amount > line.balance:
                    raise ValidationError(
                        _(f"Requested amount of dependent {line.dependent_id.name} more than "
                          f" balance {line.balance}"))

    @api.constrains('education_allowance_ids')
    def _check_number_of_dependents(self):
        for rec in self:
            if rec.education_allowance_ids and rec.sudo().employee_id:
                if len(rec.education_allowance_ids) > 3 and rec.sudo().employee_id.country_id.code != 'QA':
                    raise ValidationError(
                        _(f"Number of dependents should not exceed 3"))

    # @api.constrains('education_allowance_ids')
    # def _check_requested_education_allowance(self):
    #     if self.education_allowance_ids and self.sudo().employee_id:
    #         payscale = self.sudo().employee_id.contract_id.payscale_id
    #         eligible_amount = payscale.education_allowance
    #         total_requested_amount = 0
    #         for education_allowance_line in self.education_allowance_ids:
    #             if education_allowance_line.requested_amount:
    #                 total_requested_amount += education_allowance_line.requested_amount
    #         if eligible_amount:
    #             if total_requested_amount > eligible_amount:
    #                 raise ValidationError(
    #                     _("Total requested amount in allowance lines shouldn't exceed Eligible amount"))

    @api.constrains('education_allowance_ids')
    def _check_attachments_education_allowance(self):
        if not self.is_created_by_script and self.education_allowance_ids and self.sudo().employee_id:
            for education_allowance_line in self.education_allowance_ids:
                if not education_allowance_line.invoice_attachments:
                    raise ValidationError(_("Please add a one attachment in allowance lines"))

    @api.constrains('education_allowance_ids')
    def _check_dependents(self):
        if self.education_allowance_ids:
            for child in self.sudo().employee_id.emp_children_ids:
                if self.id:
                    education_allowance_line = self.env['education.allowance.line'].search([
                        ('dependent_id', '=', child.id),
                        ('allowance_request_id', '=', self.id)
                    ])
                    if len(education_allowance_line) > 1:
                        raise ValidationError(_('Duplicate same child in allowance lines'
                                                'Please remove duplicate child'))

    @api.constrains('allowance_type', 'academic_id', 'education_allowance_ids')
    def _check_education_allowances_mandatory(self):
        if self.allowance_type and self.academic_id:
            if self.allowance_type.code == 'education':
                if not self.education_allowance_ids:
                    raise ValidationError(_('Must be enter a one line of dependents'))

    # @api.constrains('education_allowance_ids')
    # def _check_invoice_number(self):
    #     for rec in self:
    #         if rec.education_allowance_ids:
    #             invoice_numbers = rec.education_allowance_ids.mapped('invoice_number')
    #             for number in invoice_numbers:
    #                 if number and invoice_numbers.count(number) > 1:
    #                     raise ValidationError(_('Duplicate same invoice number in allowance lines'
    #                                             ' Please remove duplicate invoice number'))

    @api.onchange('employee_id', 'allowance_type')
    def _get_ticket_leave_domain(self):
        for allowance in self:
            if allowance.sudo().employee_id:
                leaves = self.env['hr.leave'].search([
                    ('employee_id', '=', allowance.sudo().employee_id.id),
                    ('state', '=', 'validate'),
                    ('holiday_status_id.is_annual', '=', True)])
                return {'domain': {'ticket_leave_id': [('id', 'in', leaves.ids)]}}

    @api.constrains('airport_id', 'allowance_type')
    @api.onchange('airport_id', 'allowance_type')
    def _check_airport(self):
        for rec in self:
            if rec.sudo().employee_id:
                if not rec.airport_id and rec.allowance_type.code in ['ticket'] \
                        and not (rec.sudo().employee_id.country_id.code in ['QA', 'QD']):
                    raise ValidationError(_("Please, add an airport in the Employee's Contract"))

    # @api.onchange('employee_id', 'allowance_type', 'academic_id', 'eligible_amount', 'requested_amount')
    # def _get_remaining_amount(self):
    #     if self.sudo().employee_id and self.allowance_type:
    #         education_request = self.env['allowance.request'].search([('employee_id', '=', self.sudo().employee_id.id),
    #                                                                   ('academic_id', '=', self.academic_id.id),
    #                                                                   ('state', 'not in', ['refused', 'canceled'])
    #                                                                   ])
    #         if education_request:
    #             total_requested_amount = sum(education_request.mapped('requested_amount'))
    #             self.remaining_amount = self.eligible_amount - total_requested_amount - self.requested_amount
    #         else:
    #             if self.requested_amount:
    #                 self.remaining_amount = self.eligible_amount - self.requested_amount
    #             else:
    #                 self.remaining_amount = self.eligible_amount

    @api.constrains('employee_id', 'employee_id.probation_date')
    def _check_probation_date(self):
        if not (self.sudo().employee_id.probation_date and self.sudo().employee_id.probation_date < date.today()):
            raise ValidationError(_('the employee is not eligible for allowance request'
                                    ' check probation date of this employee'))

    @api.model
    def create(self, values):
        seq = ''
        if 'allowance_type' in values:
            type = self.env['allowance.type'].browse(values['allowance_type'])
            if type.code == 'education':
                seq = 'edu.allowance.request.seq'
            elif type.code == 'furniture':
                seq = 'fur.allowance.request.seq'
            elif type.code == 'maintenance':
                seq = 'fur.mai.allowance.request.seq'
            elif type.code == 'ticket':
                seq = 'tic.allowance.request.seq'
            elif type.code == 'leave':
                seq = 'leave.allowance.request.seq'
            elif type.code == 'mobilization':
                seq = 'mob.allowance.request.seq'
            elif type.code == 'trip':
                seq = 'trip.allowance.request.seq'
            elif type.code == 'eosb':
                seq = 'eosb.allowance.request.seq'
            values['name'] = self.env['ir.sequence'].get(seq) or ' '
        return super(AllowanceRequest, self).create(values)

    def unlink(self):
        if any(self.filtered(lambda allowance: allowance.state not in ('draft', 'canceled', 'approved'))):
            raise UserError(_('You cannot delete a Request which is not draft or cancelled!'))
        return super(AllowanceRequest, self).unlink()

    @api.constrains('eligible_amount', 'requested_amount')
    def _check_values(self):
        for rec in self:
            if rec.allowance_type.code == 'education' and rec.requested_amount > rec.eligible_amount:
                raise ValidationError(_("Requested amount shouldn't exceed Eligible amount"))

    # @api.constrains('employee_id', 'academic_id', 'requested_amount')
    # def _check_education_request(self):
    #     if self.allowance_type.code == 'education':
    #         education_request = self.env['allowance.request'].search([('employee_id', '=', self.sudo().employee_id.id),
    #                                                                   ('id', '!=', self.id),
    #                                                                   ('academic_id', '=', self.academic_id.id),
    #                                                                   ('state', 'not in', ['refused', 'canceled'])
    #                                                                   ])
    #         total_requested_amount = sum(education_request.mapped('requested_amount'))
    #         total_requested_amount += self.requested_amount
    #         if total_requested_amount > self.eligible_amount:
    #             raise ValidationError(_("Total Requested amount shouldn't exceed Eligible"
    #                                     " amount within the same academic year"))
    # if len(education_request) >= 1:
    #     raise ValidationError(_("Education Requested must be in another  Academic Year"))

    @api.constrains('employee_id', 'allowance_type')
    def _check_furniture_request(self):
        if self.allowance_type.code == 'furniture':
            furniture_request = self.env['allowance.request'].search([('employee_id', '=', self.sudo().employee_id.id),
                                                                      ('id', '!=', self.id),
                                                                      ('allowance_type.code', '=', 'furniture')])
            if len(furniture_request) >= 1:
                raise ValidationError(_("furniture Requested is exist"))

    @api.constrains('employee_id', 'allowance_type')
    def _check_mobilization_request(self):
        if self.allowance_type.code == 'mobilization':
            furniture_request = self.env['allowance.request'].search([('employee_id', '=', self.sudo().employee_id.id),
                                                                      ('id', '!=', self.id),
                                                                      ('allowance_type.code', '=', 'mobilization')])
            if len(furniture_request) >= 1:
                raise ValidationError(_("Mobilization Requested is exist"))

    @api.constrains('employee_id', 'allowance_type')
    def _check_ticket_request(self):
        for rec in self:
            if not rec.sudo().employee_id:
                return
            if rec.allowance_type.code == 'ticket' and rec.payment_date:
                ticket_request = rec.env['allowance.request'].search([
                    ('employee_id', '=', rec.sudo().employee_id.id),
                    ('id', '!=', rec.id),
                    ('allowance_type.code', '=', 'ticket'),
                    ('state', 'not in', ['canceled', 'refused']),
                ]).filtered(
                    lambda x: x.payment_date.year == rec.payment_date.year)

                if len(ticket_request) >= 1:
                    raise ValidationError(
                        _("The employee has maximum one ticket yearly and ticket allowance requests already exist"))
            elif rec.allowance_type.code == 'leave':
                leave_request = rec.env['allowance.request'].search([
                    ('employee_id', '=', rec.sudo().employee_id.id),
                    ('id', '!=', rec.id),
                    ('allowance_type.code', '=', 'leave'),
                    ('state', 'not in', ['canceled', 'refused']),
                ]).filtered(
                    lambda x: x.payment_date and x.payment_date.year == rec.payment_date.year)

                if len(leave_request) >= 1:
                    raise ValidationError(
                        _("The employee has maximum one leave yearly and leave allowance requests already exist"))

    @api.constrains('employee_id', 'allowance_type')
    def _check_employee_sponsor(self):
        for rec in self:
            if rec.sudo().employee_id and rec.sudo().employee_id.sponsor:
                if rec.sudo().employee_id.sponsor.id not in rec.allowance_type.sponsor_ids.ids:
                    raise ValidationError(
                        _(f"For this allowance type the employee should be under sponsorship of {rec.allowance_type.sponsor_ids.mapped('name')}"))

    def get_depreciation_line(self, final_approved_date):
        for rec in self:
            amount = 0.0
            if rec.allowance_type.code == 'maintenance' and rec.approved_amount:

                amount = rec.approved_amount / rec.allowance_type.num_of_months
            else:
                amount = rec.eligible_amount / rec.allowance_type.num_of_months
            num_of_months = rec.allowance_type.num_of_months
            # line =[]
            # for rec in range(self.allowance_type.num_of_months):
            #     result = {
            #         "date":5,
            #         "amount":amount,
            #         "allowance_id":self.id,
            #     }
            for line in rec:
                line.depreciation_line.unlink()
                if rec.allowance_type.code == 'furniture' or 'maintenance':
                    date_start = rec.effective_date
                else:
                    date_start = final_approved_date
                if date_start:
                    for i in range(1, num_of_months + 1):
                        rec.env['allowance.depreciation'].create({
                            'date': date_start,
                            'amount': amount,
                            "allowance_id": line.id
                        })
                        date_start = date_start + relativedelta(months=1)
        return True

    def action_refuse(self):
        return self.write({'state': 'refused'})

    def action_confirm(self):
        for rec in self:
            if not rec.approved_amount:
                rec.approved_amount = rec.eligible_amount
            if rec.allowance_type.code == 'ticket' and not rec.ticket_leave_id:
                raise ValidationError(_('You must set the leave on ticket allowance'))
            rec.state = 'confirmed'

    def action_approve(self):
        self.final_approve_date = fields.Date.today()
        if self.allowance_type.num_of_months:
            self.get_depreciation_line(self.final_approve_date)
        if self.state == 'first_approved':
            self.write({'state': 'approved'})

    @api.model
    def action_server_approved_allowance(self):
        for rec in self:
            if rec.state == 'first_approved':
                rec.final_approve_date = fields.Date.today()
                if rec.allowance_type.num_of_months:
                    rec.get_depreciation_line(rec.final_approve_date)
                rec.write({'state': 'approved'})

    def action_paid(self):
        if self.state in ['first_approved', 'approved']:
            self.write({'state': 'paid'})

    def update_activity(self, users):
        activity_to_do = self.env.ref('hr_allowance_request.mail_act_allowance_approval').id
        model_id = self.env['ir.model']._get('allowance.request').id
        activity = self.env['mail.activity']
        if self.state in ['confirmed', 'first_approved']:
            for user in users:
                if user:
                    act_dct = {
                        'activity_type_id': activity_to_do,
                        'note': "للتكرم بمراجعة طلب العلاوة على نظام موارد.",
                        'user_id': user.id,
                        'res_id': self.id,
                        'res_model_id': model_id,
                        'date_deadline': datetime.today().date()
                    }
                    activity.sudo().create(act_dct)
        elif self.state == 'approved':
            activity_id = self.env['mail.activity'].search(
                [('res_id', '=', self.id), ('user_id', 'in', users.ids),
                 ('activity_type_id', '=', activity_to_do)])
            activity_id.action_feedback(feedback='Approved')
            other_activity_ids = self.env['mail.activity'].search(
                [('res_id', '=', self.id),
                 ('activity_type_id', '=', activity_to_do)])
            other_activity_ids.unlink()

    def send_notification_of_allowance_request(self, users):
        template = self.env.ref('hr_allowance_request.mail_template_send_notification_of_allowance_request',
                                raise_if_not_found=False)
        if users and template:
            partner_to = [str(user.partner_id.id) for user in users if users]
            if partner_to:
                user_tz = self.env.user.partner_id.tz or 'Africa/Nairobi'
                create_date = timezone('UTC').localize(self.create_date).astimezone(timezone(user_tz))
                allowance_approval_state = 'First Approval' if self.state == 'confirmed' else 'Second Approval'
                template.sudo().with_context(
                    partner_to=','.join(partner_to), create_date=create_date,
                    allowance_approval_state=allowance_approval_state).send_mail(self.id, force_send=True)

                # notification_ids = [(0, 0,
                #                      {
                #                          'res_partner_id': user.partner_id.id,
                #                          'notification_type': 'inbox'
                #                      }
                #                      ) for user in users if users]
                #
                # self.env['mail.message'].create({
                #     'message_type': "notification",
                #     'body': f"Allowance Request {self.name} is  Submitted To {allowance_approval_state}",
                #     'partner_ids': [(4, user.partner_id.id) for user in users if users],
                #     'model': self._name,
                #     'res_id': self.id,
                #     'notification_ids': notification_ids,
                #     'author_id': self.env.user.partner_id and self.env.user.partner_id.id
                # })

    def action_first_approve(self):
        for rec in self:
            if not rec.approved_amount:
                rec.approved_amount = rec.eligible_amount
            rec.state = 'first_approved'
            second_approve_users = self.env.ref('hr_allowance_request.group_allowance_second_approval').users
            # stop send email from cro job on case maintenance allowance
            if not self.env.context.get('create_from_cron'):
                pass
                # rec.send_notification_of_allowance_request(second_approve_users)
                # if rec.activity_ids:
                #     rec.activity_ids.action_done()
                # rec.update_activity(second_approve_users)

    @api.model
    def action_server_first_approved(self):
        for rec in self:
            if rec.state == 'confirmed':
                if not rec.approved_amount:
                    rec.approved_amount = rec.eligible_amount
                rec.state = 'first_approved'
                # second_approve_users = self.env.ref(
                #     'hr_allowance_request.group_allowance_second_approval').users
                # # rec.send_notification_of_allowance_request(second_approve_users)
                # if rec.activity_ids:
                #     rec.activity_ids.action_done()
                # rec.update_activity(second_approve_users)

    def get_url(self):
        self.ensure_one()
        get_url = str(self.env['ir.config_parameter'].sudo().search(
            [('key', '=', 'web.base.url')]).value) + '/web?#id=' + str(
            self.id) + '&view_type=form&model=allowance.request&action=' + str(
            self.env.ref('hr_allowance_request.act_hr_employee_allowance_request').id) + ' & menu_id = '
        return get_url

    def action_cancel(self):
        self.write({'state': 'canceled'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def get_year(self):
        current_year = datetime.now().year
        if datetime.now().month > 6:
            return current_year + 1
        else:
            return current_year

    @api.onchange('employee_id', 'allowance_type')
    def change_effective_date(self):
        for rec in self:
            if rec.sudo().employee_id and rec.allowance_type.code == 'furniture':
                rec.effective_date = rec.sudo().employee_id.joining_date

    @api.onchange('marital', 'country_id', 'employee_id')
    def allowance_type_domain(self):
        current_user = self.env.user
        code = ['furniture', 'trip']
        # if self.country_id.code == 'QA' and self.marital == 'single':
        #     code
        if self.country_id.code == 'QA':
            code += ['leave']
        else:
            code += ['ticket']
        # elif self.country_id.code == 'QA' and self.marital != 'single':
        if self.marital != 'single':
            code += ['education']
        if self.country_id.code != 'QA':
            code += ['mobilization']
        if self.country_id.code == 'QA':
            code += ['eosb']
        if current_user.has_group('hr.group_hr_manager'):
            code += ['maintenance']
        if code:
            domain = {'domain': {'allowance_type': [('code', 'in', code)]}}
        return domain

    def _get_current_user(self):
        for rec in self:
            rec.user_id = rec.env.user

    # @api.onchange('eligible_amount')
    # def get_requested_amount(self):
    #     if self.eligible_amount:
    #         self.requested_amount = self.eligible_amount

    @api.depends('allowance_line')
    def _get_total_allowance_line(self):
        for rec in self:
            if rec.allowance_line:
                rec.total_collected = sum(line.amount for line in rec.allowance_line)
            else:
                rec.total_collected = 0

    @api.depends('employee_id')
    def get_employee_dependants(self):
        for rec in self:
            total_child = rec.env['hr.emp.child'].search([('emp_id', '=', rec.sudo().employee_id.id)])
            date_jun = datetime(rec.get_year(), 6, 30, 0, 0, 0).date()
            eligible_dependent = 0
            if total_child:
                rec.total_dependent = len(total_child)
            else:
                rec.total_dependent = 0
            for child in total_child:
                if child.date_of_birth:
                    if relativedelta(date_jun, child.date_of_birth).years <= 18:
                        eligible_dependent += 1
            if eligible_dependent > 3:
                eligible_dependent = 3
            rec.eligible_dependent = eligible_dependent

    def _number_of_dependants(self):
        for rec in self:
            has_spouse = False
            dependents_ages = []
            spouse_name = ""
            # dependents_ages = rec.sudo().employee_id.emp_children_ids.sorted(key=lambda x: x.age, reverse=True).mapped('age')
            if not rec.parent:
                dependents = rec.sudo().employee_id.emp_children_ids.sorted(key=lambda x: x.age, reverse=True)
            else:
                dependents = rec.emp_child.mapped('dependent_name').sorted(key=lambda x: x.age, reverse=True)
            current_contract = rec.env['hr.contract'].sudo().search([
                ('state', '=', 'open'),
                ('employee_id', '=', rec.sudo().employee_id.id)], limit=1)
            employee_contract = rec.sudo().employee_id.contract_id or current_contract

            age_from = rec.allowance_type.age_from
            age_to = rec.allowance_type.age_to
            number_of_dependent = employee_contract.payscale_id.number_of_dependent
            for dependent in dependents:
                if dependent.relation != 'spouse' and rec.no_dependent is False:
                    if age_from > dependent.age or dependent.age > age_to:
                        continue
                    dependents_ages.append({'age': dependent.age, 'name': dependent.name})
                elif dependent.relation == 'spouse':
                    spouse_name = dependent.name
                    has_spouse = True
            if len(dependents_ages) >= number_of_dependent:
                dependents_ages = dependents_ages[0:number_of_dependent]
            ages = list(map(lambda age: age['age'], dependents_ages))
            count_child = 0
            count_adult = 0
            count_infant = 0
            names_adult = []
            names_child = []
            names_infant = []
            adult_fare_age_from = rec.allowance_type.adult_fare_age_from
            adult_fare_age_to = rec.allowance_type.adult_fare_age_to
            child_fare_age_from = rec.allowance_type.child_fare_age_from
            child_fare_age_to = rec.allowance_type.child_fare_age_to
            infant_fare_age_from = rec.allowance_type.infant_fare_age_from
            infant_fare_age_to = rec.allowance_type.infant_fare_age_to
            if not rec.parent:
                for dep in dependents_ages:
                    if adult_fare_age_from < dep.get('age') <= adult_fare_age_to:
                        count_adult += 1
                        names_adult.append(dep.get('name'))
                    elif child_fare_age_from < dep.get('age') <= child_fare_age_to:
                        count_child += 1
                        names_child.append(dep.get('name'))
                    elif infant_fare_age_from < dep.get('age') <= infant_fare_age_to:
                        count_infant += 1
                        names_infant.append(dep.get('name'))
                if has_spouse:
                    rec.count_dependants_note = f'Employee: {rec.sudo().employee_id.name} has spouse {spouse_name}, {count_adult} Adult(s),\n' \
                                                f'{count_child} child/children, {count_infant} infant(s)'
                else:
                    rec.count_dependants_note = f'Employee: {rec.sudo().employee_id.name} has {count_adult} Adult(s),\n' \
                                                f'{count_child} child/children, {count_infant} infant(s)'

            return has_spouse, ages

    def _get_working_days(self, start_date, end_date):
        if start_date and end_date:
            # get list of all days

            all_days = (start_date + timedelta(x) for x in range((end_date - start_date).days + 1))

            # filter business days
            # weekday from 0 to 4. 0 is monday adn 4 is friday
            # increase counter in each iteration if it is a weekday

            count = sum(1 for day in all_days if day.weekday() in [0, 1, 2, 3, 6])
            return count

    def _get_ticket_allowance(self):
        for rec in self:
            eligible_amount = 0.0
            if rec.sudo().employee_id and not rec.parent:
                eligible_amount = 0.0
                today = date.today()
                joining_date = rec.sudo().employee_id.joining_date
                new_joiner = joining_date.year == today.year
                adult_fare_age_from = rec.allowance_type.adult_fare_age_from
                adult_fare_age_to = rec.allowance_type.adult_fare_age_to
                child_fare_age_from = rec.allowance_type.child_fare_age_from
                child_fare_age_to = rec.allowance_type.child_fare_age_to
                infant_fare_age_from = rec.allowance_type.infant_fare_age_from
                infant_fare_age_to = rec.allowance_type.infant_fare_age_to
                # last_date = datetime(today.year, 12, 31, 0, 0, 0)
                # emp_joining_date = datetime(joining_date.year, joining_date.month, joining_date.day, 0, 0,
                #                             0)
                # balance = 0
                #
                # remaining_working_days = self._get_working_days(emp_joining_date.date(), last_date.date())
                # balance += remaining_working_days / 261
                #
                # # days_diff = ((today - joining_date).days + 1) / 365
                # if rec.sudo().employee_id.country_id and rec.sudo().employee_id.country_id.code == 'QA':
                #     if rec.marital == 'married':
                #         if new_joiner:
                #             eligible_amount = rec.sudo().employee_id.contract_id.wage * 2 * balance
                #         else:
                #             eligible_amount = rec.sudo().employee_id.contract_id.wage * 2
                #     else:
                #         if new_joiner:
                #             eligible_amount = rec.sudo().employee_id.contract_id.wage * balance
                #         else:
                #             eligible_amount = rec.sudo().employee_id.contract_id.wage
                # elif (rec.sudo().employee_id.country_id and rec.sudo().employee_id.country_id.code == 'QD'):
                #     if rec.marital == 'married':
                #         if new_joiner:
                #             eligible_amount = rec.sudo().employee_id.contract_id.wage * balance
                #         else:
                #             eligible_amount = rec.sudo().employee_id.contract_id.wage
                #     else:
                #         if new_joiner:
                #             eligible_amount = rec.sudo().employee_id.contract_id.wage * 0.5 * balance
                #         else:
                #             eligible_amount = rec.sudo().employee_id.contract_id.wage * 0.5
                # else:
                if rec.marital == 'married':
                    has_spouse, ages = rec._number_of_dependants()
                    count_adult = 0
                    count_child = 0
                    count_infant = 0
                    if new_joiner:
                        for age in ages:
                            if adult_fare_age_from < age <= adult_fare_age_to:
                                eligible_amount += rec.adult_fare
                                count_adult += 1
                            elif child_fare_age_from < age <= child_fare_age_to:
                                eligible_amount += rec.child_fare
                                count_child += 1
                            elif infant_fare_age_from < age <= infant_fare_age_to:
                                eligible_amount += rec.infant_fare
                                count_infant += 1
                        if has_spouse:
                            if rec.gender == 'male':
                                eligible_amount += 2 * rec.adult_fare
                            elif rec.gender == 'female':
                                eligible_amount += rec.adult_fare
                        else:
                            eligible_amount += rec.adult_fare
                    else:
                        for age in ages:
                            if adult_fare_age_from < age <= adult_fare_age_to:
                                eligible_amount += rec.adult_fare
                                count_adult += 1
                            elif child_fare_age_from < age <= child_fare_age_to:
                                eligible_amount += rec.child_fare
                                count_child += 1
                            elif infant_fare_age_from < age <= infant_fare_age_to:
                                eligible_amount += rec.infant_fare
                                count_infant += 1
                        if has_spouse:
                            if rec.gender == 'male':
                                eligible_amount += 2 * rec.adult_fare
                            elif rec.gender == 'female':
                                eligible_amount += rec.adult_fare
                        else:
                            eligible_amount += rec.adult_fare
                    # rec.count_dependants_note = f"Number of Adults: {count_adult}\nNumber of Child: {count_child}\n" \
                    #                             f"Number of Infant: {count_infant}\n"
                else:
                    if new_joiner:
                        eligible_amount = rec.adult_fare
                    else:
                        eligible_amount = rec.adult_fare
            return round(eligible_amount, 2)

    def _get_eligible_leave_allowance(self):
        for rec in self:
            current_contract = rec.env['hr.contract'].sudo().search([
                ('state', '=', 'open'),
                ('employee_id', '=', rec.sudo().employee_id.id)], limit=1)
            employee_contract = rec.sudo().employee_id.contract_id or current_contract
            if rec.sudo().employee_id:
                eligible_amount = 0.0
                if not (rec.sudo().employee_id.country_id and
                        rec.sudo().employee_id.country_id.code == 'QA' and
                        rec.allowance_type.total_days_in_year):
                    return eligible_amount
                today = date.today()
                joining_date = rec.sudo().employee_id.joining_date
                if joining_date > today:
                    return eligible_amount
                difference = (today - joining_date).days
                leave_allowance_amount = employee_contract.payscale_id.leave_allowance_factor * employee_contract.wage
                year_relative = int(difference / rec.allowance_type.total_days_in_year)
                day_relative = difference % rec.allowance_type.total_days_in_year
                if year_relative < 1:
                    return eligible_amount
                # elif 1 <= year_relative < 2:
                #     day_amount = leave_allowance_amount / rec.allowance_type.total_days_in_year
                #     eligible_amount = (day_amount * day_relative) + leave_allowance_amount
                else:
                    eligible_amount = leave_allowance_amount

                return round(eligible_amount, 2)

    def _get_education_allowance(self):
        eligible_amount = 0.0
        for dep in self.education_allowance_ids:
            if dep.requested_amount:
                eligible_amount += dep.requested_amount
        return eligible_amount

    def _get_furniture_allowance(self):
        eligible_amount = 0.0
        for rec in self:
            payscale = rec.sudo().employee_id.contract_id.payscale_id
            if payscale:
                eligible_amount = payscale.furniture_allowance
        return eligible_amount

    def _get_furniture_maintenance_allowance(self):
        eligible_amount = 0.0
        payscale = self.sudo().employee_id.contract_id.payscale_id
        if payscale:
            eligible_amount = payscale.furniture_allowance * 0.1
        return eligible_amount

    def _get_mobilization_allowance(self):
        eligible_amount = 0.0
        payscale = self.sudo().employee_id.contract_id.payscale_id
        if payscale:
            eligible_amount = payscale.mobilisation_allowance
        return eligible_amount

    def _get_trip_allowance(self):
        eligible_amount = 0.0

        payscale = self.sudo().employee_id.contract_id.payscale_id
        if payscale:
            delta = (self.end_date - self.start_date)
            number_of_days = abs(delta.days) + 1
            # if self.destination.code in GCC_COUNTRIES_CODES:
            #     eligible_amount = payscale.business_allowance_gulf * number_of_days
            # else:
            eligible_amount = payscale.business_allowance * number_of_days
            if 30 < number_of_days <= 60:
                eligible_amount *= 0.75
            elif 61 <= number_of_days <= 180:
                eligible_amount *= 0.50
        return eligible_amount

    def _get_eosb_allowance(self):
        loan = self.env['hr.loan'].search(
            [('employee_id', '=', self.sudo().employee_id.id), ('is_paid', '=', False), ('state', 'in', ['paid', 'approve'])])
        if not loan:
            return self.sudo().employee_id.total_amount_working_days_no_store * 0.5

        # else:
        #     self.eligible_amount = 0.0
        #     if self._context.get('is_imported'):
        #         self.eligible_amount = 0.0
        #     elif not self.is_imported:
        #         raise ValidationError(_("First pay your loan to get EOSB allowance"))

    @api.depends('employee_id', 'allowance_type', 'marital', 'country_id', 'adult_fare',
                 'child_fare', 'infant_fare', 'start_date', 'end_date', 'destination')
    def _get_eligible_amount(self):
        eligible_amount = 0

        for rec in self:
            if rec.allowance_type.code == 'ticket':
                if rec.sudo().employee_id and not rec.parent:
                    rec.eligible_amount = rec._get_ticket_allowance()
                # elif rec.dependent_id and rec.parent:
                #     rec._get_new_dependants_fares()
            elif rec.allowance_type.code == 'leave':
                rec.eligible_amount = rec._get_eligible_leave_allowance()
            elif rec.allowance_type.code == 'education':
                rec.eligible_amount = rec._get_education_allowance()
            elif rec.allowance_type.code == 'furniture':
                rec.eligible_amount = rec._get_furniture_allowance()
            elif rec.allowance_type.code == 'maintenance':
                rec.eligible_amount = rec._get_furniture_maintenance_allowance()
            elif rec.allowance_type.code == 'trip':
                if rec.start_date and rec.end_date:
                    rec.eligible_amount = rec._get_trip_allowance()
            elif rec.allowance_type.code == 'mobilization':
                rec.eligible_amount = rec._get_mobilization_allowance()
            elif rec.allowance_type.code == 'eosb':
                rec.eligible_amount = rec._get_eosb_allowance()
            else:
                rec.eligible_amount = eligible_amount

    @api.depends('airport_id', 'employee_id', 'allowance_type')
    def _get_fares(self):
        for rec in self:
            if rec.airport_id:
                domain = [('airport_id', '=', rec.airport_id.id)]
                if rec.sudo().employee_id.contract_id.payscale_id.air_ticket_allowance == 'b':
                    domain.append(('travel_class', '=', 'b'))
                elif rec.sudo().employee_id.contract_id.payscale_id.air_ticket_allowance == 'e':
                    domain.append(('travel_class', '=', 'e'))
                fares = rec.env['dependents.fares'].search(domain, order='year desc', limit=1)
                rec.adult_fare = fares.adult_fare
                rec.child_fare = fares.child_fare
                rec.infant_fare = fares.infant_fare
            else:
                rec.adult_fare = 0
                rec.child_fare = 0
                rec.infant_fare = 0

    @api.model
    def auto_create_leave_allowance(self):
        today = date.today()
        leave_allowance_type = self.env['allowance.type'].search([('code', '=', 'leave')], limit=1)
        if not (leave_allowance_type.month and leave_allowance_type.total_days_in_year):
            return
        if int(leave_allowance_type.month) == today.month and today.day == 1:
            employees = self.env['hr.employee'].sudo().search([
                ('country_id.code', '=', 'QA'), ('joining_date', '!=', False),
                ('joining_date', '<', today)])
            eligible_employees = employees. \
                filtered(lambda employee:
                         (today - employee.sudo().joining_date).days >
                         leave_allowance_type.total_days_in_year)
            for employee in eligible_employees:
                employee.sudo()._employee_auto_create_leave_allowance(today, leave_allowance_type)

    def action_add_new_dependent(self):
        for rec in self:
            if rec.sudo().employee_id:
                search_view_ref = self.env.ref('hr_allowance_request.view_allowance_request_search_form', False)
                form_view_ref = self.env.ref('hr_allowance_request.allowance_request_form_view', False)
                # tree_view_ref = self.env.ref('hr_allowance_request.allowance_request_tree_view', False)
                type = self.env['allowance.type'].search([('code', '=', 'ticket')])
                return {
                    'name': 'Allowances',
                    'res_model': 'allowance.request',
                    'type': 'ir.actions.act_window',
                    'views': [(form_view_ref.id, 'form')],
                    'search_view_id': search_view_ref and [search_view_ref.id],
                    'target': 'current',
                    'context': {'default_parent': self.id, 'default_employee_id': self.sudo().employee_id.id,
                                'default_allowance_type': type.id}
                }

    def action_open_child_allowances(self):
        self.ensure_one()
        # invoices = self.env['membership.membership_line'].search([('partner', '=', self.partner_id.id)]).mapped(
        #     'account_invoice_id').ids
        child = self.env['allowance.request'].sudo().search([('parent', '=', self.id)])
        search_view_ref = self.env.sudo().ref('hr_allowance_request.view_allowance_request_search_form', False)
        form_view_ref = self.env.sudo().ref('hr_allowance_request.allowance_request_form_view', False)
        tree_view_ref = self.env.sudo().ref('hr_allowance_request.allowance_request_tree_view', False)

        return {
            'name': 'Allowances',
            'res_model': 'allowance.request',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'views': [(tree_view_ref.id, 'tree'), (form_view_ref.id, 'form')],
            'search_view_id': search_view_ref and [search_view_ref.id],
            "domain": [('id', 'in', child.ids)],
        }

    @api.onchange('dependent_id', 'effective_date')
    def _get_new_dependants_fares(self):
        for rec in self:
            if rec.parent and rec.dependent_id:
                eligible_amount = 0.0
                today = date.today()
                joining_date = rec.sudo().employee_id.joining_date
                effective_date = rec.effective_date
                new_joiner = joining_date.year == today.year
                last_date = datetime(today.year, 12, 31, 0, 0, 0).date()
                # request_date_time = datetime(request_date.year, request_date.month, request_date.day, 0, 0,
                #                             0)
                balance = 0

                if rec.marital == 'married':
                    age = rec.dependent_id.age
                    remaining_working_days = self.sudo().employee_id.resource_calendar_id.get_working_days(effective_date,
                                                                                                    last_date)
                    balance += remaining_working_days / 261

                    if new_joiner:

                        if 12 < age:
                            eligible_amount += rec.adult_fare * balance
                        elif 2 < age <= 12:
                            eligible_amount += rec.child_fare * balance
                        elif 0 < age <= 2:
                            eligible_amount += rec.infant_fare * balance
                        else:
                            eligible_amount += rec.adult_fare * balance
                    else:
                        if 12 < age:
                            eligible_amount += rec.adult_fare * balance
                        elif 2 < age <= 12:
                            eligible_amount += rec.child_fare * balance
                        elif 0 < age <= 2:
                            eligible_amount += rec.infant_fare * balance

                rec.eligible_amount = round(eligible_amount, 2)

    @api.model
    def action_generate_allowance_report(self):
        rec = self.filtered(lambda x: x.state == 'approved')
        if rec:
            data = {
                'allowances': rec.ids,
            }
            return self.env.ref('hr_allowance_request.action_allowance_request_xlsx_report').report_action(self,
                                                                                                           data=data)
        else:
            raise UserError(_('Please, select records with second approval.'))

    @api.model
    def action_mass_paid_allowance(self):
        for rec in self:
            if rec.state == 'approved':
                self.write({'state': 'paid'})


class InstallmentLine(models.Model):
    _name = "allowance.request.line"
    _description = "Installment Line"

    date = fields.Date(string="Payment Date", required=True, help="Date of the payment")
    amount = fields.Float(string="Amount", required=True, help="Amount")
    allowance_id = fields.Many2one(comodel_name='allowance.request', string='Allowance_id', required=False)
    ref = fields.Char('Ref')


class EducationAllowanceLines(models.Model):
    _name = 'education.allowance.line'

    allowance_request_id = fields.Many2one('allowance.request', ondelete='cascade')
    dependent_id = fields.Many2one('hr.emp.child', required=True, copy=False)
    eligible_amount = fields.Float('Eligible Amount', copy=False, default=0.0, compute="_get_eligible_amount")
    requested_amount = fields.Float('Requested Amount', required=True, copy=False)
    balance = fields.Float('Balance', copy=False, readonly=True)
    invoice_number = fields.Char('Invoice Number', copy=False)
    invoice_attachments = fields.Many2many('ir.attachment', string="Attachments",
                                           copy=False, required=True)

    dependent_id_domain = fields.Char('dependent_id_domain', compute="_get_dependent_id_domain")

    def get_year(self):
        current_year = datetime.now().year
        if datetime.now().month > 6:
            return current_year + 1
        else:
            return current_year

    @api.depends('dependent_id')
    def _get_dependent_id_domain(self):
        for dep in self:
            depends = []
            date_academic = dep.allowance_request_id.academic_id.start_date
            emp_children_ids = dep.allowance_request_id.sudo().employee_id.emp_children_ids
            date_jun = datetime(dep.get_year(), 6, 30).date()
            edu_requests = dep.env['allowance.request'].sudo().search(
                [('employee_id', '=', dep.allowance_request_id.sudo().employee_id.id),
                 ('academic_id', '=', dep.allowance_request_id.academic_id.id)]).mapped(
                'education_allowance_ids.dependent_id.id')
            exists_dep = dep.allowance_request_id.education_allowance_ids.mapped('dependent_id').ids
            if emp_children_ids:
                for child in emp_children_ids:
                    if child.date_of_birth:
                        if dep.allowance_request_id.allowance_type:
                            # if 3 < (date_jun - child.date_of_birth).days / 365 <= 18:
                            if dep.allowance_request_id.allowance_type.age_from < (
                                    date_jun - child.date_of_birth).days / 365 <= dep.allowance_request_id.allowance_type.age_to:
                                if child.id in exists_dep:
                                    continue
                                if len(edu_requests) == 3:
                                    if child.id not in edu_requests:
                                        continue

                                depends.append(child.id)
                            # elif date_academic and 3 <= (date_academic - child.date_of_birth).days / 365 <= 18:
                            elif date_academic and dep.allowance_request_id.allowance_type.age_from <= (
                                    date_academic - child.date_of_birth).days / 365 <= dep.allowance_request_id.allowance_type.age_to:
                                if child.id in exists_dep:
                                    continue
                                if len(edu_requests) == 3:
                                    if child.id not in edu_requests:
                                        continue
                                depends.append(child.id)
            dep.dependent_id_domain = json.dumps([
                ('id', 'in', depends), ('relation', '=', 'child')
            ])

    @api.depends('dependent_id')
    def _get_eligible_amount(self):
        for dep in self:
            if dep.dependent_id:
                payscale = dep.dependent_id.emp_id.contract_id.payscale_id
                if payscale:
                    dep.eligible_amount = payscale.education_allowance
                else:
                    dep.eligible_amount = 0
            else:
                dep.eligible_amount = 0

    @api.onchange('dependent_id', 'eligible_amount', 'requested_amount')
    def get_balance(self):
        for dep in self:
            if dep.allowance_request_id.sudo().employee_id and dep.dependent_id:
                payscale = dep.dependent_id.emp_id.contract_id.payscale_id
                if payscale:
                    eligible_amount = payscale.education_allowance
                else:
                    eligible_amount = 0
                education_requests_lines = self.env['education.allowance.line'].search([
                    ('allowance_request_id.employee_id', '=', dep.allowance_request_id.employee_id.id),
                    ('allowance_request_id.state', 'not in', ['refused', 'canceled']),
                    ('allowance_request_id.code', '=', 'education'),
                    ('allowance_request_id.academic_id', '=', dep.allowance_request_id.academic_id.id),
                    # ('dependent_id', 'not in', dep.dependent_id.ids)
                ])
                # education_requests_lines += dep.allowance_request_id.education_allowance_ids.\
                #     filtered(lambda x: x.dependent_id.id != dep.dependent_id.id)
                append_lines = self.env['education.allowance.line']
                for dep_line in dep.allowance_request_id.education_allowance_ids.filtered(lambda x: x.dependent_id):
                    if dep_line._origin.id in education_requests_lines.ids:
                        continue
                    append_lines += dep_line.filtered(lambda x: x.dependent_id and x.dependent_id != dep.dependent_id)
                if append_lines:
                    education_requests_lines += append_lines
                # education_requests += dep.allowance_request_id
                total_requested_amount = 0
                if education_requests_lines:
                    for education_request_line in education_requests_lines:
                        # for dependent in education_request.education_allowance_ids:
                        # if dependent.dependent_id.id == dep.dependent_id.id:
                        if education_request_line.requested_amount:
                            total_requested_amount += education_request_line.requested_amount
                if education_requests_lines and total_requested_amount:
                    dep.balance = eligible_amount - total_requested_amount
                else:
                    dep.balance = eligible_amount
            else:
                dep.balance = 0

    @api.constrains('balance')
    def _check_balance(self):
        for dep in self:
            if dep.balance < 0:
                raise ValidationError(_('Not allowed request because balance less than 0'))

    @api.constrains('dependent_id', 'invoice_number')
    def dependent_invoice_number_constraints(self):
        for rec in self:
            dep_edu_lines = rec.search([('id', '!=', rec.id)])
            for dep in dep_edu_lines:
                if dep.dependent_id == rec.dependent_id and dep.invoice_number == rec.invoice_number:
                    raise ValidationError('Duplicating same dependent with same invoice number is not allowed!')

    @api.constrains('eligible_amount', 'requested_amount')
    def _check_eligible_amount(self):
        for dep in self:
            if dep.requested_amount > dep.eligible_amount:
                raise ValidationError(_(f"Requested amount shouldn't exceed Eligible"))

    # _sql_constraints = [
    #     ('dependent_invoice_uniq', 'unique(dependent_id,invoice_number)', 'Invoice number should be unique per dependent!'),
    # ]
