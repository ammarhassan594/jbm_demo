# -*- coding: utf-8 -*-

from odoo import models, fields, api
#from odoo.exceptions import ValidationError


class AdditionalElementTypes(models.Model):
    _name = 'ebspayroll.additional.element.types'
    _description = 'Additional Element types'

    code = fields.Char(
        string='Code',
        required=False)
    name = fields.Char(
        string='Name',
        required=True)

    description = fields.Text(
        string="Description",
        required=False)

    type = fields.Selection(
        string='Type',
        selection=[('A', 'Addition'),
                   ('D', 'Deduction'), ],
        required=True, )
    _sql_constraints = [
        ('code_unique', 'unique (code)', 'Code must be unique')
    ]

    recurring = fields.Boolean()


    # @api.model_create_multi
    # def create(self, vals_list):
    #     for vals in vals_list:
    #         code = vals.get('code')
    #         name = vals.get('name')
    #         type = vals.get('type')
    #         rules = self.env['hr.salary.rule'].search([('code', '=', code)])
    #         categ = ''
    #         if type == 'A':
    #             categ = 'ALW'
    #         elif type == 'D':
    #             categ = 'DED'
    #         if rules:
    #             continue
    #         category_id = self.env['hr.salary.rule.category'].search([('code', '=', categ)])
    #         res = {
    #             'name': name,
    #             'code': code,
    #             'struct_id': self.env.ref('jbm_hr_payroll.structure_worker_jbm').id,
    #             'condition_select': 'none',
    #             'category_id': category_id.id,
    #             'amount_select': 'code',
    #             'amount_python_compute': "result=payslip.env['hr.payslip'].calculateAdditionalElements(payslip,employee,'" + code + "')"
    #         }
    #         self.env['hr.salary.rule'].create(res)
    #     return super().create(vals_list)
    #

