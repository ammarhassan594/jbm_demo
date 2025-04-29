from odoo import fields, models, api


class EmploymentContractWizard(models.TransientModel):
    _name = 'employment.contract.wizard'
    _description = 'Salary Certificate Wizard'

    partner_id = fields.Many2one('res.partner', string="Contact", required=True)
    name = fields.Char(string="Free field inserted as parameter", required=True)

    def print_employment_contract(self):
        contracts = self.env['hr.contract']
        if self.env.context.get('active_model') == 'hr.contract' and self.env.context.get('active_ids'):
            contracts = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_ids'))
        for contract in contracts:
            contract.sudo().write({'wizard_name': self.name, 'employment_wizard_name': self.partner_id.name})
        report = self.env.ref('hr_contract_custom.report_employment_contract_action').report_action(contracts)
        return report
