from odoo import models, fields, api, _


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    is_account_approval = fields.Boolean("Get Account", default=True, copy=False)
    account_account_name = fields.Char("Account Name", default=True, copy=False)
    is_reversed_entry_done = fields.Boolean("Is Reversed Entries",copy=False)




    def action_post(self):
        if self.is_account_approval == True and self.move_type == 'in_invoice':
            self.account_account_name = ', '.join(self.line_ids.mapped('account_id.name'))
            return self.approval_entries_account()
        else:
            return super(AccountMoveInherit, self).action_post()

    def approval_entries_account(self):
        return {
            'name': 'Account Approval',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('taqat_account_move_extended.account_journal_entries_approval_views').id,
            'res_model': 'account.journal.entries.approval',
            'domain': [],
            'context': {
                'move_id': self.id,
            },
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
