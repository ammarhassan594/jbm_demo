# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ContractInherit(models.Model):
    _inherit = 'hr.contract'

    @api.onchange('department_id')
    def department_onchange(self):
        self.analytic_account_id = self.department_id.analytic_account_id.id
