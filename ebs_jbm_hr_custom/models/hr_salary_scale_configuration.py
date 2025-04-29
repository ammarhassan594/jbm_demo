# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrSalaryScaleConfiguration(models.Model):
    _name = 'hr.salary.scale.configuration'
    _description = 'HrSalaryScaleConfiguration'
    _rec_name = 'grade'

    grade = fields.Char(string="Grade")
    type_id = fields.Many2one('hr.recruitment.degree', string="Degree")
    number_of_years = fields.Integer(string="Number of years")
    element_ids = fields.One2many('hr.payroll.element', 'salary_scale_id', string="Elements")

    @api.model
    def default_get(self, fields):
        res = super(HrSalaryScaleConfiguration, self).default_get(fields)
        salary_allowance_ids = self.env['hr.salary.allowance'].sudo().search([])
        vals = []
        for salary_allowance_id in salary_allowance_ids:
            vals.append((0, 0, {'allowance_id': salary_allowance_id.id}))
        res.update({'element_ids': vals})
        return res


class HrPayrollElement(models.Model):
    _name = 'hr.payroll.element'
    _description = 'Hr Payroll Element'

    salary_scale_id = fields.Many2one('hr.salary.scale.configuration', string="Salary Scale")
    allowance_id = fields.Many2one('hr.salary.allowance', string="Allowance")
    allowance_type = fields.Selection(related='allowance_id.allowance_type', string="Allowance Type")
    from_amount = fields.Float(string="From")
    to_amount = fields.Float(string="To")


class HrSalaryAllowance(models.Model):
    _name = 'hr.salary.allowance'
    _description = 'Hr Salary Allowance'

    name = fields.Char(string='Name')
    allowance_type = fields.Selection([('housing_allowance', 'Housing Allowance'),
                                       ('transport_allowance', 'Transport Allowance'),
                                       ('living_allowance', 'Living Allowance'),
                                       ('other_allowance', 'Other Allowance'),
                                       ('food_allowance', 'Food Allowance'),
                                       ('mobile_allowance', 'Mobile Allowance'),
                                       ('maximum_ticket_allowance', 'Maximum Ticket Allowance')])
