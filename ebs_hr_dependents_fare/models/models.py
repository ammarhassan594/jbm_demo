# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class ebs_hr_dependents_fare(models.Model):
#     _name = 'ebs_hr_dependents_fare.ebs_hr_dependents_fare'
#     _description = 'ebs_hr_dependents_fare.ebs_hr_dependents_fare'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
