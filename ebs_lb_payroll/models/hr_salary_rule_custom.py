# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SalaryRules(models.Model):
    _inherit = 'hr.salary.rule'

    istaxable = fields.Boolean(
        string='Is Taxable',
        required=False)
    template = fields.Selection(
        string='Template',
        selection=[
            ('AE', 'Additional Element'),
            ('package', 'Package Amount'),
            ('basic', 'Basic Salary'),
            ('acc', 'Housing Allowance'),
            ('trns', 'Transport Allowance'),
            ('living_alw', 'Living Allowance'),
            ('other_alw', 'Other Allowance'),
            ('mobile', 'Mobile Allowance'),
            ('food', 'Food Allowance'),
            ('gross', 'Gross Amount'),
            ('ded', 'Deductions Total Amount'),
            ('net', 'Net Amount'),
            ('timeoff', 'Time off'),
            ('rap', 'Request for Allowance Payment'),
            ('aap', 'Salary Advance'),
            ('arap', ' Dues/ Remaining'),
            ('talw', 'Ticket Allowance Payment'),
            ('eos_gratuity', 'EOS Gratuity'),
            ('eos_paid_leave', 'EOS Paid Leaves'),
            ('eos_provision', 'EOS Provision'),
            ('eos_other_entitlement', 'EOS Other Entitlement'),
            ('fos_service_fee', 'FOS Service Fee'),
            ('fos_private_medical_insurance', 'FOS Private Medical Insurance'),
            ('fos_air_ticket_deposit', 'FOS Air Ticket Deposit'),
            ('fos_workmen_compensation', 'FOS workmen compensation'),
        ],
        required=False, )
    related_element_type = fields.Many2one(
        comodel_name='ebspayroll.additional.element.types',
        string='Additional Element Type',
        required=False)

    allowance_type_id = fields.Many2one(
        comodel_name='ebs.payroll.allowance.request.type',
        string='Allowance Type',
        required=False)
    leave_type_id = fields.Many2one(
        comodel_name='hr.leave.type',
        string='Leave Type',
    )
    product_id = fields.Many2one('product.product',string="Product")
    type = fields.Many2one('ebs.hr.eos.other.entitlements.types', string="Other Entitlement Type")

    # @api.depends('template')
    @api.onchange('template', 'type', 'category_id')
    def _template_onchange(self):
        payslip = True
        taxable = False
        condition = 'none'
        amount_type = 'code'
        code = ""
        self.related_element_type = None
        self.allowance_type_id = None
        if self.template == 'package':
            code = "result = contract.package"
            payslip = True

        if self.template == 'acc':
            code = "result=payslip.env['hr.payslip'].get_contract_details(payslip,contract,contract.accommodation)"
            payslip = True

        if self.template == 'basic':
            code = "result=payslip.env['hr.payslip'].get_contract_details(payslip,contract,contract.wage)"
            payslip = True

        if self.template == 'trns':
            code = "result=payslip.env['hr.payslip'].get_contract_details(payslip,contract,contract.transport_allowance)"
            payslip = True

        if self.template == 'living_alw':
            code = "result=payslip.env['hr.payslip'].get_contract_details(payslip,contract,contract.living_allowance)"
            payslip = True

        if self.template == 'other_alw':
            code = "result=payslip.env['hr.payslip'].get_contract_details(payslip,contract,contract.other_allowance)"
            payslip = True

        if self.template == 'food':
            code = "result=payslip.env['hr.payslip'].get_contract_details(payslip,contract,contract.food_allowance)"
            payslip = True

        if self.template == 'mobile':
            code = "result=payslip.env['hr.payslip'].get_contract_details(payslip,contract,contract.mobile_allowance)"
            payslip = True

        if self.template == 'net':
            code = "result =  categories.BASIC + categories.ALW + categories.DED+ categories.EXTAWL"
            payslip = True

        if self.template == 'ded':
            code = "result = categories.DED"
            payslip = True
            # taxable = True

        if self.template == 'gross':
            code = "result =  categories.ALW + categories.BASIC + categories.EXTAWL"
            payslip = True

        if self.template == 'arap':
            payslip = True

        if self.template == 'rap':
            payslip = True

        if self.template == 'aap':
            payslip = False

        if self.template == 'talw':
            code = "result=payslip.env['hr.payslip'].calculateTicketAllowance(payslip,employee)"
            payslip = True
        if self.template == 'AE':
            code = ""
            payslip = True

        if self.template == 'eos_gratuity':
            code = "result=payslip.env['ebs.mod.end.of.service.payment.request'].get_eos_gratuity(payslip)"
            payslip = True

        if self.template == 'eos_paid_leave':
            code = "result=payslip.env['ebs.mod.end.of.service.payment.request'].get_eos_paid_leaves(payslip)"
            payslip = True

        if self.template == 'eos_provision':
            code = "result=payslip.env['hr.payslip'].get_eos_provision(payslip)"
            payslip = True

        if self.template == 'eos_other_entitlement':
            code = "result=payslip.env['ebs.mod.end.of.service.payment.request'].get_eos_other_entitlements(payslip," + str(
                self.type.id) + ",'" + str(self.category_id.is_deduction) + "')"
            payslip = True

        if self.template == 'fos_service_fee':
            code = "result=payslip.env['hr.payslip'].calculate_fos_service_fee(payslip)"
            payslip = True

        if self.template == 'fos_private_medical_insurance':
            code = "result=payslip.env['hr.payslip'].calculate_private_medical_insurance(payslip)"
            payslip = True

        if self.template == 'fos_air_ticket_deposit':
            code = "result=payslip.env['hr.payslip'].calculate_fos_air_ticket_deposit(payslip)"
            payslip = True

        if self.template == 'fos_workmen_compensation':
            code = "result=payslip.env['hr.payslip'].calculate_fos_workmen_compensation(payslip)"
            payslip = True

        self.appears_on_payslip = payslip
        self.istaxable = taxable
        self.condition_select = condition
        self.amount_select = amount_type
        self.amount_python_compute = code
        return

    @api.onchange('related_element_type')
    def _related_element_type_onchange(self):
        if self.related_element_type and self.template:
            rec_code = '' + self.related_element_type.name
            python_code = "result=payslip.env['hr.payslip'].calculateAdditionalElements(payslip,employee,'" + rec_code + "')"
            self.amount_python_compute = python_code
        return

    @api.onchange('allowance_type_id')
    def _allowance_type_onchange(self):
        if self.allowance_type_id and self.template:
            rec_code = '' + self.allowance_type_id.name
            if self.template == 'arap':
                code = "result=payslip.env['hr.payslip'].calculateRemainingAmortizationPayment(payslip,employee,'" + rec_code + "')"
            if self.template == 'rap':
                code = "result=payslip.env['hr.payslip'].calculateAllowancePayment(payslip,employee,'" + rec_code + "')"
            if self.template == 'aap':
                code = "result=-(payslip.env['hr.payslip'].calculateAmortizationPayment(payslip,employee,'" + rec_code + "'))"
            self.amount_python_compute = code
        return

    @api.onchange('leave_type_id')
    def _leave_type_onchange(self):
        if self.leave_type_id and self.template:
            # rec_code = '' + self.leave_type_id.name
            code = "result=payslip.env['hr.payslip'].calculateTimeOff(payslip,employee," + str(
                self.leave_type_id.id) + ",'" + str(self.category_id.is_deduction) + "')"
            self.amount_python_compute = code
        return




class SalaryRulesCategory(models.Model):
    _inherit = 'hr.salary.rule.category'

    is_deduction = fields.Boolean('Is Deduction')
