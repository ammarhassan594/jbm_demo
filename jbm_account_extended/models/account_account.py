from odoo import models, fields, api

class InheritAccountAccount(models.Model):
    _name = 'account.account'
    _inherit = ['account.account', 'dynamic.approval.mixin']
    _state_field = "state"
    _state_from = ['draft']
    _state_to = ['confirmed']

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], default='draft')

    deprecated = fields.Boolean(index=True, default=True, tracking=True, readonly=True)

    def action_confirm(self):
        self.ensure_one()
        self.state = 'confirmed'
        self.deprecated = False


    def action_cancel(self):
        self.ensure_one()
        self.state = 'cancelled'

    def _action_final_approve(self):
        res = super(InheritAccountAccount, self)._action_final_approve()
        if self._name == 'account.account':
            self.action_confirm()
        return res