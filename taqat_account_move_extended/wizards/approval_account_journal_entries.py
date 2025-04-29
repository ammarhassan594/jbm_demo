# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountJournalEntriesApproval(models.TransientModel):
    _name = 'account.journal.entries.approval'

    def get_account_name(self):
        move = self.env['account.move'].browse(self._context.get('move_id'))
        return move.account_account_name

    account_account_name = fields.Char("Account Name", default=lambda self: self.get_account_name())

    def confirm(self):
        move = self.env['account.move'].browse(self._context.get('move_id'))
        move.is_account_approval = False
        return move.action_post()
