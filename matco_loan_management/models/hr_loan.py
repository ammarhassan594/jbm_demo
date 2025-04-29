from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError
import json
from pytz import timezone
import datetime as dt


class HrLoan(models.Model):
    _name = 'hr.loan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Loan Request"

    def _create_activity(self, all_users):
        all_users = all_users.sudo()
        activity_to_do = self.env.ref('mail.mail_activity_data_todo').id
        model_id = self.env['ir.model']._get('hr.loan').id
        activity = self.env['mail.activity']
        for user in all_users:
            if user:
                act_dct = {
                    'activity_type_id': activity_to_do,
                    'note': "kindly check this Loan Edite's!",
                    'user_id': user.id,
                    'res_id': self.id,
                    'res_model_id': model_id,
                    'date_deadline': datetime.today().date()
                }
                activity.sudo().create(act_dct)

    # def write(self, vals):
    #     object = super(HrLoan, self).write(vals)
    #     if vals:
    #         users = self.env['res.users'].search([])
    #         if users:
    #             for user in users:
    #                 if user.has_group("jbm_group_access_right_extended.custom_group_shared_service_manager"):
    #                     self._create_activity(user)
    #     return object

    # @api.model
    # def default_get(self, field_list):
    #     result = super(HrLoan, self).default_get(field_list)
    #     result['installment'] = int(
    #         self.env['ir.config_parameter'].sudo().get_param('matco_loan_management.loan_installments'))
    #     if result.get('user_id'):
    #         ts_user_id = result['user_id']
    #     else:
    #         ts_user_id = self.env.context.get('user_id', self.env.user.id)
    #     result['employee_id'] = self.env['hr.employee'].search([('user_id', '=', ts_user_id)], limit=1).id
    #     return result

    @api.depends('loan_lines.paid')
    def _compute_loan_amount(self):
        for loan in self:
            total_paid = 0.0
            if loan.loan_lines:
                total_paid += sum(loan.loan_lines.filtered(lambda x: x.paid).mapped('amount'))
            balance_amount = loan.loan_amount - total_paid
            if loan.loan_lines and loan.loan_lines[-1].paid:
                loan.write({
                    'total_amount': loan.loan_amount,
                    'balance_amount': balance_amount,
                    'total_paid_amount': total_paid,
                    'state': 'settle',
                })
            else:
                loan.write({
                    'total_amount': loan.loan_amount,
                    'balance_amount': balance_amount,
                    'total_paid_amount': total_paid,
                })

    name = fields.Char(string="Loan Name", default="/", readonly=True, help="Name of the loan")
    loan_type = fields.Many2one(comodel_name="hr.loan.type", string="Loan Type", required=True)
    is_personal_loan = fields.Boolean(related="loan_type.personal_loan", string="Is Personal Loan")
    # loan_type_domain = fields.Char(compute="_compute_loan_type_domain", readonly=True, )
    date = fields.Date(string="Date", default=fields.Date.today(), readonly=True, help="Date")
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, help="Employee")
    # employee_type = fields.Selection(string="Employment Category", default="", store=True,
    #                                  selection=[('temp', 'Temporary Employee'),
    #                                             ('perm_in_house', 'Permanent In house'),
    #                                             ('perm_staff', 'Permanent Staff')], related="employee_id.employee_type")
    department_id = fields.Many2one('hr.department', related="employee_id.department_id", readonly=True,
                                    string="Department", help="Employee")
    installment = fields.Integer(string="No Of Installments", default=1, help="Number of installments",
                                 compute="get_number_of_installments", store=True, readonly=False)
    payment_date = fields.Date(string="Installment Start Date", required=True, default=fields.Date.today(),
                               help="Date of the payment of installments")
    payment_date_of_loan = fields.Date(string="Payment Date", default=fields.Date.today(),
                                       help="Date of the payment")
    loan_lines = fields.One2many('hr.loan.line', 'loan_id', string="Loan Line", index=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True, help="Company",
                                 default=lambda self: self.env.user.company_id,
                                 states={'draft': [('readonly', False)]})
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, help="Currency",
                                  default=lambda self: self.env.user.company_id.currency_id)
    job_position = fields.Many2one('hr.job', related="employee_id.job_id", readonly=True, string="Job Position",
                                   help="Job position")
    loan_amount = fields.Float(string="Loan Amount", required=True, help="Loan amount")
    max_loan_amount = fields.Float(string="Max Loan Amount", compute='_get_max_loan_amount')
    total_amount = fields.Float(string="Total Amount", store=True, readonly=True, compute='_compute_loan_amount',
                                help="Total loan amount")
    balance_amount = fields.Float(string="Balance Amount", store=True, compute='_compute_loan_amount',
                                  help="Balance amount")
    total_paid_amount = fields.Float(string="Total Paid Amount", store=True, compute='_compute_loan_amount',
                                     help="Total paid amount")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval_1', 'Submitted'),
        ('first_approve', 'First Approved'),
        ('approve', 'Second Approved'),
        ('paid', 'Paid'),
        ('settle', 'Settled'),
        ('refuse', 'Refused'),
        ('cancel', 'Canceled'),
    ], string="State", default='draft', track_visibility='onchange', copy=False, )
    is_paid = fields.Boolean(string='Is Paid')
    payroll_user = fields.Boolean('Payroll User', compute='_is_payroll_user')
    employee_number = fields.Char(related="employee_id.registration_number")
    parent_id = fields.Many2one('hr.loan')
    is_car_loan = fields.Boolean(default=False, compute="get_is_car_loan")
    # is_good_will_loan = fields.Boolean(default=False, compute="get_is_good_will_loan")
    is_clicked = fields.Boolean(default=False)
    loan_settle = fields.Boolean(default=False)
    parent_loan_settle_id = fields.Many2one('hr.loan')
    settle_amount = fields.Float(string="Settle Amount")
    paid_amount = fields.Float(string="Payable Amount", compute="get_paid_amount")
    first_paid_amount = fields.Float(string="First Paid Amount")
    loan_payment_date = fields.Date(string="Loan Payment Date", default=lambda self: fields.Datetime.now(), required=True)

    @api.constrains('loan_type', 'employee_id', 'payment_date', 'loan_amount')
    def _loan_validation(self):
        for record in self:
            if record.loan_type.marriage_loan:
                marriage_lonas = self.env['hr.loan'].search([
                    ('employee_id', '=', record.employee_id.id),
                    ('loan_type', '=', record.loan_type.id),
                    ('id', '!=', record.id)
                ])
                if marriage_lonas:
                    raise ValidationError("This Employee have marriage loan before!")
            else:
                last_settle_amount = self.env['hr.loan'].search(
                    [('employee_id', '=', record.employee_id.id),
                     ('state', 'in', ['paid', 'settle']),
                     ('loan_type', '=', record.loan_type.id),
                     ('id', '!=', record.id)], order='date DESC', limit=1)
                if last_settle_amount and record.loan_type.years_to_pass:
                    allow_date_loan = last_settle_amount.payment_date + relativedelta(
                        years=record.loan_type.years_to_pass)
                    if not record.payment_date >= allow_date_loan:
                        raise ValidationError(
                            _("This Employee Can't have same[%s] loan type before %s years", record.loan_type.name,
                              record.loan_type.years_to_pass))
                    else:
                        not_paid_loan_lines = last_settle_amount.loan_lines.filtered(lambda line: line.paid == False)
                        if not_paid_loan_lines:
                            unpaid_amount = 0.0
                            for loan_line in not_paid_loan_lines:
                                unpaid_amount += loan_line.amount
                                loan_line.write({
                                    'paid': True,
                                })
                            record.first_paid_amount = unpaid_amount

                # elif not record.loan_type.years_to_pass:
                #     raise ValidationError(_('Please set Years to pass value to [%s] loan type', record.loan_type.name))
                # elif not last_settle_amount:
                #     marriage_loan = self.env['hr.loan.type'].search([
                #         ('marriage_loan', '=', True)
                #     ], limit=1)
                #     last_another_loan = self.env['hr.loan'].search(
                #         [('employee_id', '=', record.employee_id.id),
                #          ('state', 'in', ['paid', 'settle']),
                #          ('loan_type', '!=', record.loan_type.id),
                #          ('loan_type', '!=', marriage_loan.id),
                #          ], order='date DESC', limit=1)
                #     if last_another_loan and last_another_loan.loan_lines:
                #         time_from = last_another_loan.loan_lines[0].date
                #         time_to = last_another_loan.loan_lines[-1].date
                #         if time_from <= record.payment_date <= time_to:
                #             raise ValidationError(_("This Employee have another loan type [%s] in the same time!",
                #                                     last_another_loan.loan_type.name))

            if record.loan_type.loan_amount_configuration == 'max_amount' and \
                    record.loan_type.max_amount and record.loan_amount and \
                    record.loan_amount > record.loan_type.max_amount:
                print('lol ya lol')
                raise ValidationError(_('Amount must be less than or equal to %s', record.loan_type.max_amount))
            elif record.loan_type.loan_amount_configuration == 'm_salary_element' and record.loan_type.multiplier_amount:
                contract = self.env['hr.contract'].sudo().search([
                    ('employee_id', '=', record.employee_id.id), ('state', '=', 'open')
                ], limit=1)
                if contract:
                    if record.loan_amount > (record.loan_type.multiplier_amount * contract.wage):
                        raise ValidationError(_('Amount must be less than or equal to %s', (record.loan_type.multiplier_amount * contract.wage)))


    @api.onchange('loan_type')
    @api.depends('loan_type')
    def onchange_loan_type(self):
        for record in self:
            if record.loan_type and record.loan_type.allowed_for:
                if record.loan_type.allowed_for == 'qatari':
                    country = self.env['res.country'].search([
                        ('code', '=', 'QA')
                    ], limit=1)
                    return {'domain': {
                        'employee_id': [('country_id', '=', country.id)],
                    }}
                elif record.loan_type.allowed_for == 'not_qatari':
                    country = self.env['res.country'].search([
                        ('code', '!=', 'QA')
                    ], limit=1)
                    return {'domain': {
                        'employee_id': [('country_id', '=', country.id)],
                    }}
                elif record.loan_type.allowed_for == 'both':
                    return {'domain': {
                        'employee_id': [],
                    }}

    @api.depends('employee_id', 'parent_loan_settle_id', 'total_amount', 'loan_type')
    def get_paid_amount(self):
        for rec in self:
            if rec.parent_loan_settle_id and rec.loan_type == rec.parent_loan_settle_id.loan_type:
                rec.paid_amount = rec.loan_amount - rec.parent_loan_settle_id.settle_amount
            else:
                rec.paid_amount = rec.loan_amount

    @api.depends('loan_type', 'employee_id')
    def get_number_of_installments(self):
        for record in self:
            record.installment = 1
            if record.loan_type and record.employee_id:
                if record.employee_id.country_id:
                    record.installment = record.loan_type.num_of_installments if record.employee_id.country_id.code == 'QA' else record.loan_type.non_qatar_num_of_installments

    def action_loan_settle(self):
        for rec in self:
            temp = rec.balance_amount
            rec.sudo().write({
                'loan_settle': True,
                'settle_amount': temp,
                'balance_amount': 0.00,
                'state': 'settle'
            })
            for line in rec.loan_lines:
                if not line.paid:
                    line.sudo().write({
                        'paid': True,
                        'is_in_settle': True,
                    })

    @api.depends('loan_type')
    def get_is_car_loan(self):
        if self.loan_type:
            if self.loan_type.car_loan and self.state == 'paid':
                self.is_car_loan = True
            else:
                self.is_car_loan = False
        else:
            self.is_car_loan = False

    def action_get_unpaid_lines(self):
        loan_obj = self.env['hr.loan']
        loan_line_obj = self.env['hr.loan.line']
        if self.loan_lines:
            has_unpaid = False
            for rec in self.loan_lines:
                if not rec.paid:
                    has_unpaid = True
                    break
            if has_unpaid:
                vals = {
                    'employee_number': self.employee_number,
                    'employee_id': self.employee_id.id,
                    'loan_type': self.loan_type.id,
                    'date': self.date,
                    'department_id': self.department_id.id,
                    'job_position': self.job_position.id,
                    'loan_amount': self.balance_amount,
                    'installment': self.loan_type.num_of_installments,
                    'payment_date': self.payment_date,
                    'parent_id': self.id,
                    'state': 'draft',
                }
                res = loan_obj.create(vals)
                self.is_paid = True
                self.env.cr.commit()

            for rec in self.loan_lines:
                if not rec.paid:
                    line_vals = {
                        'date': rec.date,
                        'paid': rec.paid,
                        'amount': rec.amount,
                        'loan_id': self.id,
                        'employee_id': rec.employee_id.id,
                        'payslip_id': rec.payslip_id.id,
                    }
                    result = loan_line_obj.create(line_vals)
                    rec.paid = True
                    self.is_clicked = True

    def action_unpaid(self):
        unpaid_loan = self.env['hr.loan'].search([('parent_id', '=', self.id)])
        if len(unpaid_loan) > 0:
            return {
                'name': "Unpaid",
                'view_mode': 'form',
                'res_model': 'hr.loan',
                'res_id': unpaid_loan.id,
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', unpaid_loan.ids)]
            }

    def _default_user(self):
        return self.env.user

    user_id = fields.Many2one('res.users', default=_default_user, compute="_get_current_user")

    def _get_current_user(self):
        for rec in self:
            rec.user_id = self.env.user

    @api.depends('user_id')
    def _is_payroll_user(self):
        for rec in self:
            if rec.user_id.has_group('hr_payroll.group_hr_payroll_user'):
                rec.payroll_user = True
            else:
                rec.payroll_user = False

    @api.depends('loan_amount', 'total_paid_amount')
    def _loan_is_paid(self):
        for rec in self:
            if rec.loan_amount == rec.total_paid_amount:
                rec.is_paid = True
            else:
                rec.is_paid = False

    @api.depends('loan_amount', 'loan_type', 'employee_id')
    def _get_max_loan_amount(self):
        for loan in self:
            if loan.loan_type.personal_loan:
                loan.max_loan_amount = loan.employee_id.total_amount_working_days_no_store * 0.5
            else:
                loan.max_loan_amount = 0

    @api.onchange('employee_id', 'loan_type')
    def loan_amount_update(self):
        for rec in self:
            if rec.employee_id:
                # Please uncomment this code for applying business logic
                # if rec.employee_id.employee_type == "perm_in_house":
                #     rec.loan_type = rec.env['hr.loan.type'].search([('personal_loan', '=', True)]).id
                # elif rec.employee_id.employee_type == "perm_staff":
                #
                #     rec.loan_type = rec.env['hr.loan.type'].search([('car_loan', '=', True)]).id
                contract = self.env['hr.contract'].sudo().search([
                    ('employee_id', '=', rec.employee_id.id), ('state', '=', 'open')
                ], limit=1)
                last_settle_amount = self.env['hr.loan'].search(
                    [('employee_id', '=', rec.employee_id.id), ('state', '=', 'paid'),
                     ('loan_type', '=', rec.loan_type.id)], order='date DESC', limit=1)
                if rec.loan_type.car_loan:
                    diff = relativedelta(fields.Date.today(), rec.employee_id.joining_date)
                    months_difference = (diff.years * 12) + diff.months
                    if last_settle_amount:
                        rec.loan_amount = last_settle_amount.settle_amount
                    else:
                        if months_difference <= rec.loan_type.num_of_installments:
                            rec.loan_amount = rec.employee_id.contract_id.payscale_id.car_loan
                        else:
                            rec.loan_amount = max(rec.employee_id.contract_id.payscale_id.car_loan,
                                                  rec.employee_id.contract_id.wage * 3)
                    # rec.loan_amount = rec.employee_id.contract_id.car_loan_for_permanent_staff
                elif rec.loan_type.marriage_loan:
                    if last_settle_amount:
                        rec.loan_amount = last_settle_amount.settle_amount
                    else:
                        rec.loan_amount = rec.employee_id.contract_id.payscale_id.marriage_loan - last_settle_amount.settle_amount
                else:
                    rec.loan_amount = 0.00
                # Check loan amount configuration.
                if rec.loan_type.loan_amount_configuration == 'm_salary_element':
                    rec.loan_amount = rec.loan_type.multiplier_amount * \
                                      contract.wage
                elif rec.loan_type.loan_amount_configuration == 'max_amount':
                    rec.loan_amount = rec.loan_type.max_amount

    @api.model
    def create(self, values):
        employee = self.env['hr.employee'].browse(values.get('employee_id')) or self.env.user.employee_id
        loan_count = self.env['hr.loan'].search_count(
            [('employee_id', '=', employee.id), ('loan_type', '=', values['loan_type']),
             ('state', 'not in', ['draft', 'refuse', 'cancel']),
             ('balance_amount', '!=', 0)])
        if loan_count and 'parent_id' not in values:
            raise ValidationError(_("The employee has already a pending installment"))
        else:
            values['name'] = self.env['ir.sequence'].get('hr.loan.seq') or ' '
        last_settle_loan_id = self.env['hr.loan'].search([('employee_id', '=', employee.id), ('state', '=', 'settle')],
                                                         order='date DESC', limit=1)
        values['parent_loan_settle_id'] = last_settle_loan_id.id if last_settle_loan_id else False
        res = super(HrLoan, self).create(values)
        # for line in last_settle_loan_id.loan_lines:
        #     self.env['hr.loan.line'].sudo().create({
        #         'date': line.date,
        #         'employee_id': line.employee_id.id,
        #         'amount': line.amount,
        #         'paid': False,
        #         'loan_id': res.id,
        #     })
        return res

    def get_url(self):
        self.ensure_one()
        if self.contract_id:
            get_url = str(self.env['ir.config_parameter'].sudo().search(
                [('key', '=', 'web.base.url')]).value) + '/web?#id=' + str(
                self.id) + '&view_type=form&model=hr.loan&action=' + str(
                self.env.ref('matco_loan_management.action_hr_loan_request').id) + ' & menu_id = '
            return get_url

    @api.constrains('employee_id', 'loan_type')
    def _check_employee_sponsor(self):
        for rec in self:
            if rec.employee_id and rec.employee_id.sponsor:
                if rec.employee_id.sponsor.id not in rec.loan_type.sponsor_ids.ids:
                    raise ValidationError(
                        _(f"For this loan type the employee should be under sponsorship of {rec.loan_type.sponsor_ids.mapped('name')}"))
            if rec.employee_id and rec.employee_id.collaborator:
                raise ValidationError(_('You are not applicable for requesting a loan'))

    def compute_installment(self):
        """This automatically create the installment the employee need to pay to
        company based on payment start date and the no of installments."""
        for loan in self:
            # TODO had to stop the settle logic
            if loan.parent_loan_settle_id and False:
                loan.loan_lines.unlink()
                date_start = datetime.strptime(str(loan.payment_date), '%Y-%m-%d')
                count = 0
                for rec in loan.parent_loan_settle_id.loan_lines:
                    if rec.is_in_settle:
                        count += 1
                if count > 0:
                    amount = int(loan.loan_amount / count)
                    remaining_amount = loan.loan_amount - amount * count
                    for i in range(1, count + 1):
                        self.env['hr.loan.line'].sudo().create({
                            'date': date_start,
                            'amount': amount,
                            'employee_id': loan.employee_id.id,
                            'loan_id': loan.id})
                        date_start = date_start + relativedelta(months=1)
                    loan.loan_lines[-1].write({'amount': amount + remaining_amount})
                    loan.write({'installment': count})
                    loan._compute_loan_amount()
            else:
                loan.loan_lines.unlink()
                date_start = datetime.strptime(str(loan.payment_date), '%Y-%m-%d')

                if loan.first_paid_amount > 0:
                    if loan.installment < 2:
                        if self.env.context.get('lang') == 'ar_001':
                            raise ValidationError(_("عدد الأقساط لا يمكن ان يكون اقل من  2 ........... "))
                        else:
                            raise ValidationError(_("No of installments can\'t be less than 2 ........."))
                    self.env['hr.loan.line'].sudo().create({
                        'date': date_start,
                        'amount': loan.first_paid_amount,
                        'employee_id': loan.employee_id.id,
                        'loan_id': loan.id})

                    date_start = date_start + relativedelta(months=1)
                    amount_after_first_paid = loan.loan_amount - loan.first_paid_amount
                    amount = int(amount_after_first_paid / (loan.installment - 1))
                    remaining_amount = amount_after_first_paid - amount * (loan.installment - 1)

                    for i in range(1, loan.installment):
                        self.env['hr.loan.line'].sudo().create({
                            'date': date_start,
                            'amount': amount,
                            'employee_id': loan.employee_id.id,
                            'loan_id': loan.id})
                        date_start = date_start + relativedelta(months=1)
                    loan.loan_lines[-1].write({'amount': amount + remaining_amount})
                elif loan.first_paid_amount == 0:
                    amount = int(loan.loan_amount / loan.installment)
                    remaining_amount = loan.loan_amount - amount * loan.installment
                    for i in range(1, loan.installment + 1):
                        self.env['hr.loan.line'].sudo().create({
                            'date': date_start,
                            'amount': amount,
                            'employee_id': loan.employee_id.id,
                            'loan_id': loan.id})
                        date_start = date_start + relativedelta(months=1)
                    loan.loan_lines[-1].sudo().write({'amount': amount + remaining_amount})
                loan.sudo()._compute_loan_amount()

        return True

    def action_refuse(self):
        return self.write({'state': 'refuse'})

    def action_submit(self):
        # if not self.loan_amount:
        #     raise ValidationError(_("Please Enter Loan Amount"))
        for data in self:
            if not data.loan_lines:
                raise ValidationError(_("Please Compute installment"))
            if not data.employee_id.contract_id:
                raise ValidationError(_("Please add a valid contract"))
            if data.loan_type.personal_loan and data.loan_amount > data.employee_id.total_amount_working_days_no_store * 0.5:
                raise ValidationError(_("Personal Loan amount more than 50% of the End Of Service Benefits"))
            # if data.loan_amount > 50000:
            #     raise ValidationError(_("maximum allowed amount is 50,000 QR"))
            if data.loan_type.personal_loan:
                if data.loan_amount > 50000:
                    raise ValidationError(_("maximum allowed amount is 50,000 QR"))
                loan_amount = min(data.loan_amount, 50000)
                self.sudo().write({'loan_amount': loan_amount,
                                   'state': 'waiting_approval_1'})
                self.compute_installment()
                return True
            if not data.employee_id.contract_id.wage:
                raise ValidationError(_("Please add Employee Basic"))
            if not data.employee_id.contract_id.gross:
                raise ValidationError(_("Please add Employee Gross Salary"))
            other_loans = self.env['hr.loan'].sudo().search([('employee_id', '=', data.employee_id.id),
                                                             ('state', '=', 'approve'), ('is_paid', '=', False),
                                                             ('balance_amount', '!=', 0)])
            sum_of_loan_installments = 0
            if other_loans:
                sum_of_loan_installments += data.loan_lines[0].amount
                for each_loan in other_loans:
                    sum_of_loan_installments += each_loan.loan_lines[0].amount
                if sum_of_loan_installments > data.employee_id.contract_id.gross * 0.25:
                    raise ValidationError(_("Total of Employee installments are more than 25% of his gross salary."))
            if data.loan_type.marriage_loan:
                # loan_amount = min(data.loan_amount, data.employee_id.contract_id.wage * 4, 40000)
                self.write({'state': 'waiting_approval_1'})
                # self.compute_installment()
                return True
            elif data.loan_type.car_loan:
                car_loan = self.env['hr.loan'].sudo().search([('employee_id', '=', data.employee_id.id),
                                                              ('state', '=', 'approve'),
                                                              ('loan_type.car_loan', '=', True)],
                                                             order='date desc', limit=1)
                # if car_loan:
                #     r = relativedelta(fields.Date.today(), car_loan.date)
                #     months_difference = (r.years * 12) + r.months
                #     if months_difference < 36:
                #         raise ValidationError(
                #             _("Please you can not proceed with a second car loan in less than 36 months."))
                if data.installment > data.loan_type.num_of_installments:
                    raise ValidationError(
                        _(f"Please installments must be {data.loan_type.num_of_installments} or less."))
                # if data.employee_id.employee_type == 'perm_in_house':
                #     raise ValidationError(_("You must be from Permanent Staff"))
                # if not data.employee_id.contract_id.payscale_id:
                #     raise ValidationError(_("Please add a Pay Scale for the Employee"))
                self.write({'state': 'waiting_approval_1'})
                self.compute_installment()
                return True
        self.compute_installment()
        self.write({'state': 'waiting_approval_1'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def get_url(self):
        self.ensure_one()
        get_url = str(self.env['ir.config_parameter'].sudo().search(
            [('key', '=', 'web.base.url')]).value) + '/web?#id=' + str(
            self.id) + '&view_type=form&model=hr.loan&action=' + str(
            self.env.ref('matco_loan_management.action_hr_loan_request').id) + ' & menu_id = '
        return get_url

    def action_first_approve(self):
        # for data in self:
        #     if not data.loan_lines:
        #         raise ValidationError(_("Please Compute installment"))
        #     if not data.employee_id.contract_id:
        #         raise ValidationError(_("Please add a valid contract"))
        #     if data.loan_type.personal_loan and data.loan_amount > data.employee_id.total_amount_working_days_no_store * 0.5:
        #         raise ValidationError(_("Personal Loan amount more than 50% of the End Of Service Benefits"))
        #     if data.loan_type.personal_loan:
        #         self.write({'state': 'first_approve'})
        #         return True
        #     if not data.employee_id.contract_id.wage:
        #         raise ValidationError(_("Please add Employee Basic"))
        #     if not data.employee_id.contract_id.gross:
        #         raise ValidationError(_("Please add Employee Gross Salary"))
        #     other_loans = self.env['hr.loan'].search([('employee_id', '=', data.employee_id.id),
        #                                               ('state', '=', 'approve'), ('is_paid', '=', False),
        #                                               ('balance_amount', '!=', 0)])
        #     sum_of_loan_installments = 0
        #     if other_loans:
        #         sum_of_loan_installments += data.loan_lines[0].amount
        #         for each_loan in other_loans:
        #             sum_of_loan_installments += each_loan.loan_lines[0].amount
        #         if sum_of_loan_installments > data.employee_id.contract_id.gross * 0.25:
        #             raise ValidationError(_("Total of Employee installments are more than 25% of his gross salary."))
        #     if data.loan_type.marriage_loan:
        #         loan_amount = min(data.loan_amount, data.employee_id.contract_id.wage * 4, 40000)
        #         self.write({'loan_amount': loan_amount,
        #                     'state': 'first_approve'})
        #         self.compute_installment()
        #         return True
        #     elif data.loan_type.car_loan:
        #         car_loan = self.env['hr.loan'].search([('employee_id', '=', data.employee_id.id),
        #                                                ('state', '=', 'approve'), ('loan_type.car_loan', '=', True)],
        #                                               order='date desc', limit=1)
        #         if car_loan:
        #             r = relativedelta(fields.Date.today(), car_loan.date)
        #             months_difference = (r.years * 12) + r.months
        #             if months_difference < 36:
        #                 raise ValidationError(
        #                     _("Please you can not proceed with a second car loan in less than 36 months."))
        #         if data.installment > 36:
        #             raise ValidationError(_("Please installments must be 36 or less."))
        #         if data.employee_id.employee_type == 'perm_in_house':
        #             raise ValidationError(_("You must be from Permanent Staff"))
        #         if not data.employee_id.contract_id.payscale_id:
        #             raise ValidationError(_("Please add a Pay Scale for the Employee"))
        #         if data.employee_id.contract_id.payscale_id.car_loan < data.loan_amount:
        #             self.write({'loan_amount': data.employee_id.contract_id.payscale_id.car_loan,
        #                         'state': 'first_approve'})
        #             self.compute_installment()
        #             return True
        self.write({'state': 'first_approve'})

    @api.model
    def action_server_first_approve_loan(self):
        for rec in self:
            if rec.state == 'waiting_approval_1':
                rec.write({'state': 'first_approve'})

    def send_notification_of_loan_request(self, users):
        template = self.env.ref('matco_loan_management.mail_template_send_notification_of_loan_request',
                                raise_if_not_found=False)
        if users and template:
            partner_to = [str(user.partner_id.id) for user in users if users]
            if partner_to:
                user_tz = self.env.user.partner_id.tz or 'Africa/Nairobi'
                create_date = timezone('UTC').localize(self.create_date).astimezone(timezone(user_tz))
                loan_approval_state = 'First Approval' if self.state == 'waiting_approval_1' else 'Second Approval'
                template.sudo().with_context(
                    partner_to=','.join(partner_to), create_date=create_date,
                    loan_approval_state=loan_approval_state).send_mail(self.id, force_send=True)

                # notification_ids = [(0, 0,
                #                      {
                #                          'res_partner_id': user.partner_id.id,
                #                          'notification_type': 'inbox'
                #                      }
                #                      ) for user in users if users]
                #
                # self.env['mail.message'].create({
                #     'message_type': "notification",
                #     'body': f"Loan Request {self.name} is  Submitted To {loan_approval_state}",
                #     'partner_ids': [(4, user.partner_id.id) for user in users if users],
                #     'model': self._name,
                #     'res_id': self.id,
                #     'notification_ids': notification_ids,
                #     'author_id': self.env.user.partner_id and self.env.user.partner_id.id
                # })

    def update_activity(self, users):
        activity_to_do = self.env.ref('matco_loan_management.mail_act_loan_approval').id
        model_id = self.env['ir.model']._get('hr.loan').id
        activity = self.env['mail.activity']
        if self.state in ['waiting_approval_1', 'first_approve']:
            for user in users:
                if user:
                    act_dct = {
                        'activity_type_id': activity_to_do,
                        'note': "للتكرم بمراجعة طلب السلفة على نظام موارد.",
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

    def action_approve(self):
        for data in self:
            if not data.loan_lines:
                raise ValidationError(_("Please Compute installment"))
            else:
                self.write({'state': 'approve'})

    @api.model
    def action_server_approve_loan(self):
        for rec in self:
            if rec.state == 'first_approve':
                if not rec.loan_lines:
                    raise ValidationError(_("Please Compute installment"))
                else:
                    self.write({'state': 'approve'})
                second_approve_users = self.env.ref('matco_loan_management.group_loan_second_approval').users
                first_approve_users = self.env.ref('matco_loan_management.group_loan_first_approval').users
                if second_approve_users and first_approve_users:
                    second_approve_users += first_approve_users
                rec.update_activity(second_approve_users)

    def action_paid(self):
        for data in self:
            today = dt.date.today()
            next_month_first_day = today + relativedelta(months=1, day=1)
            if not data.loan_lines:
                raise ValidationError(_("Please Compute installment"))
            else:
                data.sudo().write({
                    'state': 'paid',
                    # 'payment_date': next_month_first_day,
                })
                data.compute_installment()

    @api.model
    def action_mass_paid(self):
        for rec in self:
            if rec.state == 'approve':
                today = dt.date.today()
                next_month_first_day = today + relativedelta(months=1, day=1)
                rec.sudo().write({
                    'state': 'paid',
                    'payment_date': next_month_first_day,
                })
                rec.compute_installment()

    @api.model
    def action_generate_loan_report(self):
        rec = self.filtered(lambda x: x.state == 'approve')
        if rec:
            data = {
                'loans': rec.ids,
            }
            return self.env.ref('matco_loan_management.action_loan_request_xlsx_report').report_action(self,
                                                                                                       data=data)
        else:
            raise UserError(_('Please, select records with second approval.'))

    def unlink(self):
        for loan in self:
            if loan.state not in ('draft', 'cancel'):
                raise UserError('You cannot delete a loan which is not in draft or cancelled state')
        return super(HrLoan, self).unlink()

    def _update_loan_balance(self):
        loans = self.env['hr.loan'].search([('state', '=', 'paid')])
        for loan in loans:
            total_paid = 0.0
            for line in loan.loan_lines:
                if line.paid:
                    total_paid += line.amount
            balance_amount = loan.loan_amount - total_paid
            loan.sudo().write({
                'total_amount': loan.total_amount,
                'balance_amount': balance_amount,
                'total_paid_amount': total_paid,
                'state': 'settle' if balance_amount == 0 else 'paid'
            })

    @api.model
    def _delete_inactive_activity_loans(self):
        loans = self.search([
            ('state', 'in', ['refuse', 'cancel', 'approve', 'settle', 'paid']),
            ('activity_ids', '!=', False)
        ])


class InstallmentLine(models.Model):
    _name = "hr.loan.line"
    _description = "Installment Line"

    date = fields.Date(string="Payment Date", required=True, help="Date of the payment")
    employee_id = fields.Many2one('hr.employee', string="Employee", help="Employee")
    amount = fields.Float(string="Amount", required=True, help="Amount")
    paid = fields.Boolean(string="Paid", help="Paid")
    loan_id = fields.Many2one('hr.loan', string="Loan Ref.", help="Loan")
    payslip_id = fields.Many2one('hr.payslip', string="Payslip Ref.", help="Payslip")
    is_in_settle = fields.Boolean(default=False)


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _compute_employee_loans(self):
        """This compute the loan amount and total loans count of an employee.
            """
        self.loan_count = self.env['hr.loan'].search_count([('employee_id', '=', self.id)])

    loan_count = fields.Integer(string="Loan Count", compute='_compute_employee_loans')
