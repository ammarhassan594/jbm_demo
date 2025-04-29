from odoo import api, fields, models, _

class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    def _get_available_contracts_domain(self):
        hr_payslip_run_id = self.env['hr.payslip.run'].browse([self._context.get('active_id')])
        client_id = hr_payslip_run_id.client_id
        if client_id:
            return [('contract_ids.state', 'in', ('open', 'close')),('partner_parent_id','=',client_id.id),('company_id','=',self._context.get('payslip_batch_company'))]
        else:
            return [('contract_ids.state', 'in', ('open', 'close')),('company_id','=',self._context.get('payslip_batch_company'))]
