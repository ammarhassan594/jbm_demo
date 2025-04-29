from odoo import models, fields, api, _

class InheritHrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    def action_employee_send_sms(self):
        if self.slip_ids:
            for slip in self.slip_ids:
                if slip.employee_id:
                    slip.employee_id.with_context(slip=slip).send_sms_message()