from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import AccessError, UserError, ValidationError


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee", readonly=True)
    employee_number = fields.Char(related="employee_id.registration_number")

    def action_get_employees_bank(self):
        emp_banks = self.env['hr.employee'].search([]).mapped('bank_account_id')
        return {
            'name': _('Employees Bank Account'),
            'domain': [('id', 'in', emp_banks.ids)],
            'view_type': 'form',
            'res_model': 'res.partner.bank',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    # @api.model
    # def create(self, vals):
    #     obj = super(ResPartnerBank, self).create(vals)
    #     employee = self.env['hr.employee'].search(
    #         [('id', '=', obj.employee_id.id)], limit=1)
    #     # employee_bank = self.env['hr.employee'].search(
    #     #             [('id', '=', obj.employee_id.id)], limit=1).mapped('bank_account_id')
    #     if len(employee):
    #         employee.write({'bank_account_id': obj.id})
    #     # if len(employee.bank_account_id):
    #     #     employee.write({'bank_account_id': obj.id})
    #     # else:
    #     #     employee.write({'bank_account_id': obj.id})
    #     return obj
    #
    # def write(self, vals):
    #     emp_id = vals.get('employee_id')
    #     if emp_id:
    #         employee = self.env['hr.employee'].search(
    #             [('id', '=', emp_id)], limit=1)
    #         employee.write({'bank_account_id': self.id})
    #     return super(ResPartnerBank, self).write(vals)

    _sql_constraints = [
        ('unique_number', '', 'Account Number must be unique SQL'),
    ]

    @api.constrains('acc_number', 'employee_id')
    def _check_unique_acc_number(self):
        for number in self:
            all_numbers = self.search([
                ('acc_number', '=', number.acc_number), ('id', '!=', number.id)
            ])
            employees = self.env['hr.employee'].search([
                ('bank_account_id', 'in', all_numbers.ids), ('active', '=', True)
            ])
            if employees:
                raise ValidationError(_('Account Number must be unique'))
