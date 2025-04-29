from odoo import fields, models, api


class SalaryCertificate(models.TransientModel):
    _name = 'emp.salary.certificate.wizard'
    _description = 'Salary Certificate Wizard'

    partner_id = fields.Many2one('res.partner', string="Contact", required=True)

    def print_salary_certificate(self):
        contracts = self.env['hr.contract']
        if self.env.context.get('active_model') == 'hr.contract' and self.env.context.get('active_ids'):
            contracts = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_ids'))
        for contract in contracts:
            contract.sudo().write({'wizard_name': self.partner_id.name})
        report = self.env.ref('hr_contract_custom.contract_salary_certificate_action').report_action(contracts)
        return report
