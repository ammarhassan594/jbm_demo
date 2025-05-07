import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class InheritAccountMove(models.Model):
    _name = 'account.move'
    _inherit = ['account.move', 'dynamic.approval.mixin']
    _state_field = "state"
    _state_from = ['draft']
    # _state_to = ['posted']


    approval_for_reverse = fields.Boolean(string="Approval For Reverse", default=False, store=True)


    def notify_user(self, user):
        self.activity_schedule('jbm_account_extended.mail_activity_journal_entry', user_id=user.id)
        return True

    @api.model
    def create(self, vals):
        object = super(InheritAccountMove, self).create(vals)
        if object['move_type'] == 'entry':
            users = self.env['res.users'].search([])
            if users:
                for user in users:
                    if user.has_group('jbm_group_access_right_extended.custom_accounting_manager'):
                            object.notify_user(user)
        return object

    def approval_reverse_entry(self):
        self.approval_for_reverse = True

    # def _action_final_approve(self):
    #     res = super(InheritAccountMove, self)._action_final_approve()
    #     # if self._name == 'account.move':
    #     #     self.action_post()
    #     return res



