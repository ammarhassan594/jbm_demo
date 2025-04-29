from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class InheritHrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    def unlink(self):
        attendance_batch = self.env['hr.attendance.batch'].search([
            ('payslip_batch_id', '=', self.id)
        ])
        if attendance_batch:
            raise ValidationError(_("this payslip batch have attendance batch , please delete attendance batch!"))
        else:
            return super(InheritHrPayslipRun, self).unlink()

    def action_draft(self):
        if self.slip_ids:
            for slip in self.slip_ids:
                slip.action_payslip_draft()
            self.slip_ids.unlink()
        attendance_batch = self.env['hr.attendance.batch'].search([('payslip_batch_id','=',self.id)])
        if attendance_batch:
            attendance_batch.unlink()
        return super(InheritHrPayslipRun, self).action_draft()

