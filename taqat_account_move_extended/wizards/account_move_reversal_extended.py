# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMoveReversalExtended(models.TransientModel):
    _inherit = 'account.move.reversal'

    def reverse_moves(self):
        res =super(AccountMoveReversalExtended, self).reverse_moves()
        move = self.env['account.move'].browse(self._context.get('active_id'))
        move.is_reversed_entry_done = True
        return res
