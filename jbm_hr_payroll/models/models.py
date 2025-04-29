# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class jbm_hr_payroll(models.Model):
#     _name = 'jbm_hr_payroll.jbm_hr_payroll'
#     _description = 'jbm_hr_payroll.jbm_hr_payroll'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
