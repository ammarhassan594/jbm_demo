# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AdditionalElementLines(models.Model):
    _name = 'ebspayroll.additional.element.lines'
    _description = 'Additional Element Lines'

    additional_element_id = fields.Many2one(
        comodel_name='ebspayroll.additional.elements',
        string='Addition Element',
        required=True)

    employee = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        required=True)

    amount = fields.Float(
        string='Amount',
        required=True)

    type = fields.Many2one(
        comodel_name='ebspayroll.additional.element.types',
        string='Element Type',
        related='additional_element_id.type')

    rule_type = fields.Selection(
        string='Type',
        related='additional_element_id.rule_type')

    payment_date = fields.Date(
        string='Payment Date',
        related='additional_element_id.payment_date')

    company_id = fields.Many2one('res.company', string="Main Company", related='additional_element_id.company_id')

    client_id = fields.Many2one('res.partner', string="Company/Client",
                                domain=[('is_customer', '=', True),
                                        ('is_company', '=', True), ('parent_id', '=', False)],
                                related='additional_element_id.client_id')
    import_allowance_id = fields.Many2one('ebspayroll.import.allowances', string="Import Allowance")

    payslip_id = fields.Many2one('hr.payslip', string="Payslip", ondelete='cascade')

    _sql_constraints = [
        ('add_element_line_emp_unique', 'unique(employee,additional_element_id)', _("Employee already exists"))
    ]

    @api.onchange('employee')
    def onchange_employee(self):
        domain = [('partner_parent_id', '=',
                   self.additional_element_id.client_id.id)] if self.additional_element_id.client_id else []
        return {'domain': {'employee': domain}}
