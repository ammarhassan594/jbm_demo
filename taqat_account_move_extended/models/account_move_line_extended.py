from odoo import models, fields, api, _

from odoo.exceptions import UserError


class AccountMoveLineInherit(models.Model):
    _inherit = 'account.move.line'

    move_line_description = fields.Char("Description")


class AnalyticAccountTagInherit(models.Model):
    _inherit = 'account.analytic.tag'

    @api.constrains('name')
    def analytic_tag_constrains(self):
        if self.env['account.analytic.tag'].search([('name', '=', self.name)]) - self:
            raise UserError(_('Account Analytic Tag field must be unique'))
