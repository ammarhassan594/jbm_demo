from odoo import api, fields, models


class HrDepartureWizardInherit(models.TransientModel):
    _inherit = 'hr.departure.wizard'

    termination_date = fields.Date(string="Termination Date")

    def action_register_departure(self):
        employee = self.employee_id
        if employee and employee.user_id:
            employee.user_id.sudo().write({'active': False})
        contracts = self.env['hr.contract'].sudo().search([('employee_id', '=', employee.id)])
        for contract in contracts:
            contract.sudo().write({'active': False})
        if employee.sudo().address_home_id:
            employee.sudo().address_home_id.sudo().write({'active': False})
        employee.sudo().write({
            'termination_date': self.termination_date,
            'reason':  False,
        })
        res = super(HrDepartureWizardInherit, self).action_register_departure()
        return res
