# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, Command
from odoo.exceptions import ValidationError, UserError
from datetime import date, datetime
from itertools import groupby
from odoo.tools.misc import format_date
from odoo.tools import float_round, date_utils
from odoo.tools import float_compare, float_is_zero
from dateutil.relativedelta import relativedelta
import math
from odoo.addons.hr_payroll.models.hr_payslip import HrPayslip as c1
import calendar

import inflect


class PayslipInherit(models.Model):
    _name = 'hr.payslip'
    _inherit = ['hr.payslip', 'mail.thread', 'mail.activity.mixin']

    payslip_comments = fields.Text(string='Payslip Comments')
    employee_type = fields.Selection(string='Employee Type', selection=[('fusion_employee', 'Fusion Employee'),
                                                                        ('fos_employee', 'Outsourced Employees'),
                                                                        ('client_employee', 'Client Employee')],
                                     related='employee_id.employee_type')

    # payroll_grade = fields.Selection(
    #     string='Payroll Grade',
    #     selection=[('1', 'Grade 1'),
    #                ('2', 'Grade 2'), ('3', 'Grade 3')],
    #     required=False, related="contract_id.job_id.payroll_grade")

    sponsored_company_id = fields.Many2one('res.partner', related='employee_id.sponsored_company_id',
                                           string="Sponsor Company")
    partner_parent_id = fields.Many2one('res.partner', related='employee_id.partner_parent_id', string='Parent Company')
    payment_id = fields.Many2one(
        comodel_name='account.payment',
        string='Payment',
        required=False)

    expense_transfer_ids = fields.One2many('account.move', 'payslip_id', string="Expense Transfer ")
    expense_transfer_jv = fields.Many2one('account.move', string="Expense Transfer ")
    payslipinvoice_ids = fields.Many2many('account.move', 'invoice_payslip_rel', 'invoice_id', 'payslip_id',
                                          string="Invoices")
    button_show = fields.Selection([('hr', 'hr'), ('finance', 'finance'), ('director', 'director')],
                                   compute='show_button', default=False)
    hr_approver_id = fields.Many2one('res.users', string="Hr Approver")
    finance_approver_id = fields.Many2one('res.users', string="Finance Approver")
    director_approver_id = fields.Many2one('res.users', string="Director Approver")
    outsource_director_approver_id = fields.Many2one('res.users', string="outsource director approver")
    # is_show_hr = fields.Boolean('is Show',compute='show_button' ,default=False,)
    # is_show_finance = fields.Boolean('is Show Finance',compute='show_button',default=False,)
    # is_show_director = fields.Boolean('is Show Director',compute='show_button',default=False,)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('verify', 'Waiting'),
        ('by_manager', 'Approved by Manager'),
        ('by_hr', 'Approved by HR'),
        ('by_finance', 'Approved By Finance'),
        ('paid', 'Paid'),
        ('done', 'Done'),
        ('cancel', 'Rejected'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft',
        help="""* When the payslip is created the status is \'Draft\'
                \n* If the payslip is under verification, the status is \'Waiting\'.
                \n* If the payslip is confirmed then status is set to \'Done\'.
                \n* When user cancel payslip the status is \'Rejected\'.""")
    deduction_reason = fields.Selection([
        ('01', 'Deduction related to working hours'),
        ('02', 'Deduction related to work arrangement '),
        ('03', 'Deduction related to harm or damage'),
        ('04', 'Deduction related to advances payment'),
        ('99', 'Other Reasons'),
    ], string='Deduction Reasons', index=True, readonly=True, copy=False)

    comments = fields.Text(string="Notes/Comments")
    wps_working_days = fields.Integer(string="WPS Working Days")
    is_wps = fields.Boolean(related="employee_id.is_wps")
    is_labor = fields.Boolean(related="employee_id.is_labor")
    fully_invoiced = fields.Boolean('Fully Invoiced', help="All payslip lines are invoiced",
                                    compute="check_payslip_lines")
    is_required_approve = fields.Boolean(string="Is Required Approve", default=False)

    def _create_activity(self, all_users):
        all_users = all_users.sudo()
        activity_to_do = self.env.ref('mail.mail_activity_data_todo').id
        model_id = self.env['ir.model']._get('hr.payslip').id
        activity = self.env['mail.activity']
        for user in all_users:
            if user:
                act_dct = {
                    'activity_type_id': activity_to_do,
                    'note': "kindly check this Payslip Edite's, it's awaiting your approval",
                    'user_id': user.id,
                    'res_id': self.id,
                    'res_model_id': model_id,
                    'date_deadline': datetime.today().date()
                }
                activity.sudo().create(act_dct)

    def action_manager_approve(self):
        self.state = 'by_manager'
        self.is_required_approve = False

    def write(self, vals):
        if 'input_line_ids' in vals:
            vals['is_required_approve'] = True
            object = super(PayslipInherit, self).write(vals)
            self.compute_sheet()
            # users = self.env['res.users'].search([])
            # if users:
            #     for user in users:
            #         if user.has_group("jbm_group_access_right_extended.custom_group_shared_service_manager"):
            #             self._create_activity(user)

            return object
        else:
            return super(PayslipInherit, self).write(vals)

    def get_contract_details(self, payslip, contract, amount):
        if payslip:
            employee_id = self.env['hr.employee'].browse([payslip.employee_id])
            if payslip.date_from.day == 1:
                if payslip.date_from >= contract.date_start:
                    return round(amount)
                else:
                    last_day = calendar.monthrange(contract.date_start.year, contract.date_start.month)[1]
                    last_day_date = datetime(contract.date_start.year, contract.date_start.month, last_day)
                    days = relativedelta(last_day_date, contract.date_start).days + 1
                    line_amount = (amount * employee_id.get_prorata(payslip.date_from)) * days
                    return round(line_amount)
            else:
                days = relativedelta(payslip.date_to, payslip.date_from).days + 1
                line_amount = (amount * employee_id.get_prorata(payslip.date_from)) * days
                return round(line_amount)

    def check_payslip_lines(self):
        lines = self.line_ids.filtered(lambda y: y.amount > 0 and y.salary_rule_id.product_id)
        is_created = self.line_ids.filtered(
            lambda x: x.amount > 0 and x.salary_rule_id.product_id and x.invoice_line_id)

        if len(is_created) == len(lines) and not (len(is_created) == 0 and len(lines) == 0):
            self.fully_invoiced = True
        else:
            self.fully_invoiced = False
        return True

    def show_button(self):
        direct_gp = self.env['res.users'].has_group('ebs_lb_payroll.group_director_payroll_confirm')
        finance_gp = self.env['res.users'].has_group('ebs_lb_payroll.group_finance_payroll_confirm')
        hr_gp = self.env['res.users'].has_group('ebs_lb_payroll.group_payroll_hr')
        # fusion_gp = self.env['res.users'].has_group('ebs_lb_payroll.group_fusion_payroll')
        for rec in self:
            if hr_gp and rec.state == 'verify':
                rec.button_show = 'hr'
            elif finance_gp and rec.state == 'by_hr':
                rec.button_show = 'finance'
            elif direct_gp and rec.state == 'by_finance':
                rec.button_show = 'director'
            else:
                rec.button_show = ''

    def days360(self, start_date, end_date, method_eu=False):
        start_day = start_date.day
        start_month = start_date.month
        start_year = start_date.year
        end_day = end_date.day
        end_month = end_date.month
        end_year = end_date.year

        if (
                start_day == 31 or
                (
                        method_eu is False and
                        start_month == 2 and (
                                start_day == 29 or (
                                start_day == 28 and
                                start_date.is_leap_year is False
                        )
                        )
                )
        ):
            start_day = 30

        if end_day == 31:
            if method_eu is False and start_day != 30:
                end_day = 1

                if end_month == 12:
                    end_year += 1
                    end_month = 1
                else:
                    end_month += 1
            else:
                end_day = 30

        return (
                end_day + end_month * 30 + end_year * 360 -
                start_day - start_month * 30 - start_year * 360)

    def number_to_word(self, number):
        p = inflect.engine()
        return p.number_to_words(int(number)).title()

    def compute_sheet(self):
        payslips = self.filtered(lambda slip: slip.state in ['draft', 'verify'])
        # delete old payslip lines
        payslips.line_ids.unlink()
        for payslip in payslips:
            number = payslip.number or self.env['ir.sequence'].next_by_code('salary.slip')
            lines = [(0, 0, line) for line in payslip._get_payslip_lines()]
            payslip.write({'line_ids': lines, 'number': number, 'state': 'verify', 'compute_date': fields.Date.today()})
        return True

    # def compute_sheet(self):
    #     """Check about Attendance Sheet or Generate it Before Compute Sheet of Payslip """
    #     for rec in self:
    #         attendance_sheet = rec.env['attendance.sheet'].search([
    #             ('employee_id', '=', rec.employee_id.id),
    #             ('date_from', '=', rec.date_from),
    #             ('date_to', '=', rec.date_to),
    #             ('contract_id', '=', rec.contract_id.id)
    #         ], limit=1)
    #         if attendance_sheet:
    #             attendance_sheet.get_attendances()
    #         else:
    #             attendance_sheet = rec.env['attendance.sheet'].create({
    #                 'employee_id': rec.employee_id.id,
    #                 'date_from': rec.date_from,
    #                 'date_to': rec.date_to,
    #                 'contract_id': rec.contract_id.id
    #             }).get_attendances()
    #
    #         res = super(PayslipInherit, rec).compute_sheet()
    #         comment = ""
    #         comment = ""
    #         for line in rec.line_ids.filtered(lambda x: x.category_id.is_deduction and x.amount != 0):
    #             amt = abs(line.amount)
    #             comment += line.name + " " + str(round(amt, 2)) + ','
    #         rec.comments = comment
    #         if rec.comments:
    #             rec.deduction_reason = '99'
    #         else:
    #             rec.deduction_reason = False
    #         if rec.contract_id:
    #             net_salary_line = rec.line_ids.filtered(lambda x: x.category_id.name == 'Net')
    #             basic_with_alw = rec.contract_id.wage + rec.contract_id.accommodation + \
    #                              rec.contract_id.transport_allowance + rec.contract_id.living_allowance + \
    #                              rec.contract_id.other_allowance + rec.contract_id.food_allowance + \
    #                              rec.contract_id.mobile_allowance
    #             if net_salary_line.amount != basic_with_alw:
    #                 net_salary_line.is_check_balance = True
    #         return res

    def get_eos_provision(self, payslip):
        if payslip:
            # difference_in_years = relativedelta(payslip.date_from, payslip.contract_id.date_start).years
            # if difference_in_years < 1:
            #     return str(0)
            # else:
            eos_config_id = self.env['ebs.hr.eos.config'].search(
                [
                    ('start_date', '<=', payslip.date_from),
                    ('end_date', '>=', payslip.date_from)
                ])
            if eos_config_id:
                return (payslip.contract_id.wage * eos_config_id.working_days / eos_config_id.salary_days) / 12
            else:
                return 0

    def calculate_fos_service_fee(self, payslip):
        if payslip:
            employee_id = self.env['hr.employee'].browse(payslip.employee_id)
            entry_date = employee_id.entry_date
            exit_date = employee_id.exit_date
            date = exit_date or entry_date
            if date and date >= payslip.date_from and date <= payslip.date_to:
                if entry_date:
                    last_date = calendar.monthrange(entry_date.year, entry_date.month)[1]
                    return (last_date - entry_date.day + 1) * (employee_id.service_fee / 30)
                if exit_date:
                    return (exit_date.day) * (employee_id.service_fee / 30)
            else:
                return employee_id.service_fee

    def calculate_private_medical_insurance(self, payslip):
        if payslip:
            employee_id = self.env['hr.employee'].browse(payslip.employee_id)
            entry_date = employee_id.entry_date
            exit_date = employee_id.exit_date
            date = exit_date or entry_date
            if date and date >= payslip.date_from and date <= payslip.date_to:
                if entry_date:
                    last_date = calendar.monthrange(entry_date.year, entry_date.month)[1]
                    return (last_date - entry_date.day + 1) * (employee_id.private_medical_insurance / 30)
                if exit_date:
                    return (exit_date.day) * (employee_id.private_medical_insurance / 30)
            else:
                return employee_id.private_medical_insurance

    def calculate_fos_air_ticket_deposit(self, payslip):
        if payslip:
            employee_id = self.env['hr.employee'].browse(payslip.employee_id)
            entry_date = employee_id.entry_date
            exit_date = employee_id.exit_date
            date = exit_date or entry_date
            if date and date >= payslip.date_from and date <= payslip.date_to:
                if entry_date:
                    last_date = calendar.monthrange(entry_date.year, entry_date.month)[1]
                    return (last_date - entry_date.day + 1) * (employee_id.air_ticket_deposit / 30)
                if exit_date:
                    return (exit_date.day) * (employee_id.air_ticket_deposit / 30)
            else:
                return employee_id.air_ticket_deposit

    def calculate_fos_workmen_compensation(self, payslip):
        if payslip:
            employee_id = self.env['hr.employee'].browse(payslip.employee_id)
            entry_date = employee_id.entry_date
            exit_date = employee_id.exit_date
            date = exit_date or entry_date
            if date and date >= payslip.date_from and date <= payslip.date_to:
                if entry_date:
                    last_date = calendar.monthrange(entry_date.year, entry_date.month)[1]
                    return (last_date - entry_date.day + 1) * (employee_id.workmen_compensation / 30)
                if exit_date:
                    return (exit_date.day) * (employee_id.workmen_compensation / 30)
            else:
                return employee_id.workmen_compensation

    def action_show_invoice_line(self):
        self.ensure_one()
        form_view = self.env.ref('account.view_move_form')
        tree_view = self.env.ref('account.view_invoice_tree')
        return {
            'name': _('Invoices'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'res_model': 'account.move',
            'views': [(form_view.id, 'form')],
            'view_id': form_view.id,
            'target': 'current',
            'res_id': self.id,
            'domain': [('id', '=', self.id)]

        }

    def calculateEndOfService(self, payslip, employee):
        contract_list = self.env['hr.contract'].search([('employee_id', '=', employee.id)], order='date_start')
        joining_date = contract_list[0].date_start
        end_date = payslip.contract_id.date_end
        wage = payslip.contract_id.wage
        number_of_days = self.days360(joining_date, end_date)
        eos_amount = ((wage * 21.0) / 365.0) * 12.0 * ((number_of_days / 30.0) / 12.0)
        return eos_amount

    # def calculateAdditionalElements(self, payslip, employee, type_code):
    #     amount = 0.0
    #     elementTypeList = self.env['ebspayroll.additional.element.types'].search([('name', '=', type_code)])
    #     if len(elementTypeList) == 0:
    #         # raise ValidationError(_("There no element type with code %s", (type_code)))
    #         return 0.0
    #     elementType = elementTypeList[0]
    #     elementList = self.env['ebspayroll.additional.elements'].search(
    #         [('type', '=', elementType.id), ('payment_date', '>=', payslip.date_from), ('state', '=', 'confirm'),
    #          ('payment_date', '<=', payslip.date_to)])
    #     if len(elementList) == 0:
    #         # raise ValidationError(_("There no element  with Type %s", (type_code)))
    #         return 0.0
    #
    #     for element in elementList:
    #         for rec in element.lines:
    #             if rec.employee.id == employee.id:
    #                 amount += rec.amount
    #     if elementType.type == 'A':
    #         return amount
    #     else:
    #         return -amount
    def calculateAdditionalElements(self, payslip, employee, type_code):
        amount = 0.0
        elementTypeList = self.env['ebspayroll.additional.element.types'].search([('code', '=', type_code)])
        print('elementTypeList', elementTypeList, type_code)
        if len(elementTypeList) == 0:
            # raise ValidationError(_("There no element type with code %s", (type_code)))
            return 0.0
        elementType = elementTypeList[0]
        elementList = []
        if elementType.recurring:
            elements = self.env['ebspayroll.additional.elements'].search(
                [('type', '=', elementType.id), ('state', '=', 'confirm')])
            for rec in elements:
                if rec.payment_date and rec.to_date and payslip.date_from and payslip.date_to:
                    if (
                            rec.payment_date.month == payslip.date_from.month or rec.to_date.month == payslip.date_to.month or rec.payment_date <= payslip.date_from) and rec.to_date >= payslip.date_to:
                        elementList.append(rec)
                elif rec.payment_date and not rec.to_date:
                    if payslip.date_from and rec.payment_date.month == payslip.date_from.month or rec.payment_date <= payslip.date_from:
                        elementList.append(rec)
        else:
            elementList = self.env['ebspayroll.additional.elements'].search(
                [('type', '=', elementType.id), ('payment_date', '>=', payslip.date_from), ('state', '=', 'confirm'),
                 ('payment_date', '<=', payslip.date_to)])
        if len(elementList) == 0:
            # raise ValidationError(_("There no element  with Type %s", (type_code)))
            return 0.0

        for element in elementList:
            for rec in element.lines:
                if rec.employee.id == employee.id:
                    if elementType.type == 'D':
                        amount += (rec.amount * -1)
                    else:
                        amount += rec.amount
                    break
        return amount

    def CheckAdditionalElements(self, payslip, employee, type_code):
        amount = 0.0
        elementTypeList = self.env['ebspayroll.additional.element.types'].search([('name', '=', type_code)])
        if len(elementTypeList) == 0:
            # raise ValidationError(_("There no element type with code %s", (type_code)))
            return 0.0
        elementType = elementTypeList[0]
        elementList = self.env['ebspayroll.additional.elements'].search(
            [('type', '=', elementType.id), ('payment_date', '>=', payslip.date_from), ('state', '=', 'confirm'),
             ('payment_date', '<=', payslip.date_to)])
        if len(elementList) == 0:
            # raise ValidationError(_("There no element  with Type %s", (type_code)))
            return 0.0

        for element in elementList:
            for rec in element.lines:
                if rec.employee.id == employee.id:
                    amount += rec.amount
        if elementType.type == 'A':
            return amount
        else:
            return -amount

    def calculateTransportation(self, payslip, employee):
        amount = 0.0

        ruleList = self.env['ebspayroll.transportation.rule'].search(
            [('payment_date', '>=', payslip.date_from),
             ('payment_date', '<=', payslip.date_to)])
        if len(ruleList) == 0:
            # raise ValidationError(_("There no element  with Type %s", (type_code)))
            return 0.0

        for rule in ruleList:
            for rec in rule.lines:
                if rec.employee.id == employee.id:
                    amount += (rec.amount * rec.days)
                    break
        return amount

    def calculateTicketAllowance(self, payslip, employee):
        amount = 0.0
        req_allowance = self.env['ebs.payroll.ticket.allowance.request'].search([('employee_id', '=', employee.id),
                                                                                 ('state', '=', 'approved'),
                                                                                 ('payment_date', '>=',
                                                                                  payslip.date_from),
                                                                                 ('payment_date', '<=',
                                                                                  payslip.date_to)])
        for req in req_allowance:
            amount += req.approved_amount
        return amount

    def calculateAllowancePayment(self, payslip, employee, type):
        amount = 0.0
        allowance_type = self.env['ebs.payroll.allowance.request.type'].search([('name', '=', type)], limit=1)
        req_allowance = self.env['ebs.payroll.allowance.request'].search([('employee_id', '=', employee.id),
                                                                          ('state', '=', 'approved'),
                                                                          ('request_type', '=', allowance_type.id),
                                                                          ('payment_date', '>=', payslip.date_from),
                                                                          ('payment_date', '<=', payslip.date_to)])
        for req in req_allowance:
            amount += req.amount
        return amount

    def calculateAmortizationPayment(self, payslip, employee, type):
        allowance_type = self.env['ebs.payroll.allowance.request.type'].search([('name', '=', type)], limit=1)
        amount = 0.0
        req_line_allowance = self.env['ebs.payroll.allowance.request.lines'].search([
            ('employee_id', '=', employee.id),
            ('parent_type', '=', allowance_type.id),
            ('parent_state', '=', 'approved'),
            ('date', '>=', payslip.date_from),
            ('date', '<=', payslip.date_to)])
        for line in req_line_allowance:
            amount += line.amount
        return amount

    def calculateRemainingAmortizationPayment(self, payslip, employee, type):
        amount = 0.0
        allowance_type = self.env['ebs.payroll.allowance.request.type'].search([('name', '=', type)], limit=1)

        req_line_allowance = self.env['ebs.payroll.allowance.request.lines'].search([('employee_id', '=', employee.id),
                                                                                     ('parent_state', '=', 'approved'),
                                                                                     ('parent_type', '=',
                                                                                      allowance_type.id),
                                                                                     ('date', '>=', payslip.date_from),
                                                                                     ])
        for line in req_line_allowance:
            amount += line.amount
        return amount

    def calculateTimeOff(self, payslip, employee, leave_type, is_deduction):
        current_contract = payslip.contract_id
        basic_salary = current_contract.wage

        leave = self.env['hr.leave.type'].browse(int(leave_type))
        amount = 0
        if leave:
            for line in payslip.worked_days_line_ids:
                if line.work_entry_type_id.id == leave.work_entry_type_id.id and leave.work_entry_type_id.id:
                    amount += (basic_salary * employee.get_prorata(payslip.date_from)) * line.number_of_days
        if is_deduction == 'True':
            amount = -1 * amount
        return amount

    @api.onchange('employee_id', 'struct_id', 'contract_id', 'date_from', 'date_to')
    def _onchange_employee(self):
        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return

        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to

        sponsored_company_id = self.env['res.company'].search([('partner_id', '=', employee.sponsored_company_id.id)])
        if sponsored_company_id:
            self.company_id = sponsored_company_id.id
        else:
            self.company_id = employee.company_id
        if not self.contract_id or self.employee_id != self.contract_id.employee_id:  # Add a default contract if not already defined
            contracts = employee._get_contracts(date_from, date_to)

            if not contracts or not contracts[0].structure_type_id.default_struct_id:
                self.contract_id = False
                self.struct_id = False
                return
            self.contract_id = contracts[0]
            self.struct_id = contracts[0].structure_type_id.default_struct_id

        payslip_name = self.struct_id.payslip_name or _('Salary Slip')
        self.name = '%s - %s - %s' % (
            format_date(self.env, self.date_from, date_format="MMMM"),
            self.employee_id.name or '',
            format_date(self.env, self.date_from, date_format="y")
        )

        if date_to > date_utils.end_of(fields.Date.today(), 'month'):
            self.warning_message = _(
                "This payslip can be erroneous! Work entries may not be generated for the period from %s to %s." %
                (date_utils.add(date_utils.end_of(fields.Date.today(), 'month'), days=1), date_to))
        else:
            self.warning_message = False

        self.worked_days_line_ids = self._get_new_worked_days_lines()

    def director_approved(self):
        for rec in self:
            rec.state = "done"
            rec.director_approver_id = self.env.user.id

    def hr_confirm_approved_by_action(self):
        for rec in self:
            if rec.state in 'verify':
                rec.action_hr_confirm()

    def action_hr_confirm(self):
        if self.is_required_approve:
            raise ValidationError('We Need An Approval From The Shared Service Manager!')

        for rec in self:
            for lines in rec.line_ids.filtered(lambda x: x.category_id.is_deduction and x.amount != 0):
                if lines and not rec.deduction_reason:
                    raise UserError(_("Before proceeding, please set a deduction reason"))
                elif not rec.comments and rec.deduction_reason == '99':
                    raise UserError(_('If you select other option, you must fill out the deduction reason'))
            notification_ids = []
            if rec.employee_id.employee_type == 'fusion_employee':
                gid = self.env.ref('ebs_lb_payroll.group_finance_payroll_confirm')
                users = self.env['res.users'].search(
                    [('groups_id', 'in', gid.id)])

                for result in users:
                    body = "Payslip HR Confirm Notification for " + result.name
                    notification_ids.append((0, 0, {
                        'res_partner_id': result.partner_id.id,
                        'notification_type': 'inbox'}))
                    mail_server_id = self.env['ir.mail_server'].sudo().search([], order='sequence asc', limit=1)
                    mail = self.env['mail.mail'].sudo().create({
                        'subject': body,
                        'body_html': 'Payslip - <b>%s</b>'
                                     '<br/><p>Your Payslip from <b>%s</b> to. <b>%s</b></p><br/>'
                                     'HR Confirm Verified'
                                     % (
                                         rec.employee_id.name, rec.date_from, rec.date_to),
                        'email_from': self.env.user.email,
                        'email_to': result.email,
                        # 'mail_message_id': message.id,
                        'recipient_ids': [(4, result.partner_id.id)],
                        'mail_server_id': mail_server_id and mail_server_id.id,
                    })
                    mail.send()

                self.env.user.partner_id.message_post(
                    body='Payslip - <b>%s</b>'
                         '<br/><p> Payslip from <b>%s</b> to. <b>%s</b></p>'
                         'has been confirmed by HR ' % (
                             rec.employee_id.name, rec.date_from, rec.date_to),
                    message_type='notification', subtype_xmlid='mail.mt_comment', author_id=self.env.user.partner_id.id,
                    notification_ids=notification_ids)

            rec.state = 'by_hr'
            rec.hr_approver_id = self.env.user.id

    def reset_to_draft(self):
        for rec in self:
            rec.state = "draft"

    def finance_confirm_approved_by_action(self):
        for rec in self:
            if rec.state in 'by_hr':
                rec.action_finance_confirm()

    def action_finance_confirm(self):
        self.action_payslip_done()
        self.generate_expense_transfer_journal_entry()
        for rec in self:
            if rec.employee_id.employee_type == 'fusion_employee':
                gid = self.env.ref('ebs_lb_payroll.group_director_payroll_confirm')
                users = self.env['res.users'].search(
                    [('groups_id', 'in', gid.id)])
                notification_ids = []
                for result in users:
                    body = "Payslip Finance Confirm Notification for - " + result.name
                    notification_ids.append((0, 0, {
                        'res_partner_id': result.partner_id.id,
                        'notification_type': 'inbox'}))
                    mail_server_id = self.env['ir.mail_server'].sudo().search([], order='sequence asc', limit=1)
                    mail = self.env['mail.mail'].sudo().create({
                        'subject': body,
                        'body_html': 'Payslip - <b>%s</b>'
                                     '<br/><p>Your Payslip from <b>%s</b> to. <b>%s</b> </p>'
                                     'has been confirmed by Finance ' % (
                                         rec.employee_id.name, rec.date_from, rec.date_to),
                        'email_from': self.env.user.email,
                        'email_to': result.email,
                        # 'mail_message_id': message.id,
                        'recipient_ids': [(4, result.partner_id.id)],
                        'mail_server_id': mail_server_id and mail_server_id.id,
                    })
                    mail.send()
                self.env.user.partner_id.message_post(
                    body='Payslip - <b>%s</b>'
                         '<br/><p> Payslip from <b>%s</b> to. <b>%s</b> </p>'
                         'has been confirmed by Finance ' % (
                             rec.employee_id.name, rec.date_from, rec.date_to),
                    message_type='notification', subtype_xmlid='mail.mt_comment', author_id=self.env.user.partner_id.id,
                    notification_ids=notification_ids)

            rec.state = "by_finance"
            rec.finance_approver_id = self.env.user.id

    def direct_approved_by_action(self):
        for rec in self:
            if rec.state not in 'by_finance':
                raise ValidationError(
                    '%s payslip is not in Finance state, so this operation cannot be performed ' % rec.name)
            else:
                self.director_approved()

    def direct_approved(self):
        for rec in self:
            if self.employee_id.employee_type == 'fos_employee':
                # rec.action_hr_confirm()
                # rec.action_finance_confirm()
                # rec.director_approved()
                rec.hr_approver_id = self.env.user.id
                # rec.finance_approver_id = self.env.user.id
                # rec.director_approver_id = self.env.user.id
                rec.state = 'verify'
            # elif self.employee_id.employee_type == 'fusion_employee':
            #     rec.action_hr_confirm()

    def outsourced_direct_approved(self):
        for rec in self:
            if rec.state in 'done' and rec.employee_id.employee_type == 'fos_employee':
                rec.outsource_director_approver_id = self.env.user.id

    def generate_expense_transfer_journal_entry(self):
        for rec in self:
            if rec.state == "done" and not rec.expense_transfer_ids:
                moves = rec.move_id
                expense_transfer = self.env['ebs.payroll.expense.transfer'].search(
                    [('from_date', '<=', rec.date_from), ('to_date', '>=', rec.date_to)])
                employee_transfer = self.env['ebs.payroll.emp.transfer.config'].search(
                    [('employee_id', '=', rec.employee_id.id)])
                if not expense_transfer or not employee_transfer:
                    return
                transfer_lines = expense_transfer.transfer_lines_ids
                # company_transfer_line = transfer_lines.filtered(
                #     lambda o: o.company_id.partner_id.id == rec.employee_id.partner_parent_id.id)
                fusion_company_transfer_line = transfer_lines.filtered(
                    lambda o: o.company_id.id == rec.employee_id.company_id.id)
                vals_move = {}
                move_name = ""
                emp_comp_line = employee_transfer.line_ids
                if not fusion_company_transfer_line:
                    raise UserError("Please Configure company in Expense Transfer line")
                for transfer_line in fusion_company_transfer_line:
                    from_accounts = fusion_company_transfer_line.mapped('from_account_ids')
                    # search company and find it's percentage and then divide debit and credit their according to
                    # Fusion Account
                    move_line_ids = moves.line_ids.filtered(lambda x: x.account_id.id in from_accounts.ids)
                    if move_line_ids:
                        total_move_debit = sum(move_line_ids.mapped('debit'))
                        move_credit = sum(move_line_ids.mapped('credit'))
                        vals_move.update({'move_debit': total_move_debit})
                        lst = []
                        account = move_line_ids.mapped('account_id')
                        for move in move_line_ids:
                            move_line_1 = {'account_id': move.account_id.id,
                                           'partner_id': rec.employee_id.company_id.partner_id.id,
                                           'credit': move.debit,
                                           'name': move.name}
                            if move.debit > 0:
                                lst.append((0, 0, move_line_1))

                        move_line_2 = {'account_id': fusion_company_transfer_line.close_account_id.id,
                                       'partner_id': rec.employee_id.company_id.partner_id.id,
                                       'debit': total_move_debit}
                        lst.append((0, 0, move_line_2))
                        fusion_comp_moves = self.env['account.move'].create({
                            'ref': 'Expense Transfer - ' + rec.employee_id.name,
                            'date': rec.date,
                            'journal_id': transfer_line.journal_id.id,
                            'type': 'entry',
                        })
                        fusion_comp_moves.write({'line_ids': lst})
                        fusion_comp_moves.filtered(lambda move: move.journal_id.post_at != 'bank_rec').post()
                        # Update the state / move before performing any reconciliation.

                        rec.write({'expense_transfer_ids': [(4, fusion_comp_moves.id)]})
                        # result = True
                    else:
                        raise UserError("Account Move line not found for this Account - %s  " % (from_accounts.name))

                for company_line_item in emp_comp_line:
                    # main_accounts = company_line_item.main_expense_account
                    # move_debit_multi = sum(
                    #     moves.line_ids.filtered(lambda x: x.account_id.id in from_accounts.ids).mapped('debit'))
                    # company_per = emp_comp_line.filtered(lambda x: x.company_id == company_line_item.company_id)
                    companies = emp_comp_line.mapped('company_id')
                    move_debit = vals_move.get('move_debit')
                    if company_line_item.percentage:
                        percentage = company_line_item.percentage
                        move_debit = total_move_debit * (percentage / 100)
                        vals_move.update({'move_debit': move_debit})
                    transfer_line = transfer_lines.filtered(
                        lambda x: x.company_id.id == company_line_item.company_id.id)

                    if transfer_line:
                        move_line_3 = {'account_id': transfer_line.main_expense_account.id,
                                       'partner_id': company_line_item.company_id.partner_id.id,
                                       'debit': vals_move.get('move_debit')}
                        move_line_4 = {'account_id': transfer_line.close_account_id.id,
                                       'partner_id': company_line_item.company_id.partner_id.id,
                                       'credit': vals_move.get('move_debit')}

                        moves = self.env['account.move'].create({
                            'ref': 'Expense Transfer - ' + rec.employee_id.name,
                            'date': rec.date,
                            'type': 'entry',
                            'journal_id': transfer_line.journal_id.id,
                            'line_ids': [(0, 0, move_line_3), (0, 0, move_line_4)]
                        })
                        moves.filtered(lambda move: move.journal_id.post_at != 'bank_rec').post()
                        # Update the state / move before performing any reconciliation.
                        name = ""
                        move_name = name.join(moves.mapped('name'))
                        rec.write({'expense_transfer_ids': [(4, moves.id)]})
                    # self.write({'state': 'posted', 'move_name': move_name})

    def action_payslip_done(self):
        """
            Generate the accounting entries related to the selected payslips
            A move is created for each journal and for each month.
        """
        # super(HrPayslip, self).action_payslip_done()
        res = c1.action_payslip_done(self)
        precision = self.env['decimal.precision'].precision_get('Payroll')

        # A payslip need to have a done state and not an accounting move.
        payslips_to_post = self.filtered(lambda slip: slip.state == 'done' and not slip.move_id)

        # Check that a journal exists on all the structures
        if any(not payslip.struct_id for payslip in payslips_to_post):
            raise ValidationError(_('One of the contract for these payslips has no structure type.'))
        if any(not structure.journal_id for structure in payslips_to_post.mapped('struct_id')):
            raise ValidationError(_('One of the payroll structures has no account journal defined on it.'))

        for slip in payslips_to_post:  # For each month.
            line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            slip_date = fields.Date().end_of(slip.date_to, 'month')
            date = slip_date
            journal_id = slip.struct_id.journal_id.id
            ref = slip.number or ''
            ref += " - " + slip.employee_id.name or ''
            ref += " - " + slip_date.strftime('%B %Y')
            move_dict = {
                'narration': '',
                'ref': ref,
                'journal_id': journal_id,
                'date': date,
            }
            for line in slip.line_ids.filtered(lambda line: line.category_id):
                amount = -line.total if slip.credit_note else line.total
                if amount != 0:
                    debit_account_id = line.salary_rule_id.account_debit.id
                    credit_account_id = line.salary_rule_id.account_credit.id

                    if debit_account_id:  # If the rule has a debit account.
                        debit = amount if amount > 0.0 else 0.0
                        credit = -amount if amount < 0.0 else 0.0
                        debit_line = {
                            'name': line.name,
                            'partner_id': slip.employee_id.user_partner_id and slip.employee_id.user_partner_id.id or False,
                            'account_id': debit_account_id,
                            'journal_id': line.slip_id.struct_id.journal_id.id,
                            'date': date,
                            'debit': debit,
                            'credit': credit,
                            'analytic_account_id': line.salary_rule_id.analytic_account_id.id or line.slip_id.contract_id.analytic_account_id.id,
                        }
                        line_ids.append(debit_line)

                    if credit_account_id:  # If the rule has a credit account.
                        debit = -amount if amount < 0.0 else 0.0
                        credit = amount if amount > 0.0 else 0.0

                        credit_line = {
                            'name': line.name,
                            'partner_id': slip.employee_id.user_partner_id and slip.employee_id.user_partner_id.id or False,
                            'account_id': credit_account_id,
                            'journal_id': line.slip_id.struct_id.journal_id.id,
                            'date': date,
                            'debit': debit,
                            'credit': credit,
                            'analytic_account_id': line.salary_rule_id.analytic_account_id.id or line.slip_id.contract_id.analytic_account_id.id,
                        }
                        line_ids.append(credit_line)
            move_dict['line_ids'] = [(0, 0, line_vals) for line_vals in line_ids]
            move = self.env['account.move'].sudo().create(move_dict)
            slip.write({'move_id': move.id, 'date': date})
        return res

    def action_payslip_paid(self):
        super(PayslipInherit, self).action_payslip_paid()
        self._create_deduction_ele()

    def _create_deduction_ele(self):
        ded_typ = self.env['ebspayroll.additional.element.types'].search([('code', '=', 'AD')])
        if not ded_typ:
            return
        for rec in self.filtered(lambda x: x.state == 'paid'):
            sadj_line = rec.line_ids.filtered(lambda l: l.code == 'SADJ' and l.amount)
            sadj_line = sadj_line and sadj_line[0]
            if not sadj_line:
                continue
            month = rec.date_from.month
            year = rec.date_from.year
            if month == 12:
                month = 0
                year = year + 1
            next_month = rec.date_from.replace(year=year, month=month + 1, day=1)
            ded_element = rec.env['ebspayroll.additional.elements'].search([
                ('payment_date', '=', next_month),
                ('type', '=', ded_typ.id)], limit=1)
            if ded_element:
                ded_element.write({
                    'lines': [
                        Command.create({
                            'employee': rec.employee_id.id,
                            'payslip_id': rec.id,
                            'amount': sadj_line.amount
                        })
                    ]
                })
            else:
                lines = [(0, 0, {
                    'employee': rec.employee_id.id,
                    'payslip_id': rec.id,
                    'amount': sadj_line.amount
                })]

                ded_element = rec.env['ebspayroll.additional.elements'].create(
                    {
                        'type': ded_typ.id,
                        'rule_type': 'D',
                        'payment_date': next_month,
                        'lines': lines
                    }
                )


class HrPayslipRun(models.Model):
    _name = 'hr.payslip.run'
    _inherit = ['hr.payslip.run', 'dynamic.approval.mixin', 'mail.thread', 'mail.activity.mixin']
    _state_from = ['verify']
    _state_to = ['paid']

    state = fields.Selection([
        ('draft', 'New'),
        ('verify', 'Confirmed'),
        ('approved', 'Approved'),
        ('close', 'Done'),
        ('paid', 'Paid'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft', tracking=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=False, required=False,
                                 default=lambda self: self.env.company)
    client_id = fields.Many2one('res.partner', string='Client', domain=[('is_company', '=', True),
                                                                        ('parent_id', '=', False)])

    def _action_final_approve(self):
        res = super(HrPayslipRun, self)._action_final_approve()
        if self._name == 'hr.payslip.run':
            self.action_validate()
            self.action_paid()
        return res


class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    payslip_run_id = fields.Many2one(related="slip_id.payslip_run_id", store=True)
    state = fields.Selection(related="slip_id.state", store=True)
    invoice_line_id = fields.Many2one('account.move.line', string="Invoice Line ")
    is_created = fields.Boolean('Is Created', help='Is payslip line already created for invoice')
    is_check_balance = fields.Boolean('balance')


class HrPayslipEmployeesInherit(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    def get_related_employees(self):
        domain = []
        if self._context.get('payslip_batch_company'):
            employee_ids = self.env['hr.employee'].search(
                [('company_id', '=', self._context.get('payslip_batch_company'))])
            domain = [('id', 'in', employee_ids.ids)]
        return domain

    def _get_employees(self):
        domain = []
        if self._context.get('payslip_batch_company'):
            domain.append(('company_id', '=', self._context.get('payslip_batch_company')))
        if self._context.get('payslip_batch_client'):
            domain.append(('partner_parent_id', '=', self._context.get('payslip_batch_client')))
        return self.env['hr.employee'].search(domain)

    company_id = fields.Many2one('res.company', string="Company")
    employee_ids = fields.Many2many('hr.employee', 'hr_employee_group_rel', 'payslip_id', 'employee_id', 'Employees',
                                    default=lambda self: self._get_employees(), required=True,
                                    domain=get_related_employees)
