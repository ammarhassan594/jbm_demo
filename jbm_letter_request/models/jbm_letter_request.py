# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class JbmLetterRequest(models.Model):
    _name = 'jbm.letter.request'
    _inherit = ['mail.thread']
    _description = 'JBM Letter Request'
    _order = 'date desc'

    def _get_default_employee_id(self):
        return self.env.user.employee_id.id or False

    letter_type_id = fields.Many2one(comodel_name='letter.type',
                                     string='Letter Type',
                                     required=True)
    code = fields.Char(string='Code', related='letter_type_id.code', store=True)

    address_id = fields.Many2one(comodel_name='res.partner', required=True,
                                 string='Contact Address')

    name = fields.Char(string='Letter Request No.', default='New', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  required=True, index=True, tracking=True,
                                  default=_get_default_employee_id)
    registration_number = fields.Char(related="employee_id.registration_number",
                                      string="Employee Code", store=True)

    user_id = fields.Many2one('res.users', related='employee_id.user_id',
                              string='Related User', store=True)

    date = fields.Date(string='Date', required=True,
                       default=fields.Date.today(),
                       tracking=True)
    signatory_id = fields.Many2one('hr.employee', string='Signatory',
                                   domain=[('signatory', '=', True)],
                                   readonly=True)
    description = fields.Text(string="Description", copy=False)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)
    state = fields.Selection([
        ('draft', 'draft'),
        ('print', 'Printed'),
    ], string='Status', readonly=True,
        default='draft', tracking=True)
    name_sequence = fields.Char(default='New', readonly=True)

    # Report Methods
    def number_to_word(self, number):
        return str(self.env.user.company_id.currency_id.
        with_context(lang='ar_001',
                     qatar=True).amount_to_text(
            number)) + ' قطري فقط لا غير '

    def get_employee_contract(self):
        self.ensure_one()
        return self.employee_id.contract_id if \
            self.employee_id.contract_id.state == 'open' \
            else self.env['hr.contract'].search([
            ('employee_id', '=', self.employee_id.id), ('state', '=', 'open')], limit=1)

    def get_loan(self):
        self.ensure_one()
        loan_line_sudo = self.env['hr.loan.line'].sudo()
        if not self.employee_id:
            return loan_line_sudo
        loan_lines = loan_line_sudo.search([
            ('employee_id', '=', self.employee_id.id),
            ('loan_id.state', '=', 'paid'),
        ]).filtered(
            lambda l: l.date and self.date and
                      l.date.month == self.date.month
                      and self.date.year == l.date.year)

        return loan_lines

    def get_pension_letter(self):
        self.ensure_one()
        amount_pension = 0
        if self.employee_id.out_of_pension:
            return amount_pension
        pension_obj = self.env['pension.config'].search([
            ('country_id', '=', self.employee_id.country_id.id)],
            limit=1)
        if not pension_obj:
            return amount_pension
        employee_contract = self.get_employee_contract()
        emp_basic = pension_obj.employee_basic / 100 * employee_contract.wage
        emp_social = pension_obj.employee_social / 100 * employee_contract.social_alw
        emp_housing = pension_obj.employee_housing / 100 * employee_contract.housing_alw
        emp_transport = pension_obj.employee_transport / 100 * employee_contract.transport_alw
        emp_mobile = pension_obj.employee_mobile / 100 * employee_contract.mobile_alw
        return emp_basic + emp_mobile + emp_transport + emp_housing + emp_social

    @api.constrains('employee_id', 'letter_type_id', 'date')
    def _check_max_letter_request(self):
        for letter in self:
            last_letters = self.search([
                ('employee_id', '=', letter.employee_id.id),
                ('letter_type_id', '=', letter.letter_type_id.id),
                ('date', '=', letter.date)
            ])
            max_number_letter = int(self.env['ir.config_parameter'].sudo().get_param(
                'jbm_letter_request.max_number_letter', 0))
            if max_number_letter and last_letters and len(last_letters) > max_number_letter:
                raise ValidationError(_(f'Can not create more than {max_number_letter} letters'
                                        f', Contact to your manager for help !'))

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_print(self):
        if self.letter_type_id.code in ['csd']:
            self.state = 'print'
            return self.env.ref('jbm_letter_request.jbm_report_certificate_salary_template'). \
                report_action(self)
        elif self.letter_type_id.code in ['wcl'] and self.employee_id:
            self.employee_id.sudo().write({'wizard_name': self.address_id.name})
            self.state = 'print'
            return self.env.ref('jbm_letter_request.employee_work_certificate_report'). \
                report_action(self)

    @api.model
    def default_get(self, field_list):
        result = super(JbmLetterRequest, self).default_get(field_list)
        result['signatory_id'] = self.env['hr.employee'].sudo().search([('signatory', '=', True)], limit=1).id
        return result

    @api.model_create_multi
    def create(self, values_list):
        for val in values_list:
            val['name'] = self.env['ir.sequence'].next_by_code('jbm.letter.request') or _('New')
            val['name_sequence'] = self.env['ir.sequence'].next_by_code('jbm.letter.request.second') or _('New')
        letters = super(JbmLetterRequest, self).create(values_list)
        return letters

    def unlink(self):
        for letter in self:
            if letter.state == 'print':
                raise ValidationError(_('Can not delete printed letter.'))
        return super(JbmLetterRequest, self).unlink()


class LetterType(models.Model):
    _name = "letter.type"
    _description = "Selection many2one field in Letter request"

    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Char(string='Code')


