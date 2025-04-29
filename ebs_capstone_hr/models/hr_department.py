# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class HrDepartmentCustom(models.Model):
    _inherit = 'hr.department'

    is_human_resource = fields.Boolean(string="Is Human Resource")
    is_budget_preparation = fields.Boolean(string="Is Budget Preparation")
