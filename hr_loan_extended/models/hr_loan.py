
from odoo import models, fields, api, _


class Loans(models.Model):
    _name = 'hr.loan'
    _inherit = ['hr.loan', 'dynamic.approval.mixin']
    _state_field = "state"
    _state_from = ['waiting_approval_1', 'first_approve']
    _state_to = ['paid']
