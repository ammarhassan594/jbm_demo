from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class AccountMove(models.Model):
    _inherit = 'account.move'

    service_payment_id = fields.Many2one('ebs.mod.end.of.service.payment.request', string='Service Payment')
    payslip_id = fields.Many2one('hr.payslip', string='Payslips')

    def button_cancel(self):
        for move in self:
            # payslips = self.env['invoice_payslip_rel'].search([])
            self._cr.execute("DELETE FROM invoice_payslip_rel WHERE payslip_id=%s", ([self.id]))
            # if move.line_ids.payslip_line_ids:
            #     move.line_ids.payslip_line_ids.unlink()
            for line in move.line_ids:
                if line.payslip_line_ids:
                    line.write({'payslip_line_ids':[(5,0,0)]})
        return super(AccountMove, self).button_cancel()

    def action_show_invoice_line(self):
        self.ensure_one()
        form_view = self.env.ref('account.view_move_form')
        tree_view = self.env.ref('account.view_invoice_tree')
        return {
            'name': _('Invoices'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'res_model': 'account.move',
            'views': [(form_view.id, 'form')],
            'view_id': form_view.id,
            'target': 'current',
            'res_id': self.id,
            'domain': [('id', '=', self.id)]

        }

class AccountMoveLines(models.Model):
    _inherit = 'account.move.line'

    payslip_line_ids = fields.One2many('hr.payslip.line', 'invoice_line_id', string='Payslips')




class AccountPayment(models.Model):
    _inherit = 'account.payment'

    is_employee_payment = fields.Boolean(
        string='Is Employee Payment',
        required=False, default=False)



