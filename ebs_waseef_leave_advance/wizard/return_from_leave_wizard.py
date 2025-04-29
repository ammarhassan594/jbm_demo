from odoo import models, fields


class ReturnFromLeaveWizard(models.TransientModel):
    _name = 'return.leave.wizard'
    _description = "Return From Leave"

    return_date = fields.Date(string="Return Date", default="", required=False)
    pay_on = fields.Date(string="Pay On", default="", required=False)
    has_leave_advance = fields.Boolean(default=False)

    def create_early_return_from_leave(self):
        leave = self.env['hr.leave'].browse(self.env.context.get('active_id'))
        early_return = self.env['return.from.leave'].create({
            'employee_id': leave.employee_id.id,
            'leave_id': leave.id,
            'return_date': self.return_date,
            'date_to': leave.date_to,
            'pay_on': self.pay_on,
            'employee_id': leave.employee_id.id,
        })
        early_return.compute_return_payslip()
